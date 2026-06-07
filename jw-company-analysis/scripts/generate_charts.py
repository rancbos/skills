#!/usr/bin/env python3
"""
图表自动生成脚本 v1.0
根据输入数据自动生成ASCII图表，用于报告输出

用法：
  python3 generate_charts.py --type financial --data '{"revenue": 100, "profit": 20, "margin": 25}'
  python3 generate_charts.py --type valuation --data '{"conservative": 23.5, "neutral": 33.2, "optimistic": 42.4, "current": 29.45}'
  python3 generate_charts.py --type technical --data '{"boll_position": 31.43, "rsi": 27.44, "macd": "bearish", "ma": "bearish"}'
  python3 generate_charts.py --type consensus --data '{"buy": 8, "hold": 2, "sell": 0, "target_prices": [35, 40, 43, 45, 48]}'

输出：ASCII图表字符串，可直接嵌入报告
"""

import argparse
import json
import sys
from typing import Dict, List, Any


def generate_financial_dashboard(data: Dict) -> str:
    """生成关键财务指标仪表盘"""
    revenue = data.get("revenue", 0)
    profit = data.get("profit", 0)
    margin = data.get("margin", 0)
    roe = data.get("roe", 0)
    
    # 格式化数值
    revenue_str = f"{revenue}亿" if revenue >= 1 else f"{revenue*10000:.0f}万"
    profit_str = f"{profit}亿" if profit >= 1 else f"{profit*10000:.0f}万"
    margin_str = f"{margin:.1f}%"
    roe_str = f"{roe:.1f}%"
    
    # 判断状态（根据行业基准）
    def get_status(value, low=10, high=20):
        if value >= high:
            return "🟢"
        elif value >= low:
            return "🟡"
        else:
            return "🔴"
    
    revenue_status = get_status(revenue, 50, 100)
    profit_status = get_status(profit, 10, 30)
    margin_status = get_status(margin, 15, 30)
    roe_status = get_status(roe, 10, 20)
    
    chart = f"""
┌─────────────────────────────────────────────────────────────────┐
│                    关键财务指标一览                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   营业收入        净利润          毛利率          ROE            │
│   ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐        │
│   │{revenue_str:^5}│        │{profit_str:^5}│        │{margin_str:^5}│        │{roe_str:^5}│        │
│   └─────┘        └─────┘        └─────┘        └─────┘        │
│   {revenue_status}              {profit_status}              {margin_status}              {roe_status}              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘"""
    return chart


def generate_valuation_chart(data: Dict) -> str:
    """生成估值区间图"""
    conservative = data.get("conservative", 0)
    neutral = data.get("neutral", 0)
    optimistic = data.get("optimistic", 0)
    current = data.get("current", 0)
    
    # 计算刻度
    min_val = min(conservative, current) * 0.9
    max_val = max(optimistic, current) * 1.1
    range_val = max_val - min_val
    
    # 归一化到20字符宽度
    def normalize(val):
        return int((val - min_val) / range_val * 20)
    
    cons_pos = normalize(conservative)
    neut_pos = normalize(neutral)
    opt_pos = normalize(optimistic)
    curr_pos = normalize(current)
    
    # 构建图表
    lines = []
    lines.append(f"股价（元）")
    lines.append(f"    ↑")
    
    for y in range(4, 0, -1):
        line = "    │"
        for x in range(21):
            if x == cons_pos and y == 2:
                line += "┌───┐"
            elif x == neut_pos and y == 3:
                line += "┌───┐"
            elif x == opt_pos and y == 4:
                line += "┌───┐"
            elif x == curr_pos and y == 1:
                line += "─ ─ ─"
            else:
                line += "     "
        lines.append(line)
    
    lines.append(f"    └{'─' * 105}→")
    lines.append(f"       {conservative:.1f}元      {neutral:.1f}元      {optimistic:.1f}元      当前价 {current:.2f}元")
    
    return "\n".join(lines)


