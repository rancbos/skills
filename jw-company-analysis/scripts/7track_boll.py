#!/usr/bin/env python3
"""
七轨布林线计算+可视化脚本
对接 jw-investment-data K线数据
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import argparse
import json
import sys
import os

# 添加 jw-investment-data scripts 路径
sys.path.insert(0, os.path.expanduser('~/.hermes/skills/jw-investment-data/scripts'))

def calc_7track_boll(df, n=20, k=5):
    """
    七轨布林线计算

    参数:
        df: DataFrame, 需含 'close' 列
        n: 均线周期，默认20
        k: 标准差平滑周期，默认5

    返回:
        df 新增7列: boll, top, track1, track2, track4, track5, bottom
    """
    mid = df['close'].rolling(n).mean()
    std0 = df['close'].rolling(n).std()
    dev = std0.rolling(k).mean()  # 标准差的移动平均，平滑波动

    df['boll'] = mid                    # 中轨：20日均线
    df['top'] = mid + 3 * dev           # 顶轨：+3σ
    df['track1'] = mid + 2 * dev        # 一轨：+2σ
    df['track2'] = mid + 1 * dev        # 二轨：+1σ
    df['track4'] = mid - 1 * dev        # 四轨：-1σ
    df['track5'] = mid - 2 * dev        # 五轨：-2σ
    df['bottom'] = mid - 3 * dev        # 底轨：-3σ

    return df

def get_current_track(row):
    """判断当前价格所在轨道"""
    price = row['close']
    if pd.isna(row['top']):
        return 'unknown'
    if price >= row['top']:
        return '顶轨 (极度超买)'
    elif price >= row['track1']:
        return '一轨 (超买)'
    elif price >= row['track2']:
        return '二轨 (偏强)'
    elif price >= row['boll']:
        return 'BOLL (中轨)'
    elif price >= row['track4']:
        return '四轨 (偏弱)'
    elif price >= row['track5']:
        return '五轨 (超卖)'
    else:
        return '底轨 (极度超卖)'

def plot_7track_boll(df, title="七轨布林线", save_path=None):
    """
    绘制七轨布林线图

    参数:
        df: DataFrame, 需含 close, boll, top, track1, track2, track4, track5, bottom 列
        title: 图表标题
        save_path: 保存路径，None则显示
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})

    # 绘制K线和布林轨道
    ax1.plot(df.index, df['close'], 'k-', linewidth=1, label='收盘价')
    ax1.plot(df.index, df['boll'], 'b-', linewidth=1.5, label='BOLL (中轨)')
    ax1.plot(df.index, df['top'], 'r--', linewidth=0.8, label='顶轨 (+3σ)')
    ax1.plot(df.index, df['track1'], 'r:', linewidth=0.8, label='一轨 (+2σ)')
    ax1.plot(df.index, df['track2'], 'orange', linewidth=0.8, label='二轨 (+1σ)')
    ax1.plot(df.index, df['track4'], 'green', linewidth=0.8, label='四轨 (-1σ)')
    ax1.plot(df.index, df['track5'], 'g:', linewidth=0.8, label='五轨 (-2σ)')
    ax1.plot(df.index, df['bottom'], 'g--', linewidth=0.8, label='底轨 (-3σ)')

    # 填充区域
    ax1.fill_between(df.index, df['top'], df['bottom'], alpha=0.1, color='blue')
    ax1.fill_between(df.index, df['track1'], df['track2'], alpha=0.1, color='orange')
    ax1.fill_between(df.index, df['track4'], df['track5'], alpha=0.1, color='green')

    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.set_ylabel('价格')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)

    # 绘制布林带宽度
    if 'top' in df.columns and 'bottom' in df.columns:
        width = (df['top'] - df['bottom']) / df['boll'] * 100
        ax2.plot(df.index, width, 'purple', linewidth=1, label='布林带宽度 (%)')
        ax2.set_ylabel('布林带宽度 (%)')
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    else:
        plt.show()

    plt.close()

