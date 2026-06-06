#!/usr/bin/env python3
"""
统一取数脚本 — jw-investment-data 核心引擎 v3.0
═══════════════════════════════════════════════════

v3.0 新特性:
  🔌 熔断器       — 3次失败→熔断→10min探测→自动恢复
  ⏰ 交易时钟     — 盘中5min缓存 vs 盘后24h
  📦 标准信封     — {ok, source, data, error, ts} + meta{breaker,market}

用法:
  python fetch_market_data.py --category quote  --symbol 600519 --market A
  python fetch_market_data.py --category quote  --symbol 600519 --format markdown  # 人读
  python fetch_market_data.py --schema                                          # 自描述
  python fetch_market_data.py --category kline  --symbol 600519 --market A --start 20260101
  python fetch_market_data.py --category forex  --symbol XAUUSD
  python fetch_market_data.py --category macro  --symbol GDP
  python fetch_market_data.py --category futures --symbol RB0 --market SHFE
  python fetch_market_data.py --category fund    --symbol 000001

代理（让被封锁的引擎复活）:
  export HTTP_PROXY=http://127.0.0.1:7890
  python fetch_market_data.py ...
  # 或
  python fetch_market_data.py --proxy http://127.0.0.1:7890 ...

引擎状态（2026-05-27 实测）:
  ✅ Baostock      — A股 K线/财务  EOD
  ✅ 腾讯 HTTP     — A/H股 实时行情  curl直连
  ✅ 新浪 HTTPS    — A/H股 实时行情 + 五档盘口（hq.sinajs.cn）
  ✅ AkShare 1.18  — A股 实时行情（腾讯源，首页+翻页兜底）
  ✅ 百度股市通     — A股 独立源（adata→百度，五档盘口，~0.15s）
  ✅ Tushare       — A股 独立源（T+1 K线/估值，独立数据库）
  ✅ 雪球           — A股 独立源（cookie→API，~1.2s，独立平台）
  ⚠️ yfinance      — 港/美股（需代理，带指数退避重试）
  ❌ efinance      — 东方财富封IP

四源交叉校验:
  默认双引擎（Tencent+Baostock）→ 2源校验 → 标注差异
  有新浪时（+sina）→ 3源校验 → 增强置信度
  有AkShare时（+akshare）→ 4源校验 → 全量验证
  有代理时（+yfinance）→ 5源校验 → 全量验证

置信度体系（v2.3）:
  🟢 high       — ≥3源差异 ≤2%
  🟡 medium     — 2源差异 ≤5%，或 3源差异 2-5%
  🔵 acceptable — 仅1源
  🔴 low        — 无数据

YAML配置（v2.4）:
  config/engines.yaml — 引擎优先级、超时、校验阈值、输出格式

输出格式:
  --format json (默认) — 标准信封 {ok, data, meta}（含 latency_ms）
  --format markdown     — 人类可读 Markdown（TTY 自动切换）

退出码:
  0=ok  1=runtime_error  4=no_data

输出: JSON/Markdown (结构化 + 校验结论 + 置信度 + 引擎状态)
"""

import argparse, json, os, re, subprocess, sys, time, traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── 内部模块（同目录）─────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from circuit_breaker import BreakerRegistry
from market_clock import get_market_status, MarketCache
from output_contract import envelope_ok, envelope_error, combined_envelope
from format_market import format_market as _format_markdown

__version__ = "3.5.0"

# ═══════════════════════════════ 代理 ═══════════════════════════════
PROXY_URL: Optional[str] = None

def _setup_proxy(proxy_arg=None):
    global PROXY_URL
    PROXY_URL = proxy_arg or os.environ.get("HTTP_PROXY") or os.environ.get("ALL_PROXY")
    if PROXY_URL:
        os.environ.setdefault("HTTP_PROXY", PROXY_URL)
        os.environ.setdefault("HTTPS_PROXY", PROXY_URL)

# ═══════════════════════════════ 引擎状态 ═══════════════════════════
ENGINE_STATUS = {}
for _name, _mod in [("baostock","baostock"),("yfinance","yfinance"),
                     ("akshare","akshare"),("efinance","efinance")]:
    try: __import__(_mod); ENGINE_STATUS[_name]="available"
    except: ENGINE_STATUS[_name]="not_installed"

# ═══════════════════════════════ 通用工具 ═══════════════════════════
def _parse_tencent_fields(fields: List[str]) -> Dict:
    """解析腾讯 qt.gtimg.cn ~分割的字段"""
    if len(fields) < 35: return {}
    return {
        "name": fields[1] if fields[1] else "",
        "price": float(fields[3]) if fields[3] else None,
        "prev_close": float(fields[4]) if fields[4] else None,
        "open": float(fields[5]) if fields[5] else None,
        "volume": float(fields[6]) if fields[6] else None,
        "high": float(fields[33]) if len(fields) > 33 and fields[33] else None,
        "low": float(fields[34]) if len(fields) > 34 and fields[34] else None,
        "change": float(fields[31]) if len(fields) > 31 and fields[31] else None,
        "change_pct": float(fields[32]) if len(fields) > 32 and fields[32] else None,
        "pe_ttm": float(fields[39]) if len(fields) > 39 and fields[39] else None,
        "market_cap": float(fields[45]) if len(fields) > 45 and fields[45] else None,
    }


# ═══════════════════════════════ 引擎 1: 腾讯 HTTP ══════════════════
def _tencent_raw(symbol: str, market: str = "A") -> Optional[Dict]:
    prefix = {"A": "sh" if symbol.startswith(("6","9")) else "sz", "HK": "hk"}.get(market, "sh")
    url = f"http://qt.gtimg.cn/q={prefix}{symbol}"
    try:
        r = subprocess.run(["timeout","8","curl","-sS","-m","5",url], capture_output=True, timeout=10)
        if r.returncode != 0 or not r.stdout: return None
        raw = r.stdout.decode("gbk", errors="replace").strip()
        if '"' not in raw: return None
        fields = raw.split('"')[1].split("~")
        return _parse_tencent_fields(fields)
    except: return None


# ═══════════════════════════════ 引擎 1B: 新浪 HTTPS ══════════════
def _sina_quote(symbol: str, market: str = "A") -> Optional[Dict]:
    """新浪财经 hq.sinajs.cn — 免费实时行情 + 五档盘口

    格式: var hq_str_sh601318="名称,昨收,开盘,最新,最高,最低,...,日期,时间,..."
    比腾讯多五档盘口（买1-5/卖1-5），是理想交叉校验源。
    HTTP 已超时，必须用 HTTPS + Referer。
    """
    prefix = {"A": "sh" if symbol.startswith(("6","9")) else "sz", "HK": "hk"}.get(market)
    if not prefix: return None
    url = f"https://hq.sinajs.cn/list={prefix}{symbol}"
    try:
        r = subprocess.run(
            ["timeout","8","curl","-sS","-m","5",url,
             "-H","Referer: https://finance.sina.com.cn"],
            capture_output=True, timeout=10)
        if r.returncode != 0 or not r.stdout: return None
        raw = r.stdout.decode("gbk", errors="replace").strip()
        # 提取引号内逗号分隔字段
        if '"' not in raw: return None
        fields = raw.split('"')[1].split(",")
        if len(fields) < 32: return None
        return {
            "name": fields[0] if fields[0] else "",
            "price": float(fields[3]) if fields[3] else None,
            "prev_close": float(fields[2]) if fields[2] else None,
            "open": float(fields[1]) if fields[1] else None,
            "high": float(fields[4]) if fields[4] else None,
            "low": float(fields[5]) if fields[5] else None,
            "volume": float(fields[8]) if fields[8] else None,
            "amount": float(fields[9]) if fields[9] else None,
            "date": fields[30] if len(fields) > 30 else "",
            "bid1": float(fields[11]) if fields[11] else None,
            "ask1": float(fields[21]) if fields[21] else None,
        }
    except: return None