def generate_technical_dashboard(data: Dict) -> str:
    """生成技术信号综合评估仪表盘"""
    boll_position = data.get("boll_position", 50)
    rsi = data.get("rsi", 50)
    macd = data.get("macd", "neutral")
    ma = data.get("ma", "neutral")
    
    # 判断布林带位置
    if boll_position < 20:
        boll_label = "超卖"
        boll_signal = "🟢"
    elif boll_position < 40:
        boll_label = "偏弱"
        boll_signal = "🟡"
    elif boll_position < 60:
        boll_label = "中性"
        boll_signal = "🟡"
    elif boll_position < 80:
        boll_label = "偏强"
        boll_signal = "🟡"
    else:
        boll_label = "超买"
        boll_signal = "🔴"
    
    # 判断RSI
    if rsi < 30:
        rsi_label = "超卖"
        rsi_signal = "🟢"
    elif rsi < 50:
        rsi_label = "偏弱"
        rsi_signal = "🟡"
    elif rsi < 70:
        rsi_label = "中性"
        rsi_signal = "🟡"
    else:
        rsi_label = "超买"
        rsi_signal = "🔴"
    
    # 判断MACD
    macd_labels = {
        "bullish": "金叉",
        "bearish": "死叉",
        "neutral": "中性"
    }
    macd_label = macd_labels.get(macd, "中性")
    macd_signal = "🟢" if macd == "bullish" else "🔴" if macd == "bearish" else "🟡"
    
    # 判断均线
    ma_labels = {
        "bullish": "多头",
        "bearish": "空头",
        "neutral": "纠缠"
    }
    ma_label = ma_labels.get(ma, "纠缠")
    ma_signal = "🟢" if ma == "bullish" else "🔴" if ma == "bearish" else "🟡"
    
    # 综合信号
    bullish_count = sum(1 for s in [boll_signal, rsi_signal, macd_signal, ma_signal] if s == "🟢")
    bearish_count = sum(1 for s in [boll_signal, rsi_signal, macd_signal, ma_signal] if s == "🔴")
    
    if bullish_count >= 3:
        overall = "看多"
        overall_strength = "强"
    elif bullish_count >= 2:
        overall = "看多"
        overall_strength = "中"
    elif bearish_count >= 3:
        overall = "看空"
        overall_strength = "强"
    elif bearish_count >= 2:
        overall = "看空"
        overall_strength = "中"
    else:
        overall = "中性"
        overall_strength = "弱"
    
    chart = f"""
┌─────────────────────────────────────────────────────────────────┐
│                    技术信号综合评估                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   七轨布林线      RSI           MACD           均线              │
│   ┌─────┐        ┌─────┐        ┌─────┐        ┌─────┐        │
│   │{boll_position:.0f}%  │        │{rsi:.1f}│        │{macd_label:^4}  │        │{ma_label:^4}  │        │
│   │{boll_label:^4}  │        │{rsi_label:^4}  │        │     │        │     │        │
│   └─────┘        └─────┘        └─────┘        └─────┘        │
│   {boll_signal}              {rsi_signal}              {macd_signal}              {ma_signal}              │
│                                                                 │
│   综合信号：{overall}（技术{overall_strength}）                                 │
│   信号强度：{overall_strength}                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘"""
    return chart


