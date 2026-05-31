#!/usr/bin/env python3
"""
draw_kline.py — K线图生成器 v2.0
═══════════════════════════════════════════

v2.0 新特性:
  📦 标准信封 — 集成 output_contract.py
  ⏰ K线缓存 — 交易时段感知，避免重复拉取
  🔍 --schema — 自描述 + 当前市场状态

Baostock K线 + matplotlib 蜡烛图 + MA + 成交量 + MACD/RSI 副图

用法:
  python draw_kline.py --symbol 601318
  python draw_kline.py --symbol 601318 --days 90 --indicators macd,rsi
  python draw_kline.py --symbol 601318 --save /tmp/chart.png
  python draw_kline.py --symbol 601318 --force
  python draw_kline.py --schema

输出: PNG 文件路径 + 标准信封 JSON
"""

import argparse, json, os, sys, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

# ── 内部模块 ─────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))
from output_contract import envelope_ok, envelope_error
from market_clock import get_market_status, MarketCache

__version__ = "3.5.0"
CACHE = MarketCache()

# ═══════════════════════════════ 数据获取 ═══════════════════════════
def _fetch_kline(symbol: str, days: int, force: bool = False) -> Tuple[Optional[np.ndarray], list]:
    """Baostock → OHLCV numpy 数组（含缓存）"""

    market = get_market_status()
    cache_key = f"kline:{symbol}:{days}"

    if not force:
        cached = CACHE.get(cache_key, market["cache_ttl_minutes"])
        if cached and isinstance(cached.get("data"), list) and cached.get("dates"):
            arr = np.array(cached["data"])
            return arr[-days:], cached["dates"][-days:]

    import baostock as bs
    prefix = "sh." if symbol.startswith(("6", "9")) else "sz."
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")

    old = sys.stdout
    dn = open(os.devnull, 'w')
    try:
        sys.stdout = dn; bs.login(); sys.stdout = old
        rs = bs.query_history_k_data_plus(prefix + symbol,
            "date,open,high,low,close,volume",
            start_date=start, end_date=end, frequency="d", adjustflag="2")
        rows = []
        while rs.error_code == '0' and rs.next(): rows.append(rs.get_row_data())
        sys.stdout = dn; bs.logout(); sys.stdout = old
    finally:
        sys.stdout = old; dn.close()

    if not rows: return None, []

    dates = [r[0] for r in rows]
    raw = [[float(r[1] or 0), float(r[2] or 0), float(r[3] or 0),
             float(r[4] or 0), float(r[5] or 0)] for r in rows]
    arr = np.array(raw)

    CACHE.set(cache_key, {"data": raw, "dates": dates, "n_rows": len(rows)})
    return arr[-days:], dates[-days:]