def _baostock_kline(symbol: str, start: str, end: str = None) -> Optional[Dict]:
    import baostock as bs
    prefix = "sh." if symbol.startswith(("6","9")) else "sz."
    end = end or datetime.now().strftime("%Y-%m-%d")
    # 抑制 login/logout print
    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull
        bs.login()
        sys.stdout = old_stdout
        rs = bs.query_history_k_data_plus(prefix+symbol, "date,close,volume",
            start_date=start, end_date=end, frequency="d", adjustflag="2")
        rows = []
        while (rs.error_code == '0') & rs.next(): rows.append(rs.get_row_data())
        sys.stdout = devnull
        bs.logout()
        sys.stdout = old_stdout
        if not rows: return None
        return {"last_date": rows[-1][0], "last_close": float(rows[-1][1]),
                "count": len(rows), "source": "baostock"}
    finally:
        sys.stdout = old_stdout
        devnull.close()


def _baostock_financial(symbol: str) -> Optional[Dict]:
    """baostock 多维财务数据：5年×4季 profit+balance+cashflow+dupont+growth"""
    import baostock as bs
    from datetime import datetime
    prefix = "sh." if symbol.startswith(("6","9")) else "sz."
    code = prefix + symbol
    current_year = datetime.now().year

    def _query(fn, fields):
        """查询多季度数据，返回 [{statDate, field1, field2, ...}]"""
        rows = []
        for y in range(current_year - 4, current_year + 1):
            for q in range(1, 5):
                try:
                    rs = fn(code, year=y, quarter=q)
                    if rs.error_code == '0':
                        vals = rs.get_row_data()
                        if vals and len(vals) >= len(fields):
                            row = {f: (float(v) if v and f not in ("pubDate","statDate","code") else v)
                                   for f, v in zip(fields, vals) if v}
                            if row.get("statDate"):
                                rows.append(row)
                except Exception:
                    pass
        return rows

    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull
        bs.login()
        sys.stdout = old_stdout

        # 1) 利润表
        profit_fields = ["code","pubDate","statDate","roeAvg","npMargin","gpMargin",
                         "netProfit","epsTTM","MBRevenue","totalShare","liqaShare"]
        profit_rows = _query(bs.query_profit_data, profit_fields)

        # 2) 资产负债表
        balance_fields = ["code","pubDate","statDate","currentRatio","quickRatio",
                          "cashRatio","YOYLiability","liabilityToAsset","assetToEquity"]
        balance_rows = _query(bs.query_balance_data, balance_fields)

        # 3) 现金流量表
        cashflow_fields = ["code","pubDate","statDate","CAToAsset","NCAToAsset",
                           "tangibleAssetToAsset","ebitToInterest","CFOToOR",
                           "CFOToNP","CFOToGr"]
        cashflow_rows = _query(bs.query_cash_flow_data, cashflow_fields)

        # 4) 成长能力
        growth_fields = ["code","pubDate","statDate","YOYEquity","YOYAsset",
                         "YOYNI","YOYEPSBasic","YOYPNI"]
        growth_rows = _query(bs.query_growth_data, growth_fields)

        # 5) 杜邦分析
        dupont_fields = ["code","pubDate","statDate","dupontROE","dupontAssetSto498",
                         "dupontAssetTurn","dupontPnitoni","dupontNitogr",
                         "dupontTaxnint","dupontIntoni","dupontEbitoni"]
        dupont_rows = _query(bs.query_dupont_data, dupont_fields)

        # 6) 分红数据
        dividend_rows = []
        for y in range(current_year - 4, current_year + 1):
            try:
                rs = bs.query_dividend_data(code, year=y, yearType="report")
                if rs.error_code == '0':
                    while rs.next():
                        vals = rs.get_row_data()
                        if vals:
                            dividend_rows.append(vals)
            except Exception:
                pass

        sys.stdout = devnull
        bs.logout()
        sys.stdout = old_stdout

        if not profit_rows:
            return None

        # 提取最新一期关键指标用于顶层摘要
        latest = profit_rows[-1] if profit_rows else {}
        latest_balance = balance_rows[-1] if balance_rows else {}
        latest_cashflow = cashflow_rows[-1] if cashflow_rows else {}

        return {
            "summary": {
                "latest_period": latest.get("statDate"),
                "revenue": latest.get("MBRevenue"),
                "net_profit": latest.get("netProfit"),
                "roe": latest.get("roeAvg"),
                "gross_margin": latest.get("gpMargin"),
                "net_margin": latest.get("npMargin"),
                "eps_ttm": latest.get("epsTTM"),
                "current_ratio": latest_balance.get("currentRatio"),
                "liability_to_asset": latest_balance.get("liabilityToAsset"),
                "cfo_to_np": latest_cashflow.get("CFOToNP"),
                "cfo_to_or": latest_cashflow.get("CFOToOR"),
            },
            "profit": profit_rows,
            "balance": balance_rows,
            "cashflow": cashflow_rows,
            "growth": growth_rows,
            "dupont": dupont_rows,
            "dividend_raw": dividend_rows,
            "source": "baostock",
            "row_counts": {
                "profit": len(profit_rows),
                "balance": len(balance_rows),
                "cashflow": len(cashflow_rows),
                "growth": len(growth_rows),
                "dupont": len(dupont_rows),
                "dividend": len(dividend_rows),
            }
        }
    except Exception as e:
        try:
            sys.stdout = devnull
            bs.logout()
        except Exception:
            pass
        sys.stdout = old_stdout
        return None
    finally:
        try: sys.stdout = old_stdout
        except: pass
        try: devnull.close()
        except: pass


# ═══════════════════════════════ 引擎 3: AkShare 1.18 ═══════════════
def _akshare_a_quote(symbol: str) -> Optional[Dict]:
    """AkShare 1.18.63: A股实时行情（腾讯源）, 首页取数 + 不命中的翻页兜底

    策略:
      1. 首页200只（按价格降序），命中率 ~60%（沪市大盘股+活跃深市股）
      2. 未命中 → 翻页搜索（最多翻20页 = 4000只），命中率 100%
         - 单页 ~0.8s，最坏 16s，典型 < 5s
      3. 超时/异常 → 返回 None，不影响其他引擎
    """
    from akshare.stock.stock_zh_a_tx import stock_zh_a_spot_tx
    import requests as _requests
    try:
        # 第一步: 首页快速查找（绝大多数情况命中）
        df = stock_zh_a_spot_tx()
        prefix = "sh" if symbol.startswith(("6","9")) else "sz"
        full_code = f"{prefix}{symbol}"
        row = df[df["code"] == full_code]
        if not row.empty:
            r = row.iloc[0].to_dict()
            return {
                "price": float(r.get("zxj",0)) if r.get("zxj") else None,
                "change_pct": float(r.get("zdf",0)) if r.get("zdf") else None,
                "volume": float(r.get("volume",0)) if r.get("volume") else None,
                "market_cap": float(r.get("zsz",0)) if r.get("zsz") else None,
                "pe_ttm": float(r.get("pe_ttm",0)) if r.get("pe_ttm") else None,
                "name": r.get("name",""), "source": "akshare_1.18"
            }

        # 第二步: 翻页兜底（首页未命中时，翻页搜索）
        # 000792这一类低价深市股在首页命中不了
        url = "https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList"
        for page in range(1, 21):  # 最多翻20页 = 4000只
            params = {"_appver":"11.17.0","board_code":"aStock",
                      "sort_type":"price","direct":"down",
                      "offset":str(page*200),"count":"200"}
            r = _requests.get(url, params=params, timeout=8)
            j = r.json()
            if j.get("code") != 0: break
            records = j["data"]["rank_list"]
            if not records: break
            for rec in records:
                if rec["code"] == full_code:
                    return {
                        "price": float(rec.get("zxj",0)) if rec.get("zxj") else None,
                        "change_pct": float(rec.get("zdf",0)) if rec.get("zdf") else None,
                        "volume": float(rec.get("volume",0)) if rec.get("volume") else None,
                        "market_cap": float(rec.get("zsz",0)) if rec.get("zsz") else None,
                        "pe_ttm": float(rec.get("pe_ttm",0)) if rec.get("pe_ttm") else None,
                        "name": rec.get("name",""), "source": "akshare_1.18"
                    }
        return None
    except Exception:
        return None


