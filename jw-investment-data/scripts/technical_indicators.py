#!/usr/bin/env python3
"""
technical_indicators.py — jw-investment-data 技术指标模块 v2.0
════════════════════════════════════════════════════════════════

v2.0 新特性:
  📦 标准信封 — 集成 output_contract.py {ok, source, data, meta}
  ⏰ 交易时钟 — 集成 market_clock.py 缓存 + 时间感知
  🔍 动态 schema — --schema 输出当前市场状态

计算 MA/MACD/RSI/Bollinger/ATR，基于 Baostock K线数据（无需 API Key）。
纯 numpy 实现，不依赖 stockstats/tushare。

用法:
  python technical_indicators.py --symbol 601318
  python technical_indicators.py --symbol 601318 --indicators macd,rsi,boll
  python technical_indicators.py --symbol 601318 --format markdown
  python technical_indicators.py --symbol 601318 --force
  python technical_indicators.py --schema

输出: 标准信封 {ok, source, data, meta} 或 Markdown
退出码: 0=ok  1=runtime  4=no_data
"""

import argparse, json, os, sys, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ── 内部模块 ─────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))
from output_contract import envelope_ok, envelope_error
from market_clock import get_market_status, MarketCache

# ═══════════════════════════════ 配置 ═══════════════════════════════
__version__ = "3.5.0"
DEFAULT_INDICATORS = ["sma", "macd", "rsi", "boll"]
LOOKBACK_DAYS = 200
RSI_PERIOD = 14
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
BOLL_PERIOD, BOLL_STD = 20, 2
ATR_PERIOD = 14
MA_PERIODS = [5, 10, 20, 60]

CACHE = MarketCache()

# ═══════════════════════════════ 数据获取 ═══════════════════════════
def _fetch_kline_baostock(symbol: str, lookback: int = LOOKBACK_DAYS,
                          force: bool = False) -> Tuple[Optional[np.ndarray], List[str]]:
    """Baostock 日K线 → numpy 数组 + 缓存"""

    market = get_market_status()
    cache_key = f"kline:{symbol}:{lookback}"

    if not force:
        cached = CACHE.get(cache_key, market["cache_ttl_minutes"])
        if cached and isinstance(cached.get("data"), list) and cached.get("dates"):
            arr = np.array(cached["data"])
            return arr, cached["dates"]

    import baostock as bs
    prefix = "sh." if symbol.startswith(("6", "9")) else "sz."
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback)).strftime("%Y-%m-%d")

    old_stdout = sys.stdout
    devnull = open(os.devnull, 'w')
    try:
        sys.stdout = devnull
        bs.login()
        sys.stdout = old_stdout
        rs = bs.query_history_k_data_plus(
            prefix + symbol,
            "date,open,high,low,close,volume",
            start_date=start, end_date=end,
            frequency="d", adjustflag="2")
        rows = []
        while rs.error_code == '0' and rs.next():
            rows.append(rs.get_row_data())
        sys.stdout = devnull
        bs.logout()
        sys.stdout = old_stdout
    finally:
        sys.stdout = old_stdout
        devnull.close()

    if not rows:
        return None, []

    dates = [r[0] for r in rows]
    raw_data = [[float(r[1] or 0), float(r[2] or 0), float(r[3] or 0),
                  float(r[4] or 0), float(r[5] or 0)] for r in rows]
    arr = np.array(raw_data)

    CACHE.set(cache_key, {"data": raw_data, "dates": dates, "n_rows": len(rows)})
    return arr, dates


# ═══════════════════════════════ 指标计算 ═══════════════════════════
def _sma(data: np.ndarray) -> Dict:
    closes = data[:, 3]
    result = {}
    for p in MA_PERIODS:
        ma = np.convolve(closes, np.ones(p)/p, mode='valid')
        if len(ma) > 0:
            result[f"MA{p}"] = round(float(ma[-1]), 2)
    if len(closes) >= 20:
        ma5_full = np.convolve(closes, np.ones(5)/5, mode='valid')
        ma20_full = np.convolve(closes, np.ones(20)/20, mode='valid')
        min_len = min(len(ma5_full), len(ma20_full))
        ma5_a, ma20_a = ma5_full[-min_len:], ma20_full[-min_len:]
        if len(ma5_a) >= 2:
            if ma5_a[-2] <= ma20_a[-2] and ma5_a[-1] > ma20_a[-1]:
                result["signal"] = "🟢 MA5金叉MA20"
            elif ma5_a[-2] >= ma20_a[-2] and ma5_a[-1] < ma20_a[-1]:
                result["signal"] = "🔴 MA5死叉MA20"
            elif ma5_a[-1] > ma20_a[-1]:
                result["signal"] = "📈 MA5 > MA20（多头）"
            else:
                result["signal"] = "📉 MA5 < MA20（空头）"
    return result