def generate_consensus_chart(data: Dict) -> str:
    """生成一致预期分布图"""
    buy = data.get("buy", 0)
    hold = data.get("hold", 0)
    sell = data.get("sell", 0)
    target_prices = data.get("target_prices", [])
    
    total = buy + hold + sell
    if total == 0:
        return "无评级数据"
    
    # 计算百分比
    buy_pct = buy / total * 100
    hold_pct = hold / total * 100
    sell_pct = sell / total * 100
    
    # 构建评级分布图
    buy_bars = "█" * int(buy_pct / 5)
    hold_bars = "█" * int(hold_pct / 5)
    sell_bars = "█" * int(sell_pct / 5)
    
    # 目标价分布
    if target_prices:
        min_price = min(target_prices)
        max_price = max(target_prices)
        median_price = sorted(target_prices)[len(target_prices) // 2]
        avg_price = sum(target_prices) / len(target_prices)
    else:
        min_price = max_price = median_price = avg_price = 0
    
    chart = f"""
评级分布图

买入  {buy_bars} {buy_pct:.0f}% ({buy}家)
增持  {hold_bars} {hold_pct:.0f}% ({hold}家)
中性  {sell_bars} {sell_pct:.0f}% ({sell}家)

一致预期：{"买入/增持（正面）" if buy + hold > sell else "中性/减持（负面）"}

目标价分布（元）：
  最低：{min_price:.1f}元
  中位：{median_price:.1f}元
  均值：{avg_price:.1f}元
  最高：{max_price:.1f}元
  样本：{len(target_prices)}家"""
    return chart


def generate_cycle_dashboard(data: Dict) -> str:
    """生成周期定位仪表盘"""
    cycle = data.get("cycle", "复苏")
    interest_rate = data.get("interest_rate", "中性")
    inflation = data.get("inflation", "温和")
    liquidity = data.get("liquidity", "适度")
    
    # 判断状态
    cycle_status = "🟢" if cycle in ["复苏", "繁荣"] else "🔴" if cycle in ["衰退", "萧条"] else "🟡"
    rate_status = "🟢" if interest_rate == "宽松" else "🔴" if interest_rate == "紧缩" else "🟡"
    inflation_status = "🟢" if inflation == "温和" else "🔴" if inflation == "高" else "🟡"
    liquidity_status = "🟢" if liquidity == "充裕" else "🔴" if liquidity == "紧张" else "🟡"
    
    chart = f"""
┌─────────────────────────────────────────────────────────────────┐
│                    宏观周期定位仪表盘                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   经济周期          利率环境          通胀水平          流动性    │
│   ┌─────┐          ┌─────┐          ┌─────┐          ┌─────┐  │
│   │     │          │     │          │     │          │     │  │
│   │  ●  │          │  ●  │          │  ●  │          │  ●  │  │
│   │{cycle:^4}  │          │{interest_rate:^4}  │          │{inflation:^4}  │          │{liquidity:^4}  │  │
│   │     │          │     │          │     │          │     │  │
│   └─────┘          └─────┘          └─────┘          └─────┘  │
│   {cycle_status}              {rate_status}              {inflation_status}              {liquidity_status}              │
│                                                                 │
│   周期阶段判断：{cycle}期                                            │
│   对公司影响：{"利好" if cycle_status == "🟢" else "利空" if cycle_status == "🔴" else "中性"} + 经济{cycle}带动需求{"回升" if cycle_status == "🟢" else "下降"}                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘"""
    return chart


def main():
    parser = argparse.ArgumentParser(description="图表自动生成")
    parser.add_argument("--type", required=True, 
                       choices=["financial", "valuation", "technical", "consensus", "cycle"],
                       help="图表类型")
    parser.add_argument("--data", required=True, help="JSON格式数据")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"错误：JSON解析失败 - {e}", file=sys.stderr)
        sys.exit(1)
    
    # 根据类型生成图表
    generators = {
        "financial": generate_financial_dashboard,
        "valuation": generate_valuation_chart,
        "technical": generate_technical_dashboard,
        "consensus": generate_consensus_chart,
        "cycle": generate_cycle_dashboard
    }
    
    generator = generators.get(args.type)
    if not generator:
        print(f"错误：不支持的图表类型 - {args.type}", file=sys.stderr)
        sys.exit(1)
    
    chart = generator(data)
    
    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(chart)
        print(f"图表已保存到：{args.output}")
    else:
        print(chart)


if __name__ == "__main__":
    main()