def _akshare_futures() -> Optional[List]:
    """AkShare 1.18.63: 期货合约列表"""
    from akshare.futures.futures_comm_js import futures_comm_js
    try:
        df = futures_comm_js()
        records = df.astype(str).to_dict(orient="records")
        return records if len(records) > 0 else None
    except: return None


# ═══════════════════════════════ 引擎 5: 新浪期货 ═══════════════════
_SINA_FUTURES_MAP = {
    "RB0":"RB0","AU0":"AU0","AG0":"AG0","CU0":"CU0","AL0":"AL0",
    "ZN0":"ZN0","NI0":"NI0","SN0":"SN0","PB0":"PB0",
    "SC0":"SC0","FU0":"FU0","BU0":"BU0","RU0":"RU0",
    "MA0":"MA0","TA0":"TA0","PP0":"PP0","L0":"L0","V0":"V0",
    "M0":"M0","RM0":"RM0","Y0":"Y0","P0":"P0","OI0":"OI0",
    "CF0":"CF0","SR0":"SR0","C0":"C0","CS0":"CS0",
    "JM0":"JM0","J0":"J0","I0":"I0","ZC0":"ZC0",
    "IF0":"IF0","IC0":"IC0","IH0":"IH0","IM0":"IM0",
}

def _sina_futures(symbol: str) -> Optional[Dict]:
    """新浪 hq.sinajs.cn — 期货实时行情
    字段: 0=名, 2=开盘, 3=昨收, 5=最高, 6=最低, 8=最新价, 12=成交量
    """
    code = _SINA_FUTURES_MAP.get(symbol, symbol)
    url = f"https://hq.sinajs.cn/list={code}"
    try:
        r = subprocess.run(
            ["timeout","8","curl","-sS","-m","5",url,
             "-H","Referer: https://finance.sina.com.cn"],
            capture_output=True, timeout=10)
        if r.returncode != 0 or not r.stdout: return None
        raw = r.stdout.decode("gbk", errors="replace").strip()
        if '"' not in raw: return None
        fields = raw.split('"')[1].split(",")
        if len(fields) < 10: return None
        return {
            "name": fields[0],
            "price": float(fields[8]) if fields[8] else None,
            "open": float(fields[2]) if fields[2] else None,
            "high": float(fields[5]) if fields[5] else None,
            "low": float(fields[6]) if fields[6] else None,
            "prev_close": float(fields[3]) if fields[3] else None,
            "volume": float(fields[12]) if len(fields)>12 and fields[12] else None,
            "source": "sina_futures"
        }
    except: return None


def _akshare_fund_etf() -> Optional[List]:
    """AkShare 1.18.63: ETF规模（上交所）"""
    from akshare.fund.fund_etf_sse import fund_etf_scale_sse
    try:
        df = fund_etf_scale_sse()
        return df.to_dict(orient="records") if len(df) > 0 else None
    except: return None


# ═══════════════════════════════ 引擎 6: 百度股市通 ═══════════════════
def _baidu_quote(symbol: str) -> Optional[Dict]:
    """adata/百度股市通 — 真正独立的 A 股实时源（非腾讯/新浪数据流）

    使用 get_market_five (五档盘口，~0.15s)，b1 作为近似实时价。
    adata 底层走百度股市通，与腾讯/新浪数据流完全独立。
    """
    try:
        import adata
        df = adata.stock.market.get_market_five(stock_code=symbol)
        if df is None or len(df) == 0: return None
        r = df.iloc[0].to_dict()
        price = float(r.get("b1", 0)) if r.get("b1") else None
        if not price: return None
        return {
            "name": r.get("short_name", ""),
            "price": price,
            "bid1": price,
            "ask1": float(r.get("s1", 0)) if r.get("s1") else None,
            "source": "baidu"
        }
    except ImportError:
        return None
    except Exception:
        return None


# ═══════════════════════════════ 引擎 7: Tushare ═══════════════════
def _get_tushare_token() -> Optional[str]:
    """从 YAML 配置读取 Tushare token"""
    creds = CONFIG.get("credentials", {})
    return creds.get("tushare_token") or os.environ.get("TUSHARE_TOKEN")


def _tushare_quote(symbol: str) -> Optional[Dict]:
    """Tushare — 独立 A 股行情源（T+1，与交易所/Baidu/Baostock 均无关）

    使用 pro.daily() 获取最近交易日收盘价，完全是第四方独立数据。
    """
    token = _get_tushare_token()
    if not token: return None
    try:
        import tushare as ts
        ts.set_token(token)
        pro = ts.pro_api()
        ts_code = f"{symbol}.{'SH' if symbol.startswith(('6','9')) else 'SZ'}"
        # 取最近3天数据（覆盖周末/节假日）
        from datetime import timedelta
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
        if df is None or len(df) == 0: return None
        row = df.iloc[0].to_dict()
        return {
            "price": float(row.get("close", 0)),
            "prev_close": float(row.get("pre_close", 0)),
            "open": float(row.get("open", 0)),
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
            "volume": float(row.get("vol", 0)) if row.get("vol") else None,
            "date": str(row.get("trade_date", "")),
            "source": "tushare"
        }
    except ImportError:
        return None
    except Exception:
        return None


# ═══════════════════════════════ 引擎 8: 雪球 ═══════════════════════
_XQ_COOKIE_FILE = "/tmp/xueqiu_cookies.txt"
_XQ_COOKIE_TS = 0  # cookie 时间戳，过期重取

def _xueqiu_quote(symbol: str) -> Optional[Dict]:
    """雪球 — 独立 A 股行情源（需两步：cookie→API，~1.2s）

    雪球数据与交易所/百度/Tushare/Baostock 均无关，是第五独立源。
    首次请求需获取 cookie（~0.8s），后续复用（~0.4s）。
    """
    global _XQ_COOKIE_TS
    import time as _time

    prefix = "SH" if symbol.startswith(("6","9")) else "SZ"
    xq_sym = f"{prefix}{symbol}"

    # Cookie 过期重取（30分钟）
    now = _time.time()
    if now - _XQ_COOKIE_TS > 1800:
        subprocess.run(
            ["timeout","8","curl","-sS","-c",_XQ_COOKIE_FILE,"-m","8",
             "https://xueqiu.com/",
             "-H","User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"],
            capture_output=True, timeout=10)
        _XQ_COOKIE_TS = now

    try:
        r = subprocess.run(
            ["timeout","8","curl","-sS","-b",_XQ_COOKIE_FILE,"-m","5",
             f"https://stock.xueqiu.com/v5/stock/quote.json?symbol={xq_sym}&extend=detail",
             "-H","User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"],
            capture_output=True, timeout=10)
        if r.returncode != 0 or not r.stdout: return None
        import json as _json
        d = _json.loads(r.stdout)
        if d.get("error_code") != 0: return None
        q = d["data"]["quote"]
        return {
            "name": q.get("name", ""),
            "price": float(q["current"]) if q.get("current") else None,
            "change_pct": float(q["percent"]) if q.get("percent") else None,
            "high": float(q["high"]) if q.get("high") else None,
            "low": float(q["low"]) if q.get("low") else None,
            "volume": float(q.get("volume")) if q.get("volume") else None,
            "pe_ttm": float(q["pe_ttm"]) if q.get("pe_ttm") else None,
            "source": "xueqiu"
        }
    except Exception:
        return None


def _yf_ticker(symbol: str):
    """yfinance Ticker — session 级代理（v1.4.0兼容）"""
    import yfinance as yf, requests
    session = requests.Session()
    if PROXY_URL: session.proxies = {"http": PROXY_URL, "https": PROXY_URL}
    return yf.Ticker(symbol, session=session)


def _yf_fetch_price(ticker, retries=2) -> Optional[float]:
    """带重试的价格提取 — Rate limited 时自动退避"""
    import time
    for attempt in range(retries + 1):
        try:
            info = ticker.info or {}
            p = info.get("regularMarketPrice") or info.get("currentPrice")
            if p: return float(p)
        except Exception as e:
            err = str(e)
            if "Rate limited" in err or "Too Many" in err or "429" in err:
                if attempt < retries:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    time.sleep(wait)
                    continue
            # 非限流错误直接抛出，不重试
            raise
        # 无数据也重试一次（可能是 transient）
        if attempt < retries:
            time.sleep(1)
    return None