def _ema(series: np.ndarray, period: int) -> np.ndarray:
    alpha = 2 / (period + 1)
    result = np.zeros_like(series)
    result[0] = series[0]
    for i in range(1, len(series)):
        result[i] = alpha * series[i] + (1 - alpha) * result[i-1]
    return result

def _macd(data: np.ndarray) -> Dict:
    closes = data[:, 3]
    ema12 = _ema(closes, MACD_FAST)
    ema26 = _ema(closes, MACD_SLOW)
    dif = ema12 - ema26
    dea = _ema(dif, MACD_SIGNAL)
    macd_bar = 2 * (dif - dea)
    result = {"DIF": round(float(dif[-1]), 4), "DEA": round(float(dea[-1]), 4),
              "MACD": round(float(macd_bar[-1]), 4)}
    if len(dif) >= 2 and len(dea) >= 2:
        if dif[-2] <= dea[-2] and dif[-1] > dea[-1]:
            result["signal"] = "🟢 MACD金叉"
        elif dif[-2] >= dea[-2] and dif[-1] < dea[-1]:
            result["signal"] = "🔴 MACD死叉"
        elif dif[-1] > dea[-1]:
            result["signal"] = "📈 DIF > DEA（多头）"
        else:
            result["signal"] = "📉 DIF < DEA（空头）"
    return result

def _rsi(data: np.ndarray, period: int = RSI_PERIOD) -> Dict:
    closes = data[:, 3]
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
    rsi_val = 100 - (100 / (1 + rs)) if rs != float('inf') else 100
    result = {"RSI": round(rsi_val, 2)}
    if rsi_val < 30: result["signal"] = "🔵 RSI 超卖 (<30)"
    elif rsi_val > 70: result["signal"] = "🔴 RSI 超买 (>70)"
    elif rsi_val > 50: result["signal"] = "📈 RSI 偏强"
    else: result["signal"] = "📉 RSI 偏弱"
    return result

def _boll(data: np.ndarray) -> Dict:
    closes = data[:, 3]
    if len(closes) < BOLL_PERIOD:
        return {"error": f"数据不足{BOLL_PERIOD}天"}
    middle = np.convolve(closes, np.ones(BOLL_PERIOD)/BOLL_PERIOD, mode='valid')
    rolling_std = np.array([np.std(closes[i-BOLL_PERIOD+1:i+1]) for i in range(BOLL_PERIOD-1, len(closes))])
    upper = middle + BOLL_STD * rolling_std
    lower = middle - BOLL_STD * rolling_std
    bandwidth = (upper - lower) / middle * 100
    last_close = closes[-1]
    result = {"upper": round(float(upper[-1]), 2), "middle": round(float(middle[-1]), 2),
              "lower": round(float(lower[-1]), 2), "bandwidth_pct": round(float(bandwidth[-1]), 2)}
    if last_close > upper[-1]: result["signal"] = "🔴 收盘突破上轨"
    elif last_close < lower[-1]: result["signal"] = "🔵 收盘跌破下轨"
    elif bandwidth[-1] < 5: result["signal"] = "⏳ 布林带收窄（可能变盘）"
    else: result["signal"] = "─ 在布林带内运行"
    return result

def _atr(data: np.ndarray) -> Dict:
    high, low, close = data[:, 1], data[:, 2], data[:, 3]
    prev_close = np.roll(close, 1); prev_close[0] = close[0]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    atr = np.convolve(tr, np.ones(ATR_PERIOD)/ATR_PERIOD, mode='valid')
    return {"ATR": round(float(atr[-1]), 2)} if len(atr) > 0 else {"error": "无ATR数据"}

INDICATOR_FUNCS = {"sma": _sma, "macd": _macd, "rsi": _rsi, "boll": _boll, "atr": _atr}

def compute_all(data: np.ndarray, indicators: List[str]) -> Dict:
    results = {}
    for ind in indicators:
        fn = INDICATOR_FUNCS.get(ind)
        if fn:
            try: results[ind] = fn(data)
            except Exception as e: results[ind] = {"error": str(e)}
        else: results[ind] = {"error": f"未知指标: {ind}"}
    return results


