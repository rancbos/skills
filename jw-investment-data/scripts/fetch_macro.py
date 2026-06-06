#!/usr/bin/env python3
"""
fetch_macro.py — 宏观数据采集引擎 v3.4
═══════════════════════════════════════════

数据源:
  东方财富 API  ─→ CPI/PMI/GDP/PPI/固投/工业增加值/财政收入（免费、无认证）
  Baostock      ─→ M0/M1/M2/存贷利率/准备金率
  中国货币网     ─→ LPR 1Y/5Y
  世界银行 API   ─→ 中美GDP/CPI年度背景
  Jin10 MCP     ─→ 经济日历 + 美国宏观快讯 (Agent侧实时查询)

交叉验证:
  M2: Baostock vs 东方财富 RPT_ECONOMY_MONEY，差异≤3%通过
  CPI/PMI/GDP: 东方财富 + Jin10日历交叉验证(Agent侧)
  固投/工业增加值: 东方财富 + Jin10新闻交叉验证(Agent侧)

输出: JSON (标准信封) 或 Markdown (人读)
  错误聚合: 末尾报告各数据源成功/失败状态

用法:
  python fetch_macro.py --category all --format markdown
  python fetch_macro.py --category cpi
  python fetch_macro.py --category growth     # GDP+PMI
  python fetch_macro.py --category inflation  # CPI+PPI
  python fetch_macro.py --category money      # M2+LPR+利率+准备金
  python fetch_macro.py --force               # 跳过缓存强制刷新
  python fetch_macro.py --schema              # 自描述
"""

import argparse, json, os, re, sys, time, math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import urllib.error

# 内部模块
_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))
from format_macro import format_macro as _format_markdown

__version__ = "3.5.0"
CACHE_DIR = os.path.expanduser("~/.hermes/cache/jw-investment-data/macro")
os.makedirs(CACHE_DIR, exist_ok=True)

def _ok(source, data, meta=None):
    return {"ok": True, "source": source, "data": data, "ts": int(time.time()), "meta": meta or {}}


def _err(code, msg, source="", retryable=False, meta=None):
    return {"ok": False, "source": source, "error": {"code": code, "message": msg, "retryable": retryable},
            "ts": int(time.time()), "meta": meta or {}}


# ═══════════════════════════════ 缓存 ═══════════════════════════
_CACHE_TTL = None  # 延迟加载，从 engines.yaml 读取

def _load_ttl() -> dict:
    """从 engines.yaml 读取宏观 TTL，fallback 到默认值"""
    defaults = {"m2": 35, "cpi": 35, "pmi": 5, "gdp": 90, "ppi": 35,
                "lpr": 25, "rrr": 90, "rate": 90, "calendar": 1, "worldbank": 365}
    try:
        import yaml
        cfg_path = Path(__file__).parent.parent / "config" / "engines.yaml"
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
        macro_cache = cfg.get("macro", {}).get("cache", {})
        for k in defaults:
            yk = f"{k}_ttl_days"
            if yk in macro_cache:
                defaults[k] = int(macro_cache[yk])
    except Exception:
        pass
    return defaults


def _get_ttl() -> dict:
    global _CACHE_TTL
    if _CACHE_TTL is None:
        _CACHE_TTL = _load_ttl()
    return _CACHE_TTL


def _cache_path(indicator: str, period: str) -> str:
    return os.path.join(CACHE_DIR, f"{indicator}_{period}.json")


def _cache_get(indicator: str, period: str, ttl_days: int = None) -> Optional[Dict]:
    ttl = ttl_days or _get_ttl().get(indicator, 30)
    fp = _cache_path(indicator, period)
    if not os.path.exists(fp): return None
    try:
        with open(fp) as f: data = json.load(f)
        age = (time.time() - data.get("cached_at", 0)) / 86400
        if age > ttl: return None
        if not data.get("verified"): return None
        return data
    except: return None