# ═══════════════════════════════ 取数编排 ═══════════════════════════
def fetch_a_quote(symbol: str, force_cache: bool = False) -> Dict:
    """A股行情 — 多引擎，含熔断保护 + 交易时段感知缓存

    Args:
        symbol: 6位股票代码
        force_cache: 跳过缓存，强制实时获取
    """
    results, errors = {}, []
    market = _market_now()

    # ── 缓存检查（盘中5min / 盘后24h）─────────────────────
    cache_key = f"A:{symbol}"
    if not force_cache:
        cached = CACHE.get(cache_key, market["cache_ttl_minutes"])
        if cached and cached.get("price"):
            cached["from_cache"] = True
            cached["cache_age"] = market["cache_ttl_minutes"]
            return {"results": {"cache": cached}, "errors": [],
                    "_breaker": CB.status_snapshot(),
                    "_market": market["state"]}

    # ── 引擎1: Tencent HTTP ────────────────────────────────
    eng = "tencent_http"
    if CB.can_call(eng):
        try:
            t = _tencent_raw(symbol, "A")
            if t and t.get("price"):
                results[eng] = {"price": t["price"], "change_pct": t.get("change_pct")}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)
    else:
        errors.append(f"{eng}: breaker={CB.get_state(eng).state}")

    # ── 引擎1B: Sina HTTPS ─────────────────────────────────
    eng = "sina_https"
    if CB.can_call(eng):
        try:
            s = _sina_quote(symbol, "A")
            if s and s.get("price"):
                results[eng] = {"price": s["price"], "volume": s.get("volume")}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)
    else:
        errors.append(f"{eng}: breaker={CB.get_state(eng).state}")

    # ── 引擎2: Baostock ───────────────────────────────────
    eng = "baostock"
    if CB.can_call(eng):
        try:
            b = _baostock_kline(symbol, "2026-05-20")
            if b:
                results[eng] = {"price": b["last_close"], "date": b["last_date"]}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)

    # ── 引擎3: AkShare 1.18 ────────────────────────────────
    eng = "akshare"
    if CB.can_call(eng):
        try:
            a = _akshare_a_quote(symbol)
            if a:
                results[eng] = {"price": a["price"], "change_pct": a.get("change_pct")}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)

    # ── 引擎3B: Baidu ─────────────────────────────────────
    eng = "baidu"
    if CB.can_call(eng):
        try:
            ba = _baidu_quote(symbol)
            if ba and ba.get("price"):
                results[eng] = {"price": ba["price"], "name": ba.get("name")}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)

    # ── 引擎3C: Tushare ───────────────────────────────────
    eng = "tushare"
    if CB.can_call(eng):
        try:
            ts_q = _tushare_quote(symbol)
            if ts_q and ts_q.get("price"):
                results[eng] = {"price": ts_q["price"], "date": ts_q.get("date")}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)

    # ── 引擎3D: 雪球 ──────────────────────────────────────
    eng = "xueqiu"
    if CB.can_call(eng):
        try:
            xq = _xueqiu_quote(symbol)
            if xq and xq.get("price"):
                results[eng] = {"price": xq["price"], "change_pct": xq.get("change_pct")}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)

    # ── 引擎4: yfinance（需代理，带重试）─────────────────────
    eng = "yfinance"
    if CB.can_call(eng):
        try:
            yf_sym = f"{symbol}.SS" if symbol.startswith(("6","9")) else f"{symbol}.SZ"
            tk = _yf_ticker(yf_sym)
            p = _yf_fetch_price(tk)
            if p:
                results[eng] = {"price": float(p)}
                CB.record_success(eng)
            else:
                errors.append(f"{eng}: 无数据")
                CB.record_failure(eng)
        except Exception as e:
            errors.append(f"{eng}: {str(e)[:60]}")
            CB.record_failure(eng)

    # ── 写入缓存 ────────────────────────────────────────────
    if results:
        CACHE.set(cache_key, {"price": list(results.values())[0].get("price"),
                              "results": {k: {"price": v.get("price")} for k, v in results.items()}})

    return {"results": results, "errors": errors,
            "_breaker": CB.status_snapshot(),
            "_market": market["state"], "_cache_ttl": market["cache_ttl_minutes"]}


def fetch_hk_quote(symbol: str) -> Dict:
    results, errors = {}, []
    t = _tencent_raw(symbol, "HK")
    if t and t.get("price"): results["tencent"] = {"price": t["price"]}
    else: errors.append("tencent_http 无数据")
    s = _sina_quote(symbol, "HK")
    if s and s.get("price"): results["sina"] = {"price": s["price"]}
    else: errors.append("sina 无数据")
    try:
        tk = _yf_ticker(f"{symbol}.HK")
        p = _yf_fetch_price(tk)
        if p: results["yfinance"] = {"price": float(p)}
    except Exception as e: errors.append(f"yfinance: {str(e)[:60]}")
    return {"results": results, "errors": errors}


def fetch_a_kline(symbol: str, start: str, end: str) -> Dict:
    b = _baostock_kline(symbol, start, end)
    return {"results": {"baostock": b} if b else {}, "errors": [] if b else ["baostock 无数据"]}


def fetch_financial(symbol: str) -> Dict:
    b = _baostock_financial(symbol)
    return {"results": {"baostock": b} if b else {}, "errors": [] if b else ["baostock 无数据"]}


def _baostock_profile(symbol: str) -> Optional[Dict]:
    """baostock 公司概况：基本信息 + 行业分类 + 最近4季财务摘要"""
    import baostock as bs
    from datetime import datetime
    prefix = "sh." if symbol.startswith(("6","9")) else "sz."
    code = prefix + symbol
    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull
        bs.login()
        sys.stdout = old_stdout

        # 1) 基本信息
        rs = bs.query_stock_basic(code=code)
        basic = {}
        if rs.error_code == '0':
            while rs.next():
                vals = rs.get_row_data()
                if vals and len(vals) >= 6:
                    basic = {"code": vals[0], "name": vals[1], "ipo_date": vals[2],
                             "out_date": vals[3], "type": vals[4], "status": vals[5]}
                    break

        # 2) 行业分类
        rs2 = bs.query_stock_industry(code=code)
        industry = {}
        if rs2.error_code == '0':
            while rs2.next():
                vals = rs2.get_row_data()
                if vals and len(vals) >= 4:
                    industry = {"update_date": vals[0], "code": vals[1],
                                "industry_code": vals[2], "industry_name": vals[3]}
                    break

        # 3) 最近4季盈利摘要
        current_year = datetime.now().year
        recent_profit = []
        for y in [current_year, current_year - 1]:
            for q in range(4, 0, -1):
                try:
                    rs3 = bs.query_profit_data(code, year=y, quarter=q)
                    if rs3.error_code == '0':
                        vals = rs3.get_row_data()
                        if vals and len(vals) >= 9:
                            recent_profit.append({
                                "period": f"{y}Q{q}",
                                "roe": float(vals[3]) if vals[3] else None,
                                "gross_margin": float(vals[5]) if vals[5] else None,
                                "net_margin": float(vals[4]) if vals[4] else None,
                                "net_profit": float(vals[6]) if vals[6] else None,
                                "eps_ttm": float(vals[7]) if vals[7] else None,
                                "revenue": float(vals[8]) if vals[8] else None,
                            })
                            if len(recent_profit) >= 4:
                                break
                except Exception:
                    pass
            if len(recent_profit) >= 4:
                break

        sys.stdout = devnull
        bs.logout()
        sys.stdout = old_stdout

        return {
            "basic": basic,
            "industry": industry,
            "recent_quarters": recent_profit,
            "source": "baostock"
        }
    except Exception:
        try:
            sys.stdout = devnull; bs.logout()
        except Exception:
            pass
        sys.stdout = old_stdout
        return None
    finally:
        try: sys.stdout = old_stdout
        except: pass
        try: devnull.close()
        except: pass