# ═══════════════════════════════ 格式化 ═══════════════════════════════
def _format_markdown(symbol: str, indicators: Dict, n_rows: int, latency_ms: int,
                     market_state: str, dates: list) -> str:
    """Markdown 人读输出 + 标准化来源块"""
    lines = [f"## 📈 技术指标 — {symbol}", ""]
    mt = get_market_status()

    # 摘要
    lines.append("> " + " | ".join([
        f"K线条数: {n_rows}",
        f"日历范围: {dates[0]}~{dates[-1]}" if dates else "",
        f"🕐 {latency_ms}ms",
        f"🔧 市场: {mt['state']}",
    ]))
    lines.append("")

    ind_names = {"sma": "均线系统", "macd": "MACD", "rsi": "RSI", "boll": "布林带", "atr": "ATR"}
    for name, data in indicators.items():
        label = ind_names.get(name, name)
        if isinstance(data, dict) and "error" not in data:
            lines.append(f"### {label}")
            lines.append("| 指标 | 数值 | 信号 |")
            lines.append("|------|------|------|")
            signal = data.pop("signal", "─")
            keys = list(data.keys())
            for i, (k, v) in enumerate(data.items()):
                sig = f"🔔 {signal}" if i == 0 else ""
                lines.append(f"| {k} | {v} | {sig} |")
            lines.append("")

    # ── 标准化数据来源标注块 ──────────────────────────────
    lines.append("---")
    lines.append("📊 **数据来源**: Baostock (证券宝) — A股EOD行情")
    lines.append(f"⏱️ **数据时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CST")
    lines.append(f"📡 **市场状态**: {mt['state']} | 交易日: {'是' if mt['is_trading_day'] else '否'}")
    lines.append("🔧 **分析工具**: jw-investment-data v" + VERSION)
    lines.append("⚠️ *技术指标仅供参考，不构成投资建议*")
    return "\n".join(lines)


# ═══════════════════════════════ schema ═══════════════════════════════
def _schema_json() -> str:
    mt = get_market_status()
    return json.dumps({
        "name": "technical_indicators",
        "version": __version__,
        "description": "技术指标计算 — Baostock K线 + numpy，无需API Key",
        "features": {"cache": "交易时段感知（盘中5min/盘后24h）", "output": "标准信封 {ok, source, data, meta}"},
        "indicators": {
            "sma": "MA5/MA10/MA20/MA60 + 金叉/死叉信号",
            "macd": "MACD(12,26,9) + DIF/DEA/柱 + 金叉/死叉",
            "rsi": f"RSI({RSI_PERIOD}) + 超卖(<30)/超买(>70)",
            "boll": f"BOLL({BOLL_PERIOD},{BOLL_STD}) + 上/中/下轨 + 突破信号",
            "atr": f"ATR({ATR_PERIOD}) — 平均真实波幅",
        },
        "current_market": {
            "state": mt["state"], "is_trading_day": mt["is_trading_day"],
            "cache_ttl_minutes": mt["cache_ttl_minutes"], "beijing_time": mt["beijing_time"],
        },
        "exit_codes": {"0": "ok", "1": "runtime_error", "4": "no_data"},
        "examples": [
            "python technical_indicators.py --symbol 601318",
            "python technical_indicators.py --symbol 601318 --indicators macd,rsi,boll --format markdown",
            "python technical_indicators.py --symbol 601318 --force",
            "python technical_indicators.py --schema",
        ],
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════ main ═══════════════════════════════
def main():
    t_start = datetime.now()
    p = argparse.ArgumentParser(f"technical_indicators v{__version__}")
    p.add_argument("--symbol", help="A股代码，如 601318")
    p.add_argument("--indicators", default=",".join(DEFAULT_INDICATORS),
                   help=f"逗号分隔指标: {','.join(INDICATOR_FUNCS)}")
    p.add_argument("--lookback", type=int, default=LOOKBACK_DAYS, help=f"回溯天数(默认{LOOKBACK_DAYS})")
    p.add_argument("--format", default="json", choices=["json", "markdown"])
    p.add_argument("--force", action="store_true", help="跳过缓存，强制重新拉取")
    p.add_argument("--schema", action="store_true")
    p.add_argument("--version", action="store_true")
    args = p.parse_args()

    if args.schema:
        print(_schema_json())
        return 0
    if args.version:
        print(f"technical_indicators v3.5.0")
        return 0

    if not args.symbol:
        p.error("--symbol is required (unless --schema)")

    indicators = [s.strip().lower() for s in args.indicators.split(",") if s.strip()]

    data, dates = _fetch_kline_baostock(args.symbol, args.lookback, force=args.force)
    if data is None or len(data) == 0:
        latency = int((datetime.now() - t_start).total_seconds() * 1000)
        err = envelope_error(4, f"{args.symbol} 无K线数据", source="baostock", retryable=True,
                            meta={"latency_ms": latency, "version": __version__})
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 4

    results = compute_all(data, indicators)
    latency_ms = int((datetime.now() - t_start).total_seconds() * 1000)
    market = get_market_status()

    if args.format == "markdown" or (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()):
        print(_format_markdown(args.symbol, results, len(data), latency_ms, market["state"], dates))
    else:
        envelope = envelope_ok("baostock", {
            "symbol": args.symbol, "n_rows": len(data),
            "date_range": [dates[0], dates[-1]] if dates else [],
            "indicators": results,
        }, meta={"latency_ms": latency_ms, "version": __version__,
                "market": {"state": market["state"], "is_trading_day": market["is_trading_day"]}})
        print(json.dumps(envelope, ensure_ascii=False, indent=2))

    return 0

if __name__ == "__main__":
    sys.exit(main())