def analyze_7track_boll(df):
    """
    分析七轨布林线状态

    参数:
        df: DataFrame, 需含 close, boll, top, track1, track2, track4, track5, bottom 列

    返回:
        dict: 分析结果
    """
    if df.empty:
        return {"error": "数据为空"}

    latest = df.iloc[-1]
    current_price = latest['close']
    current_track = get_current_track(latest)

    # 计算相对位置
    if pd.notna(latest['top']) and pd.notna(latest['bottom']):
        boll_range = latest['top'] - latest['bottom']
        if boll_range > 0:
            position_pct = (current_price - latest['bottom']) / boll_range * 100
        else:
            position_pct = 50
    else:
        position_pct = None

    # 计算布林带宽度
    if pd.notna(latest['boll']) and latest['boll'] > 0:
        boll_width = (latest['top'] - latest['bottom']) / latest['boll'] * 100
    else:
        boll_width = None

    # 判断信号
    signals = []
    if current_price >= latest['top']:
        signals.append("🔴 极度超买，坚决不追")
    elif current_price >= latest['track1']:
        signals.append("🟡 超买，考虑减仓")
    elif current_price >= latest['track2']:
        signals.append("⚪ 偏强，正常持有")
    elif current_price >= latest['boll']:
        signals.append("⚪ 中轨附近，正常波动")
    elif current_price >= latest['track4']:
        signals.append("⚪ 偏弱，关注支撑")
    elif current_price >= latest['track5']:
        signals.append("🟢 超卖，关注买入机会")
    else:
        signals.append("🟢🟢 极度超卖，可能是黄金坑")

    # 趋势判断
    if len(df) >= 5:
        recent_boll = df['boll'].iloc[-5:]
        if recent_boll.is_monotonic_increasing:
            signals.append("📈 中轨向上，趋势健康")
        elif recent_boll.is_monotonic_decreasing:
            signals.append("📉 中轨向下，趋势走弱")
        else:
            signals.append("➡️ 中轨震荡，方向不明")

    return {
        "current_price": round(current_price, 2),
        "current_track": current_track,
        "position_pct": round(position_pct, 2) if position_pct else None,
        "boll_mid": round(latest['boll'], 2) if pd.notna(latest['boll']) else None,
        "boll_width": round(boll_width, 2) if boll_width else None,
        "track_values": {
            "top": round(latest['top'], 2) if pd.notna(latest['top']) else None,
            "track1": round(latest['track1'], 2) if pd.notna(latest['track1']) else None,
            "track2": round(latest['track2'], 2) if pd.notna(latest['track2']) else None,
            "boll": round(latest['boll'], 2) if pd.notna(latest['boll']) else None,
            "track4": round(latest['track4'], 2) if pd.notna(latest['track4']) else None,
            "track5": round(latest['track5'], 2) if pd.notna(latest['track5']) else None,
            "bottom": round(latest['bottom'], 2) if pd.notna(latest['bottom']) else None
        },
        "signals": signals,
        "analysis_date": datetime.now().strftime("%Y-%m-%d")
    }

def main():
    parser = argparse.ArgumentParser(description='七轨布林线计算+可视化')
    parser.add_argument('--data', type=str, help='K线数据文件路径 (CSV或JSON)')
    parser.add_argument('--symbol', type=str, help='股票代码，从 jw-investment-data 获取数据')
    parser.add_argument('--market', type=str, default='A', help='市场类型: A/HK/US')
    parser.add_argument('--days', type=int, default=120, help='获取最近N天数据')
    parser.add_argument('--n', type=int, default=20, help='均线周期，默认20')
    parser.add_argument('--k', type=int, default=5, help='标准差平滑周期，默认5')
    parser.add_argument('--output', type=str, help='输出图片路径')
    parser.add_argument('--json', action='store_true', help='输出JSON格式分析结果')

    args = parser.parse_args()

    # 获取数据
    if args.data:
        # 从文件加载
        if args.data.endswith('.csv'):
            df = pd.read_csv(args.data)
        elif args.data.endswith('.json'):
            df = pd.read_json(args.data)
        else:
            print(f"不支持的文件格式: {args.data}")
            sys.exit(1)
    elif args.symbol:
        # 直接用 baostock 获取K线数据（自包含，不依赖 fetch_market_data）
        try:
            import baostock as bs
            import io, contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                bs.login()
            # 计算起始日期
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=args.days + 30)).strftime('%Y-%m-%d')
            # 构造代码
            code = f"sh.{args.symbol}" if args.market == 'A' and args.symbol.startswith('6') else f"sz.{args.symbol}"
            rs = bs.query_history_k_data_plus(
                code, "date,open,high,low,close,volume",
                start_date=start_date, end_date=end_date,
                frequency="d", adjustflag="2"
            )
            rows = []
            while (rs.error_code == '0') and rs.next():
                rows.append(rs.get_row_data())
            with contextlib.redirect_stdout(f):
                bs.logout()
            if not rows:
                print(f"baostock 未返回K线数据: {code}")
                sys.exit(1)
            df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df['close'] = df['close'].astype(float)
            df['date'] = pd.to_datetime(df['date'])
        except ImportError:
            print("baostock 未安装，请执行: pip install baostock")
            sys.exit(1)
        except Exception as e:
            print(f"获取数据失败: {e}")
            sys.exit(1)
    else:
        print("请指定 --data 或 --symbol")
        sys.exit(1)

    # 确保有 close 列
    if 'close' not in df.columns:
        print("数据缺少 close 列")
        sys.exit(1)

    # 计算七轨布林线
    df = calc_7track_boll(df, n=args.n, k=args.k)

    # 分析
    result = analyze_7track_boll(df)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n=== 七轨布林线分析 ===")
        print(f"当前价格: {result['current_price']}")
        print(f"当前轨道: {result['current_track']}")
        print(f"相对位置: {result['position_pct']}%")
        print(f"布林带宽度: {result['boll_width']}%")
        print("\n信号:")
        for signal in result['signals']:
            print(f"  {signal}")
        print("\n轨道值:")
        for track, value in result['track_values'].items():
            print(f"  {track}: {value}")

    # 绘图
    if not args.json:
        title = f"七轨布林线 - {args.symbol or '数据文件'}"
        plot_7track_boll(df, title=title, save_path=args.output)

if __name__ == '__main__':
    main()