def fetch_profile(symbol: str) -> Dict:
    """公司概况：基本信息 + 行业分类 + 最近财务摘要"""
    b = _baostock_profile(symbol)
    return {"results": {"baostock": b} if b else {}, "errors": [] if b else ["baostock 无数据"]}


# ═══════════════════════════════ 引擎 9: adata 财务核心指标 ═══════════════
def _adata_financial(symbol: str) -> Optional[Dict]:
    """adata 财务核心指标：多年×43列完整财务数据"""
    try:
        import adata
        df = adata.stock.finance.get_core_index(stock_code=symbol)
        if df is None or df.empty:
            return None
        # 按报告日期排序，最新在后
        df = df.sort_values('report_date')
        # 转为字典列表（只保留最近20期，避免数据过大）
        cols_keep = [c for c in df.columns if c not in ['stock_code', 'short_name']]
        rows = df[cols_keep].tail(20).to_dict('records')
        # 提取最新一期摘要
        latest = rows[-1] if rows else {}
        return {
            "summary": {
                "latest_period": latest.get("report_date"),
                "report_type": latest.get("report_type"),
                "basic_eps": latest.get("basic_eps"),
                "net_asset_ps": latest.get("net_asset_ps"),
                "total_rev": latest.get("total_rev"),
                "net_profit": latest.get("net_profit_attr_sh"),
                "roe": latest.get("roe_wtd"),
                "gross_margin": latest.get("gross_margin"),
                "net_margin": latest.get("net_margin"),
                "oper_cf_ps": latest.get("oper_cf_ps"),
                "asset_liab_ratio": latest.get("asset_liab_ratio"),
                "curr_ratio": latest.get("curr_ratio"),
                "quick_ratio": latest.get("quick_ratio"),
                "total_rev_yoy": latest.get("total_rev_yoy_gr"),
                "net_profit_yoy": latest.get("net_profit_yoy_gr"),
            },
            "rows": rows,
            "row_count": len(rows),
            "columns": list(cols_keep),
            "source": "adata"
        }
    except Exception as e:
        return None


# ═══════════════════════════════ 引擎 10: baostock 业绩预告/快报/营运 ═══════════════
def _baostock_forecast(symbol: str) -> Optional[Dict]:
    """baostock 业绩预告"""
    import baostock as bs
    prefix = "sh." if symbol.startswith(("6","9")) else "sz."
    code = prefix + symbol
    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull; bs.login(); sys.stdout = old_stdout
        rs = bs.query_forecast_report(code, start_date='2024-01-01', end_date='2027-01-01')
        rows = []
        if rs.error_code == '0':
            while rs.next():
                vals = rs.get_row_data()
                if vals and len(vals) >= 7:
                    rows.append({
                        "code": vals[0], "pub_date": vals[1], "stat_date": vals[2],
                        "type": vals[3], "abstract": vals[4],
                        "chg_pct_up": vals[5], "chg_pct_down": vals[6]
                    })
        sys.stdout = devnull; bs.logout(); sys.stdout = old_stdout
        return {"rows": rows, "count": len(rows), "source": "baostock"} if rows else None
    except Exception:
        try: sys.stdout = devnull; bs.logout()
        except: pass
        sys.stdout = old_stdout
        return None
    finally:
        try: sys.stdout = old_stdout
        except: pass
        try: devnull.close()
        except: pass


def _baostock_express(symbol: str) -> Optional[Dict]:
    """baostock 业绩快报"""
    import baostock as bs
    prefix = "sh." if symbol.startswith(("6","9")) else "sz."
    code = prefix + symbol
    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull; bs.login(); sys.stdout = old_stdout
        rs = bs.query_performance_express_report(code, start_date='2024-01-01', end_date='2027-01-01')
        rows = []
        if rs.error_code == '0':
            fields = rs.fields if hasattr(rs, 'fields') else []
            while rs.next():
                vals = rs.get_row_data()
                if vals and len(vals) >= 11:
                    rows.append({
                        "code": vals[0], "pub_date": vals[1], "stat_date": vals[2],
                        "update_date": vals[3], "total_asset": vals[4], "net_asset": vals[5],
                        "eps_chg_pct": vals[6], "roe": vals[7], "eps": vals[8],
                        "rev_yoy": vals[9], "op_yoy": vals[10]
                    })
        sys.stdout = devnull; bs.logout(); sys.stdout = old_stdout
        return {"rows": rows, "count": len(rows), "source": "baostock"} if rows else None
    except Exception:
        try: sys.stdout = devnull; bs.logout()
        except: pass
        sys.stdout = old_stdout
        return None
    finally:
        try: sys.stdout = old_stdout
        except: pass
        try: devnull.close()
        except: pass


def _baostock_operation(symbol: str) -> Optional[Dict]:
    """baostock 营运能力（应收周转/存货周转/资产周转）"""
    import baostock as bs
    from datetime import datetime
    prefix = "sh." if symbol.startswith(("6","9")) else "sz."
    code = prefix + symbol
    current_year = datetime.now().year
    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull; bs.login(); sys.stdout = old_stdout
        rows = []
        for y in range(current_year - 2, current_year + 1):
            for q in range(1, 5):
                try:
                    rs = bs.query_operation_data(code, year=y, quarter=q)
                    if rs.error_code == '0':
                        vals = rs.get_row_data()
                        if vals and len(vals) >= 9:
                            rows.append({
                                "code": vals[0], "pub_date": vals[1], "stat_date": vals[2],
                                "nr_turn_ratio": float(vals[3]) if vals[3] else None,
                                "nr_turn_days": float(vals[4]) if vals[4] else None,
                                "inv_turn_ratio": float(vals[5]) if vals[5] else None,
                                "inv_turn_days": float(vals[6]) if vals[6] else None,
                                "ca_turn_ratio": float(vals[7]) if vals[7] else None,
                                "asset_turn_ratio": float(vals[8]) if vals[8] else None,
                            })
                except Exception:
                    pass
        sys.stdout = devnull; bs.logout(); sys.stdout = old_stdout
        return {"rows": rows, "count": len(rows), "source": "baostock"} if rows else None
    except Exception:
        try: sys.stdout = devnull; bs.logout()
        except: pass
        sys.stdout = old_stdout
        return None
    finally:
        try: sys.stdout = old_stdout
        except: pass
        try: devnull.close()
        except: pass


def _adata_shares(symbol: str) -> Optional[Dict]:
    """adata 股本结构变动"""
    try:
        import adata
        df = adata.stock.info.get_stock_shares(stock_code=symbol)
        if df is None or df.empty:
            return None
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata"}
    except Exception:
        return None


def _adata_concept(symbol: str) -> Optional[Dict]:
    """adata 概念板块"""
    try:
        import adata
        df = adata.stock.info.get_concept_east(stock_code=symbol)
        if df is None or df.empty:
            return None
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata"}
    except Exception:
        return None


def _adata_plate(symbol: str) -> Optional[Dict]:
    """adata 行业/板块/概念归属（东方财富）"""
    try:
        import adata
        df = adata.stock.info.get_plate_east(stock_code=symbol)
        if df is None or df.empty:
            return None
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata"}
    except Exception:
        return None


def _adata_north_flow() -> Optional[Dict]:
    """adata 北向资金30日净流入（沪股通/深股通/合计）"""
    try:
        import adata
        df = adata.sentiment.north.north_flow()
        if df is None or df.empty:
            return None
        df = df.sort_values('trade_date')
        rows = df.tail(30).to_dict('records')
        latest = rows[-1] if rows else {}
        return {
            "summary": {
                "latest_date": latest.get("trade_date"),
                "net_hgt": latest.get("net_hgt"),
                "net_sgt": latest.get("net_sgt"),
                "net_tgt": latest.get("net_tgt"),
            },
            "rows": rows,
            "count": len(rows),
            "source": "adata"
        }
    except Exception:
        return None


def _adata_stock_lifting() -> Optional[Dict]:
    """adata 当月解禁股数据"""
    try:
        import adata
        df = adata.sentiment.stock_lifting_last_month()
        if df is None or df.empty:
            return None
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata"}
    except Exception:
        return None