# ═══════════════════════════════ 绘图 ═══════════════════════════════
def draw(data: np.ndarray, dates: list, symbol: str, name: str = "",
         indicators: list = None, save_path: str = None) -> str:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    indicators = indicators or []
    n_panels = 1 + len([i for i in indicators if i in ('macd', 'rsi')])
    height_ratios = [3] + [1.5] * (n_panels - 1)

    fig = plt.figure(figsize=(16, 4 + 2 * n_panels))
    fig.patch.set_facecolor('#1a1a2e')

    x_idx = np.arange(len(data))

    # ── 主图: K线 + MA ──
    ax1 = plt.subplot(n_panels, 1, 1)
    ax1.set_facecolor('#1a1a2e')

    width = 0.6
    for i in range(len(data)):
        o, h, l, c = data[i, 0], data[i, 1], data[i, 2], data[i, 3]
        color = '#ef5350' if c >= o else '#26a69a'
        ax1.plot([i, i], [l, h], color=color, linewidth=0.8)
        body_h = abs(c - o)
        body_bottom = min(c, o)
        rect = Rectangle((i - width/2, body_bottom), width, max(body_h, 0.01),
                         facecolor=color, edgecolor=color, linewidth=0.5)
        ax1.add_patch(rect)

    closes = data[:, 3]
    for p, style in [(5, '#ffeb3b'), (10, '#ff9800'), (20, '#e91e63'), (60, '#9c27b0')]:
        if len(closes) >= p:
            ma = np.convolve(closes, np.ones(p)/p, mode='valid')
            ax1.plot(x_idx[p-1:], ma, color=style, linewidth=1.0, alpha=0.8, label=f'MA{p}')

    title = f'{symbol} {name}' if name else symbol
    ax1.set_title(title, color='white', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8, facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')
    ax1.tick_params(colors='#999')
    ax1.grid(True, alpha=0.15, color='white')
    ax1.set_ylabel('Price', color='#999')

    # ── 成交量 ──
    ax_vol = ax1.twinx()
    colors_vol = ['#ef5350' if data[i,3] >= data[i,0] else '#26a69a' for i in range(len(data))]
    ax_vol.bar(x_idx, data[:,4] / 1e6, color=colors_vol, alpha=0.3, width=0.8)
    ax_vol.set_ylabel('Vol (M)', color='#999', fontsize=8)
    ax_vol.tick_params(colors='#999', labelsize=7)

    cp = 1

    if 'macd' in indicators:
        cp += 1
        ax = plt.subplot(n_panels, 1, cp, sharex=ax1)
        ax.set_facecolor('#1a1a2e')
        ema12 = _ema(closes, 12); ema26 = _ema(closes, 26)
        dif = ema12 - ema26; dea = _ema(dif, 9); bar = 2*(dif - dea)
        colors_bar = ['#ef5350' if b >= 0 else '#26a69a' for b in bar]
        ax.bar(x_idx, bar, color=colors_bar, alpha=0.7, width=0.8)
        ax.plot(x_idx, dif, color='white', linewidth=1.0, label='DIF')
        ax.plot(x_idx, dea, color='#ffeb3b', linewidth=1.0, label='DEA')
        ax.axhline(y=0, color='#666', linewidth=0.5)
        ax.legend(loc='upper left', fontsize=7, facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')
        ax.set_ylabel('MACD', color='#999', fontsize=8)
        ax.tick_params(colors='#999', labelsize=7)
        ax.grid(True, alpha=0.15, color='white')

    if 'rsi' in indicators:
        cp += 1
        ax = plt.subplot(n_panels, 1, cp, sharex=ax1)
        ax.set_facecolor('#1a1a2e')
        rsi_vals = _rsi_array(closes, 14)
        ax.plot(x_idx, rsi_vals, color='#00bcd4', linewidth=1.2, label='RSI(14)')
        ax.axhline(y=70, color='#ef5350', linewidth=0.8, linestyle='--', alpha=0.6)
        ax.axhline(y=30, color='#26a69a', linewidth=0.8, linestyle='--', alpha=0.6)
        ax.axhline(y=50, color='#666', linewidth=0.5)
        ax.fill_between(x_idx, rsi_vals, 50, where=(rsi_vals>=50), color='#ef5350', alpha=0.08)
        ax.fill_between(x_idx, rsi_vals, 50, where=(rsi_vals<50), color='#26a69a', alpha=0.08)
        ax.set_ylim(0, 100)
        ax.set_ylabel('RSI', color='#999', fontsize=8)
        ax.tick_params(colors='#999', labelsize=7)
        ax.grid(True, alpha=0.15, color='white')

    plt.tight_layout()
    path = save_path or f"/tmp/{symbol}_kline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(path, dpi=120, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    return path


# ═══════════════════════════════ 指标工具 ═══════════════════════════
def _ema(series: np.ndarray, period: int) -> np.ndarray:
    alpha = 2/(period+1)
    r = np.zeros_like(series); r[0] = series[0]
    for i in range(1, len(series)): r[i] = alpha*series[i] + (1-alpha)*r[i-1]
    return r

def _rsi_array(closes: np.ndarray, period: int = 14) -> np.ndarray:
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    rsi = np.full(len(closes), np.nan)
    if len(gains) <= period: return rsi
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    for i in range(period, len(gains)):
        avg_gain = (avg_gain*(period-1) + gains[i])/period
        avg_loss = (avg_loss*(period-1) + losses[i])/period
        rs = avg_gain/avg_loss if avg_loss else float('inf')
        rsi[i+1] = 100 - (100/(1+rs)) if rs != float('inf') else 100
    return rsi


# ═══════════════════════════════ schema ═══════════════════════════════
def _schema_json() -> str:
    mt = get_market_status()
    return json.dumps({
        "name": "draw_kline",
        "version": __version__,
        "description": "K线图生成 — Baostock + matplotlib，支持MA/成交量/MACD/RSI副图",
        "features": {"cache": "交易时段感知", "output": "标准信封 + PNG"},
        "current_market": {
            "state": mt["state"], "is_trading_day": mt["is_trading_day"],
            "beijing_time": mt["beijing_time"],
        },
        "exit_codes": {"0": "ok", "1": "runtime_error", "4": "no_data"},
        "examples": [
            "python draw_kline.py --symbol 601318",
            "python draw_kline.py --symbol 601318 --days 90 --indicators macd,rsi",
            "python draw_kline.py --symbol 601318 --force",
            "python draw_kline.py --schema",
        ],
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════ main ═══════════════════════════════
def main():
    t_start = datetime.now()
    p = argparse.ArgumentParser(f"draw_kline v{__version__}")
    p.add_argument("--symbol", help="A股代码")
    p.add_argument("--days", type=int, default=120, help="K线天数(默认120)")
    p.add_argument("--indicators", default="macd,rsi", help="副图指标: macd,rsi")
    p.add_argument("--save", help="保存路径(默认 /tmp/)")
    p.add_argument("--force", action="store_true", help="跳过缓存，强制重新拉取")
    p.add_argument("--schema", action="store_true")
    p.add_argument("--version", action="store_true")
    args = p.parse_args()

    if args.schema:
        print(_schema_json())
        return 0
    if args.version:
        print(f"draw_kline v3.5.0")
        return 0

    if not args.symbol:
        p.error("--symbol is required (unless --schema)")

    print(f"📊 获取 {args.symbol} K线数据...", file=sys.stderr)
    data, dates = _fetch_kline(args.symbol, args.days, force=args.force)
    if data is None or len(data) == 0:
        latency = int((datetime.now() - t_start).total_seconds() * 1000)
        err = envelope_error(4, f"{args.symbol} 无K线数据", source="baostock", retryable=True,
                            meta={"latency_ms": latency, "version": __version__})
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 4

    indicators = [i.strip().lower() for i in args.indicators.split(",") if i.strip()]
    path = draw(data, dates, args.symbol, indicators=indicators, save_path=args.save)

    latest = data[-1]
    prev = data[-2] if len(data) > 1 else latest
    chg = (latest[3] - prev[3]) / prev[3] * 100

    latency_ms = int((datetime.now() - t_start).total_seconds() * 1000)
    market = get_market_status()

    print(f"MEDIA:{path}")
    envelope = envelope_ok("baostock", {
        "symbol": args.symbol, "date": dates[-1],
        "close": round(float(latest[3]), 2),
        "change_pct": round(chg, 2),
        "volume": int(latest[4]), "n_days": len(data),
    }, meta={
        "latency_ms": latency_ms, "version": __version__,
        "image_path": path, "indicators": indicators,
        "market": {"state": market["state"], "is_trading_day": market["is_trading_day"]},
    })
    print(json.dumps(envelope, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.exit(main())