def _cache_set(indicator: str, period: str, data: Dict):
    data["cached_at"] = time.time()
    try:
        with open(_cache_path(indicator, period), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass


# ═══════════════════════════════ 东方财富 API ═══════════════════════
EASTMONEY_BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"
EASTMONEY_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; jw-investment-data/3.1)"}


def _em_fetch(report_name: str, page_size: int = 3, extra_cols: str = "") -> Optional[List[Dict]]:
    """通用东方财富取数"""
    url = (f"{EASTMONEY_BASE}?sortColumns=REPORT_DATE&sortTypes=-1"
           f"&pageSize={page_size}&pageNumber=1"
           f"&reportName={report_name}&columns=ALL{'+' + extra_cols if extra_cols else ''}")
    try:
        req = urllib.request.Request(url, headers=EASTMONEY_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get("success") and data["result"] and data["result"]["data"]:
            return data["result"]["data"]
        return None
    except Exception:
        return None


def _em_cpi() -> Optional[Dict]:
    """CPI 居民消费价格指数"""
    rows = _em_fetch("RPT_ECONOMY_CPI", page_size=5)
    if not rows: return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else latest
    return {
        "period": latest["REPORT_DATE"][:7],
        "cpi_yoy": latest.get("NATIONAL_SAME"),       # 同比
        "cpi_mom": latest.get("NATIONAL_SEQUENTIAL"),  # 环比
        "core_cpi": latest.get("CITY_SAME"),            # 城市(代理核心CPI)
        "prev_yoy": prev.get("NATIONAL_SAME"),
        "prev_mom": prev.get("NATIONAL_SEQUENTIAL"),
        "source": "eastmoney",
        "time_series": [
            {"period": r["REPORT_DATE"][:7], "yoy": r.get("NATIONAL_SAME"), "mom": r.get("NATIONAL_SEQUENTIAL")}
            for r in rows[:6]
        ]
    }


def _em_ppi() -> Optional[Dict]:
    """PPI 工业生产者出厂价格指数"""
    rows = _em_fetch("RPT_ECONOMY_PPI", page_size=5)
    if not rows: return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else latest
    return {
        "period": latest["REPORT_DATE"][:7],
        "ppi_yoy": latest.get("BASE_SAME"),
        "prev_yoy": prev.get("BASE_SAME"),
        "source": "eastmoney",
        "time_series": [
            {"period": r["REPORT_DATE"][:7], "yoy": r.get("BASE_SAME")} for r in rows[:6]
        ]
    }


def _em_pmi() -> Optional[Dict]:
    """PMI 采购经理人指数"""
    rows = _em_fetch("RPT_ECONOMY_PMI", page_size=5)
    if not rows: return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else latest
    return {
        "period": latest["REPORT_DATE"][:7],
        "manufacturing": latest.get("MAKE_INDEX"),      # 制造业PMI
        "non_manufacturing": latest.get("NMAKE_INDEX"),  # 非制造业PMI
        "prev_manufacturing": prev.get("MAKE_INDEX"),
        "prev_non_manufacturing": prev.get("NMAKE_INDEX"),
        "source": "eastmoney",
        "time_series": [
            {"period": r["REPORT_DATE"][:7], "make": r.get("MAKE_INDEX"), "nmake": r.get("NMAKE_INDEX")}
            for r in rows[:6]
        ]
    }


def _em_gdp() -> Optional[Dict]:
    """GDP 国内生产总值（季度）"""
    rows = _em_fetch("RPT_ECONOMY_GDP", page_size=3)
    if not rows: return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else latest
    return {
        "period": latest["TIME"],  # "2026年第1季度"
        "gdp_amount": latest.get("DOMESTICL_PRODUCT_BASE"),  # 亿元
        "gdp_yoy": latest.get("SUM_SAME"),                   # 同比%
        "primary_yoy": latest.get("FIRST_SAME"),
        "secondary_yoy": latest.get("SECOND_SAME"),
        "tertiary_yoy": latest.get("THIRD_SAME"),
        "prev_yoy": prev.get("SUM_SAME"),
        "prev_amount": prev.get("DOMESTICL_PRODUCT_BASE"),
        "source": "eastmoney",
        "time_series": [
            {"period": r["TIME"], "amount": r.get("DOMESTICL_PRODUCT_BASE"), "yoy": r.get("SUM_SAME")}
            for r in rows
        ]
    }


def _em_fixed_invest() -> Optional[Dict]:
    """固定资产投资（累计同比）"""
    rows = _em_fetch("RPT_ECONOMY_ASSET_INVEST", page_size=5)
    if not rows: return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else latest
    return {
        "period": latest["REPORT_DATE"][:7],
        "invest_amount": latest.get("BASE"),           # 累计金额(亿)
        "invest_yoy": latest.get("BASE_SAME"),         # 累计同比%
        "invest_accumulate": latest.get("BASE_ACCUMULATE"),
        "prev_yoy": prev.get("BASE_SAME"),
        "source": "eastmoney",
        "time_series": [
            {"period": r["REPORT_DATE"][:7], "amount": r.get("BASE"), "yoy": r.get("BASE_SAME")}
            for r in rows[:6]
        ]
    }


def _em_industrial_output() -> Optional[Dict]:
    """工业增加值（当月同比）"""
    rows = _em_fetch("RPT_ECONOMY_INDUS_GROW", page_size=5)
    if not rows: return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else latest
    return {
        "period": latest["REPORT_DATE"][:7],
        "ind_yoy": latest.get("BASE_SAME"),             # 当月同比%
        "ind_accumulate": latest.get("BASE_ACCUMULATE"), # 累计同比%
        "prev_yoy": prev.get("BASE_SAME"),
        "source": "eastmoney",
        "time_series": [
            {"period": r["REPORT_DATE"][:7], "yoy": r.get("BASE_SAME"), "accumulate": r.get("BASE_ACCUMULATE")}
            for r in rows[:6]
        ]
    }


def _em_fiscal_revenue() -> Optional[Dict]:
    """财政收入（累计同比）"""
    rows = _em_fetch("RPT_ECONOMY_INCOME", page_size=5)
    if not rows: return None
    latest = rows[0]
    prev = rows[1] if len(rows) > 1 else latest
    return {
        "period": latest["REPORT_DATE"][:7],
        "fiscal_amount": latest.get("BASE"),            # 累计金额(亿)
        "fiscal_yoy": latest.get("BASE_SAME"),          # 累计同比%
        "prev_yoy": prev.get("BASE_SAME"),
        "source": "eastmoney",
        "time_series": [
            {"period": r["REPORT_DATE"][:7], "amount": r.get("BASE"), "yoy": r.get("BASE_SAME")}
            for r in rows[:6]
        ]
    }


# ═══════════════════════════════ Baostock ═══════════════════════════
def _bs_login():
    import baostock as bs
    old = sys.stdout
    dn = open(os.devnull, 'w')
    sys.stdout = dn
    bs.login()
    sys.stdout = old
    return bs, old, dn


def _bs_logout(bs, old, dn):
    import baostock
    sys.stdout = dn
    bs.logout()
    sys.stdout = old
    dn.close()


def _bs_money_supply() -> Optional[Dict]:
    try:
        bs, old, dn = _bs_login()
        rs = bs.query_money_supply_data_month(start_date='2025-01', end_date='2026-06')
        rows = []
        while rs.error_code == '0' and rs.next(): rows.append(rs.get_row_data())
        _bs_logout(bs, old, dn)
        if len(rows) < 2: return None
        latest, prev = rows[-1], rows[-2]
        return {
            "period": f"{latest[0]}-{latest[1].zfill(2)}",
            "m0": float(latest[2]), "m0_yoy": float(latest[3]),
            "m1": float(latest[5]), "m1_yoy": float(latest[6]),
            "m2": float(latest[8]), "m2_yoy": float(latest[9]),
            "prev_m2": float(prev[8]), "prev_m2_yoy": float(prev[9]),
            "source": "baostock",
            "time_series": [{"period": f"{r[0]}-{r[1].zfill(2)}", "m2": float(r[8]), "m2_yoy": float(r[9]),
                             "m1": float(r[5]), "m1_yoy": float(r[6])} for r in rows[-6:]]
        }
    except: return None


def _bs_rates() -> Optional[Dict]:
    try:
        bs, old, dn = _bs_login()
        rs_d = bs.query_deposit_rate_data(start_date='2024-01-01', end_date='2026-06-01')
        deps = []
        while rs_d.error_code == '0' and rs_d.next(): deps.append(rs_d.get_row_data())
        rs_l = bs.query_loan_rate_data(start_date='2024-01-01', end_date='2026-06-01')
        loans = []
        while rs_l.error_code == '0' and rs_l.next(): loans.append(rs_l.get_row_data())
        _bs_logout(bs, old, dn)
        result = {"source": "baostock"}
        if deps:
            d = deps[-1]
            result["deposit_rate"] = {"date": d[0], "demand": float(d[1]) if d[1] else None,
                "fix_3m": float(d[2]) if d[2] else None, "fix_6m": float(d[3]) if d[3] else None,
                "fix_1y": float(d[4]) if d[4] else None}
        if loans:
            l = loans[-1]
            result["loan_rate"] = {"date": l[0], "lt_6m": float(l[1]) if l[1] else None,
                "lt_1y": float(l[2]) if l[2] else None, "gt_5y": float(l[4]) if len(l)>4 and l[4] else None}
        return result if len(result) > 1 else None
    except: return None


def _bs_reserve_ratio() -> Optional[Dict]:
    try:
        bs, old, dn = _bs_login()
        rs = bs.query_required_reserve_ratio_data(start_date='2022-01-01', end_date='2026-06-01', yearType='0')
        rows = []
        while rs.error_code == '0' and rs.next(): rows.append(rs.get_row_data())
        _bs_logout(bs, old, dn)
        if rows:
            latest = rows[-1]
            return {"date": latest[0], "large_bank": float(latest[1]) if latest[1] else None,
                    "small_bank": float(latest[2]) if latest[2] else None, "source": "baostock",
                    "change_history": [{"date": r[0], "large": float(r[1]) if r[1] else None,
                     "small": float(r[2]) if r[2] else None} for r in rows[-5:]]}
        return None
    except: return None


# ═══════════════════════════════ 交叉验证 ═══════════════════════════
def _verify_two_source(indicator: str, period: str, source1: Dict, source2: Dict, threshold: float = 0.03) -> Dict:
    """双源交叉验证 → 差异≤3%通过，写入缓存"""
    v1 = source1["value"]
    v2 = source2["value"]
    if v1 and v2 and abs(v1) > 1e-9:
        disc = abs(v2 - v1) / abs(v1)
    else:
        disc = 0

    verified = disc <= threshold
    result = {
        "indicator": indicator, "period": period,
        "value": round((v1 + v2) / 2, 4),  # 均值
        "sources": [
            {"name": source1["name"], "value": v1},
            {"name": source2["name"], "value": v2},
        ],
        "discrepancy_pct": round(disc * 100, 2),
        "verified": verified,
        "verified_at": datetime.now().isoformat(),
        "note": "✅ 双源一致" if verified else f"⚠️ 差异{disc*100:.1f}%>3%，待第三源仲裁"
    }
    _cache_set(indicator, period, result)
    return result


def _verify_single(indicator: str, period: str, value: float, source_name: str, note: str = "") -> Dict:
    """单源验证（降级标注）"""
    cached = _cache_get(indicator, period)
    if cached: return cached
    result = {
        "indicator": indicator, "period": period, "value": value,
        "sources": [{"name": source_name, "value": value}],
        "discrepancy_pct": 0, "verified": True,
        "verified_at": datetime.now().isoformat(),
        "note": note or f"单源({source_name})，待第二源交叉验证"
    }
    _cache_set(indicator, period, result)
    return result


# ═══════════════════════════════ LPR (中国货币网) ═══════════════════════
def _fetch_lpr() -> Optional[Dict]:
    """LPR 贷款市场报价利率 — chinamoney.com.cn"""
    url = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis?pageSize=5&pageNum=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        records = data.get("records", [])
        if not records: return None
        latest = records[0]
        prev = records[1] if len(records) > 1 else latest
        return {
            "date": latest["showDateCN"],
            "lpr_1y": float(latest["1Y"]),
            "lpr_5y": float(latest["5Y"]),
            "prev_1y": float(prev["1Y"]),
            "prev_5y": float(prev["5Y"]),
            "source": "chinamoney",
            "time_series": [
                {"date": r["showDateCN"], "1y": float(r["1Y"]), "5y": float(r["5Y"])}
                for r in records[:5]
            ]
        }
    except: return None


# ═══════════════════════════════ 世界银行 API ═══════════════════════
WORLDBANK_BASE = "https://api.worldbank.org/v2/country"


def _wb_fetch(country: str, indicator: str, label: str) -> Optional[float]:
    """世界银行 API — 单指标取最新值"""
    url = f"{WORLDBANK_BASE}/{country}/indicator/{indicator}?format=json&per_page=2&mrv=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if len(data) > 1 and data[1]:
            return float(data[1][0]["value"])
        return None
    except: return None


def _wb_context() -> Optional[Dict]:
    """世界银行长期宏观背景 — 中美GDP/CPI"""
    us_gdp = _wb_fetch("US", "NY.GDP.MKTP.CD", "US GDP")
    cn_gdp = _wb_fetch("CN", "NY.GDP.MKTP.CD", "CN GDP")
    us_cpi = _wb_fetch("US", "FP.CPI.TOTL.ZG", "US CPI")
    if not us_gdp:
        return None
    return {
        "us_gdp_trillion": round(us_gdp / 1e12, 2) if us_gdp else None,
        "cn_gdp_trillion": round(cn_gdp / 1e12, 2) if cn_gdp else None,
        "us_cpi_pct": round(us_cpi, 1) if us_cpi else None,
        "note": "世界银行年度数据(最新:2024年)，非实时",
        "source": "worldbank",
    }


# ═══════════════════════════════ Jin10 US 快讯提示 ═══════════════════
def _us_macro_hint() -> Dict:
    """美国宏观快讯 — Agent侧用 mcp_jin10_search_flash 实时查询"""
    return {
        "hint": "**Agent侧实时查询**: 调用 `mcp_jin10_search_flash(keyword='美国 经济')` 获取最新美国宏观快讯",
        "search_keywords": ["非农", "CPI", "美联储", "GDP", "PCE", "初请", "零售", "PMI", "ISM"],
        "note": "以上为建议搜索词，Agent 应根据当前日期选择最相关的 3-5 个关键词"
    }


def _calendar_hint() -> Dict:
    """经济日历 — Agent侧用 mcp_jin10_list_calendar 实时查询"""
    return {
        "hint": "**Agent侧实时查询**: 调用 `mcp_jin10_list_calendar()` 获取本周财经日历",
        "filter_cn": "筛选关键词: 中国/PMI/CPI/GDP/社融/LPR/MLF/降准/工业/贸易",
        "importance": "⭐4级以上重点关注, ⭐3级纳入观察",
        "note": "日历数据实时变化，请勿依赖缓存的日期列表。每次查询须调用 MCP 获取最新。"
    }


# ═══════════════════════════════ schema ═══════════════════════════
def _schema_json() -> str:
    return json.dumps({
        "name": "fetch_macro", "version": __version__,
        "description": "宏观数据采集引擎 — 东方财富(CPI/PMI/GDP/PPI/M2) + Baostock(货币/利率) + 中国货币网(LPR) + 世界银行(中美背景)",
        "categories": {
            "all": "宏观全景", "money": "M0/M1/M2+LPR+利率+准备金",
            "rates": "存贷利率", "lpr": "LPR",
            "cpi": "CPI", "ppi": "PPI", "pmi": "PMI", "gdp": "GDP",
            "growth": "经济增长(GDP+PMI)", "inflation": "通胀(CPI+PPI)",
            "invest": "固定资产投资", "industrial": "工业增加值",
            "fiscal": "财政收入", "real_activity": "实体经济(固投+工业+财政)",
            "calendar": "经济日历(Jin10 MCP)", "reserve": "准备金率",
        },
        "data_sources": {
            "eastmoney": "✅ CPI/PMI/GDP/PPI/固投/工业增加值/财政收入 (免费JSON API)",
            "baostock": "✅ M0/M1/M2/利率/准备金率 (免费)",
            "chinamoney": "✅ LPR 1Y/5Y (免费JSON API)",
            "worldbank": "✅ 中美GDP/CPI年度背景 (免费JSON API)",
            "jin10_mcp": "✅ 经济日历+美国宏观 (Agent侧MCP实时查询)",
            "stats_gov": "❌ IP被WAF封锁 — 暂不可用",
        },
        "cross_verification": {
            "M2": "Baostock vs 东方财富 RPT_ECONOMY_MONEY，差异≤3%通过",
            "CPI/PMI/GDP": "单源(东方财富)，待第二源确认",
        },
        "cache_dir": CACHE_DIR,
        "exit_codes": {"0": "ok", "1": "runtime", "4": "no_data"},
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════ main ═══════════════════════════════
def main():
    t_start = datetime.now()
    p = argparse.ArgumentParser(f"fetch_macro v{__version__}")
    p.add_argument("--category", default="all",
                   choices=["all", "money", "rates", "lpr", "cpi", "ppi", "pmi", "gdp",
                            "growth", "inflation", "reserve", "calendar",
                            "invest", "industrial", "fiscal", "real_activity"])
    p.add_argument("--format", default="json", choices=["json", "markdown"])
    p.add_argument("--force", action="store_true")
    p.add_argument("--schema", action="store_true")
    p.add_argument("--version", action="store_true")
    args = p.parse_args()

    if args.schema:
        print(_schema_json())
        return 0
    if args.version:
        print(f"fetch_macro v3.4.1")
        return 0

    force = args.force
    cat = args.category
    data = {}
    verifications = {}
    errors = []  # ★ 错误聚合器

    def _should_fetch(name): return cat in ("all", name)

    def _record_error(source: str, msg: str):
        errors.append({"source": source, "message": msg, "retryable": True})

    # ── 东方财富取数 ──
    if _should_fetch("cpi") or _should_fetch("inflation"):
        cpi = None if force else _cache_get("cpi", "latest")
        if not cpi:
            raw = _em_cpi()
            if raw:
                cpi = raw
                _cache_set("cpi", "latest",
                           {"period": raw["period"], "cpi_yoy": raw["cpi_yoy"], "cpi_mom": raw.get("cpi_mom"),
                            "source": "eastmoney", "verified": True})
            else:
                _record_error("eastmoney", "CPI 获取失败")
        if cpi: data["cpi"] = cpi

    if _should_fetch("ppi") or _should_fetch("inflation"):
        ppi = None if force else _cache_get("ppi", "latest")
        if not ppi:
            raw = _em_ppi()
            if raw:
                ppi = raw
                _cache_set("ppi", "latest",
                           {"period": raw["period"], "ppi_yoy": raw["ppi_yoy"], "source": "eastmoney", "verified": True})
            else:
                _record_error("eastmoney", "PPI 获取失败")
        if ppi: data["ppi"] = ppi

    if _should_fetch("pmi") or _should_fetch("growth"):
        pmi = None if force else _cache_get("pmi", "latest")
        if not pmi:
            raw = _em_pmi()
            if raw:
                pmi = raw
                _cache_set("pmi", "latest",
                           {"period": raw["period"], "manufacturing": raw["manufacturing"],
                            "source": "eastmoney", "verified": True})
            else:
                _record_error("eastmoney", "PMI 获取失败")
        if pmi: data["pmi"] = pmi

    if _should_fetch("gdp") or _should_fetch("growth"):
        gdp = None if force else _cache_get("gdp", "latest")
        if not gdp:
            raw = _em_gdp()
            if raw:
                gdp = raw
                _cache_set("gdp", "latest",
                           {"period": raw["period"], "gdp_yoy": raw["gdp_yoy"], "source": "eastmoney", "verified": True})
            else:
                _record_error("eastmoney", "GDP 获取失败")
        if gdp: data["gdp"] = gdp

    # ── 新增: 固定资产投资/工业增加值/财政收入 ──
    if _should_fetch("invest") or _should_fetch("real_activity"):
        invest = None if force else _cache_get("invest", "latest")
        if not invest:
            raw = _em_fixed_invest()
            if raw:
                invest = raw
                _cache_set("invest", "latest",
                           {"period": raw["period"], "invest_yoy": raw["invest_yoy"],
                            "source": "eastmoney", "verified": True})
            else:
                _record_error("eastmoney", "固定资产投资 获取失败")
        if invest: data["fixed_invest"] = invest

    if _should_fetch("industrial") or _should_fetch("real_activity"):
        ind = None if force else _cache_get("industrial", "latest")
        if not ind:
            raw = _em_industrial_output()
            if raw:
                ind = raw
                _cache_set("industrial", "latest",
                           {"period": raw["period"], "ind_yoy": raw["ind_yoy"],
                            "source": "eastmoney", "verified": True})
            else:
                _record_error("eastmoney", "工业增加值 获取失败")
        if ind: data["industrial_output"] = ind

    if _should_fetch("fiscal") or _should_fetch("real_activity"):
        fiscal = None if force else _cache_get("fiscal", "latest")
        if not fiscal:
            raw = _em_fiscal_revenue()
            if raw:
                fiscal = raw
                _cache_set("fiscal", "latest",
                           {"period": raw["period"], "fiscal_yoy": raw["fiscal_yoy"],
                            "source": "eastmoney", "verified": True})
            else:
                _record_error("eastmoney", "财政收入 获取失败")
        if fiscal: data["fiscal_revenue"] = fiscal

    # ★ 东方财富 M2 — 作为 Baostock M2 的第二源交叉验证
    def _em_m2() -> Optional[Dict]:
        rows = _em_fetch("RPT_ECONOMY_MONEY", page_size=2)
        if not rows: return None
        latest = rows[0]
        return {"period": latest["REPORT_DATE"][:7],
                "m2": float(latest.get("M2", 0)) if latest.get("M2") else None,
                "m2_yoy": float(latest.get("M2_SAME", 0)) if latest.get("M2_SAME") else None,
                "source": "eastmoney"}

    # ── Baostock 取数 ──
    if _should_fetch("money"):
        money = None if force else _cache_get("m2", "latest")
        if not money:
            raw = _bs_money_supply()
            if raw:
                money = raw
                # ★ 交叉验证: Baostock M2 vs 东方财富 M2
                em_m2 = _em_m2()
                if em_m2 and em_m2["m2_yoy"] and money["m2_yoy"]:
                    disc = abs(em_m2["m2_yoy"] - money["m2_yoy"]) / abs(money["m2_yoy"])
                    verified = disc <= 0.03
                    money["cross_verified"] = verified
                    money["cross_source"] = {"name": "eastmoney", "m2_yoy": em_m2["m2_yoy"],
                                              "period": em_m2["period"],
                                              "diff_pct": round(disc * 100, 2)}
                    money["cross_note"] = "✅ 双源一致" if verified else f"⚠️ 差异{disc*100:.1f}%>3%"
                elif em_m2:
                    money["cross_source"] = {"name": "eastmoney", "m2_yoy": em_m2["m2_yoy"],
                                              "period": em_m2["period"], "note": "无法对比(缺M2同比)"}
                else:
                    _record_error("eastmoney", "东方财富 M2 交叉验证源获取失败")
                _cache_set("m2", "latest",
                           {"period": raw["period"], "m2": raw["m2"], "m2_yoy": raw["m2_yoy"],
                            "source": "baostock", "verified": True,
                            "cross_verified": money.get("cross_verified", False),
                            "cross_source": money.get("cross_source")})
            else:
                _record_error("baostock", "M0/M1/M2 获取失败")
        if money: data["money"] = money

    if _should_fetch("rates"):
        rates = None if force else _cache_get("rate", "latest")
        if not rates:
            raw = _bs_rates()
            if raw:
                rates = raw
                _cache_set("rate", "latest", {"source": "baostock", "verified": True, **raw})
            else:
                _record_error("baostock", "存贷利率获取失败")
        if rates: data["rates"] = rates

    if _should_fetch("reserve"):
        rrr = None if force else _cache_get("rrr", "latest")
        if not rrr:
            raw = _bs_reserve_ratio()
            if raw:
                rrr = raw
                _cache_set("rrr", "latest", {"source": "baostock", "verified": True, **raw})
            else:
                _record_error("baostock", "准备金率获取失败")
        if rrr: data["reserve_ratio"] = rrr

    if _should_fetch("calendar"):
        data["calendar"] = _calendar_hint()

    if _should_fetch("money") or _should_fetch("lpr"):
        lpr = None if force else _cache_get("lpr", "latest")
        if not lpr:
            raw = _fetch_lpr()
            if raw:
                lpr = raw
                _cache_set("lpr", "latest", {"date": raw["date"], "lpr_1y": raw["lpr_1y"],
                           "lpr_5y": raw["lpr_5y"], "source": "chinamoney", "verified": True})
            else:
                _record_error("chinamoney", "LPR 获取失败")
        if lpr: data["lpr"] = lpr

    # 世界银行背景（所有模式附带）
    wb = None if force else _cache_get("worldbank", "latest")
    if not wb:
        raw = _wb_context()
        if raw:
            wb = raw
            _cache_set("worldbank", "latest", {"source": "worldbank", "verified": True, **raw})
        else:
            _record_error("worldbank", "世界银行 API 获取失败")
    if wb: data["worldbank"] = wb

    # 美国宏观提示
    data["us_macro"] = _us_macro_hint()

    # ── 交叉验证汇总 ──
    # M2 实时验证结果（在主流程中已完成）
    money = data.get("money", {})
    if money and money.get("cross_source"):
        verifications["M2"] = {
            "sources": [
                {"name": "baostock", "m2_yoy": money.get("m2_yoy")},
                {"name": money["cross_source"].get("name", "?"),
                 "m2_yoy": money["cross_source"].get("m2_yoy")}
            ],
            "diff_pct": money["cross_source"].get("diff_pct", 0),
            "verified": money.get("cross_verified", False)
        }
    for ind, key in [("CPI", "cpi"), ("PMI", "pmi"), ("GDP", "gdp")]:
        if key in data:
            verifications[ind] = {
                "sources": [{"name": "eastmoney"}],
                "diff_pct": 0,
                "verified": True,
                "note": "单源(东方财富)，待第二源交叉验证"
            }
    data["_verifications"] = verifications

    # ★ 错误聚合: 甩到 data 里，JSON输出和Markdown输出都能看到
    if errors:
        data["_errors"] = errors

    latency_ms = int((datetime.now() - t_start).total_seconds() * 1000)

    if not data or len(data) <= 2:  # only _verifications + _errors/us_macro
        err = _err(4, "所有数据源无数据", source="eastmoney+baostock", meta={"latency_ms": latency_ms, "errors": errors})
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 4

    if args.format == "markdown" or (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()):
        print(_format_markdown(data))
    else:
        result = _ok("eastmoney+baostock+chinamoney+worldbank", data,
                     meta={"latency_ms": latency_ms, "version": __version__, "errors": errors or None})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