def _adata_popularity() -> Optional[Dict]:
    """adata 东方财富人气榜TOP100"""
    try:
        import adata
        df = adata.sentiment.hot.pop_rank_100_east()
        if df is None or df.empty:
            return None
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata"}
    except Exception:
        return None


def _adata_index_membership(symbol: str) -> Optional[Dict]:
    """adata 判断个股是否纳入主要指数（沪深300/中证500等）"""
    try:
        import adata
        indices = {"000300": "沪深300", "000905": "中证500", "000016": "上证50", "399006": "创业板指"}
        membership = []
        for idx_code, idx_name in indices.items():
            try:
                df = adata.stock.info.index_constituent(index_code=idx_code)
                if df is not None and not df.empty:
                    if symbol in df.iloc[:, 1].astype(str).values:
                        membership.append({"index_code": idx_code, "index_name": idx_name})
            except Exception:
                pass
        return {"membership": membership, "count": len(membership), "source": "adata"} if membership else None
    except Exception:
        return None


def _adata_concept_ths(symbol: str) -> Optional[Dict]:
    """adata 同花顺概念板块"""
    try:
        import adata
        df = adata.stock.info.get_concept_ths(stock_code=symbol)
        if df is None or df.empty:
            return None
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata_ths"}
    except Exception:
        return None


def _adata_hot_concept() -> Optional[Dict]:
    """adata 同花顺热门概念TOP20（市场情绪）"""
    try:
        import adata
        df = adata.sentiment.hot.hot_concept_20_ths()
        if df is None or df.empty:
            return None
        for col in df.columns:
            if hasattr(df[col].dtype, 'tz') or str(df[col].dtype).startswith('datetime'):
                df[col] = df[col].astype(str)
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata_ths"}
    except Exception:
        return None


def _adata_hot_rank() -> Optional[Dict]:
    """adata 同花顺热门股TOP100（市场热度）"""
    try:
        import adata
        df = adata.sentiment.hot.hot_rank_100_ths()
        if df is None or df.empty:
            return None
        for col in df.columns:
            if hasattr(df[col].dtype, 'tz') or str(df[col].dtype).startswith('datetime'):
                df[col] = df[col].astype(str)
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata_ths"}
    except Exception:
        return None


def _adata_market_five(symbol: str) -> Optional[Dict]:
    """adata 五档盘口"""
    try:
        import adata
        df = adata.stock.market.get_market_five(stock_code=symbol)
        if df is None or df.empty:
            return None
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata"}
    except Exception:
        return None


def _adata_north_flow_current() -> Optional[Dict]:
    """adata 北向资金实时"""
    try:
        import adata
        df = adata.sentiment.north.north_flow_current()
        if df is None or df.empty:
            return None
        # 转换 Timestamp 为字符串
        for col in df.columns:
            if hasattr(df[col].dtype, 'tz') or str(df[col].dtype).startswith('datetime'):
                df[col] = df[col].astype(str)
        rows = df.to_dict('records')
        latest = rows[-1] if rows else {}
        return {
            "summary": {
                "latest_time": str(latest.get("trade_time", "")),
                "net_hgt": latest.get("net_hgt"),
                "net_sgt": latest.get("net_sgt"),
                "net_tgt": latest.get("net_tgt"),
            },
            "rows": rows,
            "count": len(rows),
            "source": "adata"
        }
    except Exception:
        return None


def _adata_daily_movers() -> Optional[Dict]:
    """adata 每日异动股列表"""
    try:
        import adata
        df = adata.sentiment.hot.list_a_list_daily()
        if df is None or df.empty:
            return None
        # 转换 Timestamp 为字符串
        for col in df.columns:
            if hasattr(df[col].dtype, 'tz') or str(df[col].dtype).startswith('datetime'):
                df[col] = df[col].astype(str)
        rows = df.to_dict('records')
        return {"rows": rows, "count": len(rows), "source": "adata"}
    except Exception:
        return None


def _baostock_rates() -> Optional[Dict]:
    """baostock 贷款/存款利率（宏观补充）"""
    import baostock as bs
    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull; bs.login(); sys.stdout = old_stdout
        # 贷款利率
        loan_rows = []
        rs = bs.query_loan_rate_data(start_date='2023-01-01', end_date='2027-01-01')
        while rs.next():
            vals = rs.get_row_data()
            if vals and len(vals) >= 8:
                loan_rows.append({
                    "pub_date": vals[0], "rate_6m": vals[1], "rate_1y": vals[2],
                    "rate_1_3y": vals[3], "rate_3_5y": vals[4], "rate_above_5y": vals[5],
                })
        # 存款利率
        deposit_rows = []
        rs2 = bs.query_deposit_rate_data(start_date='2023-01-01', end_date='2027-01-01')
        while rs2.next():
            vals = rs2.get_row_data()
            if vals and len(vals) >= 9:
                deposit_rows.append({
                    "pub_date": vals[0], "demand": vals[1], "fixed_3m": vals[2],
                    "fixed_6m": vals[3], "fixed_1y": vals[4], "fixed_2y": vals[5],
                    "fixed_3y": vals[6], "fixed_5y": vals[7],
                })
        sys.stdout = devnull; bs.logout(); sys.stdout = old_stdout
        if not loan_rows and not deposit_rows:
            return None
        return {
            "loan": {"rows": loan_rows[-10:], "count": len(loan_rows)},
            "deposit": {"rows": deposit_rows[-10:], "count": len(deposit_rows)},
            "source": "baostock"
        }
    except Exception:
        try: sys.stdout = devnull; bs.logout()
        except: pass
        sys.stdout = old_stdout
        return None
    finally:
        try: sys.stdout = old_stdout
        except: pass
        try: devnull.close()
        except: pass


def fetch_comprehensive(symbol: str) -> Dict:
    """综合财务画像：adata财务核心 + baostock预告/快报/营运 + 股本结构 + 概念板块
    + 板块归属 + 北向资金 + 解禁数据 + 人气排名 + 指数成分
    + 同花顺概念 + 热门概念 + 热门股 + 五档盘口 + 北向实时 + 每日异动 + 利率
    一次调用获取公司分析所需的大部分量化数据（v3.9: 18个数据源）。
    """
    results, errors = {}, []

    # 1) adata 财务核心指标（43列×多年）
    a = _adata_financial(symbol)
    if a: results["adata_finance"] = a
    else: errors.append("adata finance 无数据")

    # 2) baostock 业绩预告
    f = _baostock_forecast(symbol)
    if f: results["forecast"] = f
    else: errors.append("baostock forecast 无数据")

    # 3) baostock 业绩快报
    e = _baostock_express(symbol)
    if e: results["express"] = e
    else: errors.append("baostock express 无数据")

    # 4) baostock 营运能力
    o = _baostock_operation(symbol)
    if o: results["operation"] = o
    else: errors.append("baostock operation 无数据")

    # 5) adata 股本结构
    s = _adata_shares(symbol)
    if s: results["shares"] = s
    else: errors.append("adata shares 无数据")

    # 6) adata 概念板块（东方财富）
    c = _adata_concept(symbol)
    if c: results["concept"] = c
    else: errors.append("adata concept 无数据")

    # 7) adata 行业/板块归属
    pl = _adata_plate(symbol)
    if pl: results["plate"] = pl
    else: errors.append("adata plate 无数据")

    # 8) adata 北向资金30日（全局数据）
    nf = _adata_north_flow()
    if nf: results["north_flow"] = nf
    else: errors.append("adata north_flow 无数据")

    # 9) adata 当月解禁股（全局数据）
    sl = _adata_stock_lifting()
    if sl: results["stock_lifting"] = sl
    else: errors.append("adata stock_lifting 无数据")

    # 10) adata 人气排名
    pop = _adata_popularity()
    if pop: results["popularity"] = pop
    else: errors.append("adata popularity 无数据")

    # 11) adata 指数成分股
    idx = _adata_index_membership(symbol)
    if idx: results["index_membership"] = idx
    else: errors.append("adata index_membership 无数据（未纳入主要指数）")

    # 12) adata 同花顺概念（v3.9新增）
    ct = _adata_concept_ths(symbol)
    if ct: results["concept_ths"] = ct
    else: errors.append("adata concept_ths 无数据")

    # 13) adata 同花顺热门概念TOP20（v3.9新增，全局市场情绪）
    hc = _adata_hot_concept()
    if hc: results["hot_concept"] = hc
    else: errors.append("adata hot_concept 无数据")

    # 14) adata 同花顺热门股TOP100（v3.9新增）
    hr = _adata_hot_rank()
    if hr: results["hot_rank"] = hr
    else: errors.append("adata hot_rank 无数据")

    # 15) adata 五档盘口（v3.9新增）
    mf = _adata_market_five(symbol)
    if mf: results["market_five"] = mf
    else: errors.append("adata market_five 无数据")

    # 16) adata 北向资金实时（v3.9新增）
    nfc = _adata_north_flow_current()
    if nfc: results["north_flow_current"] = nfc
    else: errors.append("adata north_flow_current 无数据")

    # 17) adata 每日异动股（v3.9新增）
    dm = _adata_daily_movers()
    if dm: results["daily_movers"] = dm
    else: errors.append("adata daily_movers 无数据")

    # 18) baostock 贷款/存款利率（v3.9新增，宏观补充）
    rt = _baostock_rates()
    if rt: results["rates"] = rt
    else: errors.append("baostock rates 无数据")

    return {"results": results, "errors": errors}


# ═══════════════════════════════ 引擎 11: adata 资金流向 ═══════════════
def fetch_capital_flow(symbol: str) -> Dict:
    """资金流向：主力/大单/中单/小单/超大单净流入"""
    try:
        import adata
        df = adata.stock.market.get_capital_flow(stock_code=symbol)
        if df is None or df.empty:
            return {"results": {}, "errors": ["adata capital_flow 无数据"]}
        # 只保留最近30天
        df = df.sort_values('trade_date').tail(30)
        rows = df.to_dict('records')
        # 提取最新一天摘要
        latest = rows[-1] if rows else {}
        return {
            "results": {
                "adata": {
                    "summary": {
                        "latest_date": latest.get("trade_date"),
                        "main_net_inflow": latest.get("main_net_inflow"),
                        "sm_net_inflow": latest.get("sm_net_inflow"),
                        "mid_net_inflow": latest.get("mid_net_inflow"),
                        "lg_net_inflow": latest.get("lg_net_inflow"),
                        "max_net_inflow": latest.get("max_net_inflow"),
                    },
                    "rows": rows,
                    "count": len(rows),
                }
            },
            "errors": []
        }
    except Exception as e:
        return {"results": {}, "errors": [f"adata: {str(e)[:60]}"]}


def fetch_forex(symbol: str) -> Dict:
    """外汇行情 — 首选 Jin10 MCP（Agent 侧调用 mcp_jin10_get_quote），yfinance 为脚本兜底"""
    results, errors = {}, []
    # Jin10 MCP 是外汇首选源（需 Agent 侧调用，此处标注）
    errors.append("外汇首选: 请用 mcp_jin10_get_quote(code='XAUUSD') 获取实时报价")
    # yfinance 兜底（需代理）
    yf_map = {"XAUUSD": "GC=F", "USOIL": "CL=F", "UKOIL": "BZ=F"}
    yf_sym = yf_map.get(symbol, f"{symbol}=X")
    try:
        tk = _yf_ticker(yf_sym)
        p = _yf_fetch_price(tk)
        if p: results["yfinance"] = {"price": float(p)}
    except Exception as e: errors.append(f"yfinance: {str(e)[:60]}")
    return {"results": results, "errors": errors}


def fetch_macro(indicator: str) -> Dict:
    """宏观指标 — 路由到 fetch_macro.py"""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch_macro.py")
    result = os.system(f"{sys.executable} {script} --category all --format json 2>/dev/null")
    return {"results": {}, "errors": [f"macro 路由到 fetch_macro.py (exit={result})"],
            "note": "请直接使用 python scripts/fetch_macro.py --category all --format markdown"}


def fetch_futures(symbol: str) -> Dict:
    results, errors = {}, []
    # 新浪期货（实时行情）
    s = _sina_futures(symbol)
    if s and s.get("price"): results["sina"] = {"price": s["price"], "name": s.get("name"), "change_pct": None}
    else: errors.append("sina futures 无数据")
    # AkShare（合约列表）
    try:
        a = _akshare_futures()
        if a: results["akshare"] = a
        else: errors.append("akshare futures 无数据")
    except Exception as e: errors.append(f"akshare futures: {str(e)[:60]}")
    return {"results": results, "errors": errors}


def fetch_fund(symbol: str) -> Dict:
    try: data = _akshare_fund_etf()
    except Exception as e: data = None; errors = [str(e)]
    return {"results": {"akshare": data} if data else {}, "errors": [] if data else ["akshare fund 无数据"]}


# ═══════════════════════════════ 校验 ═══════════════════════════════
def verify(results: Dict, threshold=0.02) -> Dict:
    """多源交叉校验 → 返回 {status, sources_used, distinct_origins, adopted_value, max_discrepancy, confidence, details}

    数据源独立性:
      - 交易所直连: tencent, sina, akshare (共享上游)
      - 独立数据库: baostock (证券宝)
      - 海外独立: yfinance (Yahoo)
      - 百度独立: baidu (adata/百度股市通)

    置信度等级:
      🟢 high       — ≥2独立源且差异 ≤2%
      🟡 medium     — 1独立源差异 ≤5%
      🔵 acceptable — 仅1源或全同源
      🔴 low        — 无数据
    """
    prices, names = {}, {}
    # 源归属映射
    ORIGIN_MAP = {
        "tencent": "exchange", "sina": "exchange", "akshare": "exchange",
        "baostock": "baostock", "yfinance": "yfinance", "baidu": "baidu",
        "tushare": "tushare", "xueqiu": "xueqiu",
    }
    for engine, data in (results.get("results") or {}).items():
        if isinstance(data, dict) and data.get("price"):
            prices[engine] = data["price"]
            if data.get("date"): names[engine] = f'{data["price"]}@{data["date"]}'
    vals = list(prices.values())
    n = len(vals)

    # 计算独立源数量
    origins = set(ORIGIN_MAP.get(eng, eng) for eng in prices)
    n_origins = len(origins)

    if n == 0: return {"status":"❌ 无数据","sources_used":0,"distinct_origins":0,"adopted_value":None,"confidence":"low","max_discrepancy":"N/A","details":{}}
    if n == 1:
        o = list(origins)[0]
        return {"status":f"⚠️ 仅单源({o})","sources_used":1,"distinct_origins":1,"adopted_value":vals[0],"confidence":"acceptable","max_discrepancy":"N/A","details":prices}

    mn, mx = min(vals), max(vals)
    disc = abs(mx-mn)/abs(mn) if mn else 0
    adopted = sorted(vals)[n//2] if n>=3 else sum(vals)/n

    # 置信度 — 加权独立源数量
    if n_origins >= 2 and disc <= threshold:
        conf, st = "high", f"✅ {n}源一致({n_origins}独立)"
    elif n >= 3 and disc <= threshold:
        conf, st = "medium", f"⚠️ {n}源一致(同源-{n_origins}独立)"
    elif disc <= 0.05:
        conf, st = "medium", f"⚠️ 部分一致(差异{disc*100:.1f}%, {n_origins}独立)"
    else:
        conf, st = "medium", f"❌ 差异过大({disc*100:.1f}%, {n_origins}独立)"

    return {"status":st,"sources_used":n,"distinct_origins":n_origins,
            "adopted_value":round(adopted,4),
            "max_discrepancy":f"{disc*100:.2f}%","confidence":conf,"details":prices,"origins":list(origins)}


def _schema_json() -> str:
    """输出自描述 JSON（--schema 模式）"""
    import json as _json
    market = _market_now()
    return _json.dumps({
        "name": "fetch_market_data.py",
        "version": "3.5.0",
        "description": "A股/港股/美股/期货/外汇/基金/宏观 统一取数引擎 — 多源交叉校验 + 熔断降级 + 交易时段感知缓存",
        "features": {
            "circuit_breaker": "3次失败→熔断→10min后半开探测→自动恢复",
            "market_clock": "交易时段感知缓存（盘中5min/盘后24h）",
            "output_contract": "标准信封 {ok, source, data, error, ts} + 熔断/市场元信息",
        },
        "categories": {
            "quote": {"markets": ["A","HK"], "description": "实时行情（7引擎5独立源）"},
            "kline": {"markets": ["A"], "description": "历史K线（Baostock）", "params": ["start","end","freq"]},
            "financial": {"markets": ["A"], "description": "5年多维财务报表（profit+balance+cashflow+dupont+growth+dividend）"},
            "profile": {"markets": ["A"], "description": "公司概况（基本信息+行业分类+最近4季财务摘要）"},
            "comprehensive": {"markets": ["A"], "description": "综合财务画像v3.9（18源：adata财务43列+baostock预告/快报/营运+股本+概念(东财+同花顺)+板块+北向资金(30日+实时)+解禁+人气+指数成分+热门概念+热门股+五档盘口+每日异动+利率）"},
            "capital_flow": {"markets": ["A"], "description": "资金流向（主力/大单/中单/小单/超大单，最近30天）"},
            "forex": {"description": "外汇行情（Jin10 MCP 首选，yfinance 兜底）"},
            "futures": {"description": "期货合约（新浪+AkShare）"},
            "fund": {"description": "ETF规模（AkShare）"},
            "macro": {"description": "宏观指标（暂未实现）"},
        },
        "current_market": {
            "state": market["state"],
            "is_trading_day": market["is_trading_day"],
            "is_trading_session": market["is_trading_session"],
            "cache_ttl_minutes": market["cache_ttl_minutes"],
            "beijing_time": market["beijing_time"],
        },
        "formats": ["json","markdown"],
        "exit_codes": {"0":"ok","1":"runtime_error","2":"config_error","3":"validation_error","4":"no_data","5":"dependency_missing"},
        "engines": {
            "tencent_http": "✅ A/H股实时行情",
            "sina_https": "✅ A/H股实时行情+五档盘口",
            "baostock": "✅ A股K线/财务EOD",
            "akshare": "✅ A股实时行情（翻页兜底）",
            "baidu": "✅ A股独立源（adata→百度股市通）",
            "tushare": "✅ A股独立源（T+1，独立数据库）",
            "xueqiu": "✅ A股独立源（cookie→API）",
            "yfinance": "⚠️ 港/美股（需代理，带指数退避重试）",
            "efinance": "❌ 东方财富IP被封",
        },
        "examples": [
            "python fetch_market_data.py --category quote --symbol 600519 --market A",
            "python fetch_market_data.py --category quote --symbol 600519 --format markdown",
            "python fetch_market_data.py --category quote --symbol 600519 --force",
            "python fetch_market_data.py --schema",
        ]
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════ 配置加载 ═══════════════════════════
def _load_config() -> Dict:
    """加载 YAML 配置（config/engines.yaml），降级返回默认值"""
    try:
        import yaml
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "engines.yaml")
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass
    return {}

CONFIG = _load_config()

# ── 熔断器 + 缓存初始化 ────────────────────────────────────
_breaker_config = CONFIG.get("breaker", {})
CB = BreakerRegistry(_breaker_config)
CACHE = MarketCache()

# ── 市场时钟 ──────────────────────────────────────────────
def _market_now():
    """获取当前市场状态"""
    return get_market_status()

MARKET = _market_now()


# ═══════════════════════════════ main ═══════════════════════════════
def main():
    t_start = datetime.now()
    p = argparse.ArgumentParser("jw-investment-data v3.0")
    p.add_argument("--category", choices=["quote","kline","financial","profile","comprehensive","capital_flow","macro","forex","futures","fund"])
    p.add_argument("--symbol"); p.add_argument("--market", default="A")
    p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--freq", default="daily")
    p.add_argument("--save"); p.add_argument("--proxy")
    p.add_argument("--format", default="json", choices=["json","markdown"], help="输出格式: json(机器读) | markdown(人读)")
    p.add_argument("--force", action="store_true", help="跳过缓存 + 重置熔断状态，强制实时获取")
    p.add_argument("--schema", action="store_true", help="输出自描述JSON（参数定义）")
    p.add_argument("--version", action="store_true", help="输出版本号")
    args = p.parse_args()

    if args.version:
        print(f"fetch_market_data v{__version__}")
        return 0
    # --schema 优先
    if args.schema:
        print(_schema_json())
        return 0
    if args.version:
        print(f"fetch_market_data v{__version__}")
        return 0

    # 非 schema 模式需要 --category 和 --symbol
    if not args.category or not args.symbol:
        p.error("--category and --symbol are required (unless --schema)")

    _setup_proxy(args.proxy)

    def _d(d): return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if d else None
    s, e = _d(args.start), _d(args.end) or datetime.now().strftime("%Y-%m-%d")

    cat = args.category; sym = args.symbol; mkt = args.market

    try:
        if cat == "quote":
            data = fetch_a_quote(sym, force_cache=args.force) if mkt=="A" else fetch_hk_quote(sym) if mkt=="HK" else {"error":f"不支持market={mkt}"}
        elif cat == "kline" and mkt == "A": data = fetch_a_kline(sym, s or "2026-01-01", e)
        elif cat == "financial": data = fetch_financial(sym)
        elif cat == "profile": data = fetch_profile(sym)
        elif cat == "comprehensive": data = fetch_comprehensive(sym)
        elif cat == "capital_flow": data = fetch_capital_flow(sym)
        elif cat == "forex": data = fetch_forex(sym)
        elif cat == "macro": data = fetch_macro(sym)
        elif cat == "futures": data = fetch_futures(sym)
        elif cat == "fund": data = fetch_fund(sym)
        else: data = {"error": f"不支持 {cat}/{mkt}"}
    except Exception as exc:
        latency_ms = int((datetime.now() - t_start).total_seconds() * 1000)
        err = envelope_error(1, str(exc), source=f"{cat}/{sym}/{mkt}", retryable=True,
                            meta={"latency_ms": latency_ms, "breaker": CB.status_snapshot()})
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 1

    v = verify(data) if data.get("results") else {"status":"N/A","confidence":"low"}

    latency_ms = int((datetime.now() - t_start).total_seconds() * 1000)
    market = _market_now()

    # ── 构建输出（v3.0 标准信封） ──────────────────────────
    breaker_info = data.pop("_breaker", CB.status_snapshot())
    market_state = data.pop("_market", market["state"])
    cache_ttl = data.pop("_cache_ttl", market["cache_ttl_minutes"])

    meta = {
        "schema_version": "3.0.0",
        "latency_ms": latency_ms,
        "config_loaded": bool(CONFIG),
        "breaker": breaker_info,
        "market": {
            "state": market_state,
            "cache_ttl_minutes": cache_ttl,
            "is_trading_day": market["is_trading_day"],
            "is_trading_session": market["is_trading_session"],
            "beijing_time": market["beijing_time"],
        }
    }

    # 输出格式路由
    is_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    use_markdown = args.format == "markdown" or (is_tty and CONFIG.get("output",{}).get("tty_auto_markdown", True))

    if use_markdown:
        payload = {"query":{"category":cat,"symbol":sym,"market":mkt,
                   "proxy":PROXY_URL or "未配置","timestamp":datetime.now().isoformat()},
                   "engine_status":ENGINE_STATUS,"verification":v,"data":data}
        print(_format_markdown(payload))
    else:
        envelope = combined_envelope(v, data.get("results", {}), data.get("errors", []),
                                     meta_overrides=meta) if data.get("results") is not None else \
                   envelope_error(4, "无数据", source=f"{cat}/{sym}/{mkt}", meta=meta)
        j = json.dumps(envelope, ensure_ascii=False, indent=2)
        if args.save:
            with open(args.save,"w") as f: f.write(j)
        print(j)

    # 标准退出码
    conf = v.get("confidence","")
    if conf == "low": return 4      # no_data
    if conf == "acceptable": return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
