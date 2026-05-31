#!/usr/bin/env python3
"""
format_macro.py — 宏观数据 Markdown 格式化器 v1.0
═════════════════════════════════════════════════

从 fetch_macro.py 独立出来的展示层。数据采集和展示分离。

用法:
  from format_macro import format_macro
  print(format_macro(data, version="3.4.1"))
"""

from datetime import datetime
from typing import Dict


def format_macro(data: Dict, version: str = "3.4.1") -> str:
    """将宏观数据 dict 渲染为 Markdown 全景报告。"""

    lines = ["# 📊 宏观数据全景", ""]

    # ── 经济增长 ──
    gdp = data.get("gdp")
    pmi = data.get("pmi")
    if gdp or pmi:
        lines.append("## 📈 经济增长")
        lines.append("")
        if gdp:
            lines.append(f"| GDP ({gdp['period']}) | 数值 | 同比 |")
            lines.append(f"|------|------|------|")
            lines.append(f"| 国内生产总值 | {gdp['gdp_amount']:,.0f}亿 | **{gdp['gdp_yoy']:+.1f}%** |")
            lines.append(f"| 第一产业 | — | {gdp['primary_yoy']:+.1f}% |")
            lines.append(f"| 第二产业 | — | {gdp['secondary_yoy']:+.1f}% |")
            lines.append(f"| 第三产业 | — | {gdp['tertiary_yoy']:+.1f}% |")
            if gdp.get("prev_yoy"):
                lines.append(f"| 上期同比 | — | {gdp['prev_yoy']:+.1f}% |")
            lines.append("")
        if pmi:
            mfg = pmi["manufacturing"]
            nmfg = pmi["non_manufacturing"]
            m_trend = "🟢扩张" if mfg and mfg >= 50 else "🔴收缩" if mfg else "?"
            n_trend = "🟢扩张" if nmfg and nmfg >= 50 else "🔴收缩" if nmfg else "?"
            lines.append(f"| PMI ({pmi['period']}) | 数值 | 趋势 | 前值 |")
            lines.append(f"|------|------|------|------|")
            lines.append(f"| 制造业 | **{mfg}** | {m_trend} | {pmi.get('prev_manufacturing','?')} |")
            lines.append(f"| 非制造业 | **{nmfg}** | {n_trend} | {pmi.get('prev_non_manufacturing','?')} |")
            lines.append("")

    # ── 通胀 ──
    cpi = data.get("cpi")
    ppi = data.get("ppi")
    if cpi or ppi:
        lines.append("## 🔥 通胀")
        lines.append("")
        if cpi:
            lines.append(f"| CPI ({cpi['period']}) | 同比 | 环比 | 前值 |")
            lines.append(f"|------|------|------|------|")
            lines.append(f"| 全国 | **{cpi['cpi_yoy']:+.1f}%** | {cpi.get('cpi_mom', 0):+.1f}% | {cpi.get('prev_yoy',0):+.1f}% |")
            lines.append("")
        if ppi:
            lines.append(f"| PPI ({ppi['period']}) | 同比 | 前值 |")
            lines.append(f"|------|------|------|")
            lines.append(f"| 全部工业品 | **{ppi['ppi_yoy']:+.1f}%** | {ppi.get('prev_yoy','?'):+.1f}% |")
            lines.append("")

    # ── 货币 ──
    money = data.get("money")
    if money and money.get("m2"):
        lines.append("## 🏦 货币供应")
        lines.append(f"> {money['period']} | 来源: Baostock")
        m2_yoy = money["m2_yoy"]
        trend = "📈 宽松" if m2_yoy > 9 else "📉 收紧" if m2_yoy < 7 else "─ 中性"
        cross = money.get("cross_source")
        if cross:
            cross_icon = "✅" if money.get("cross_verified") else "⚠️"
            lines.append(f"> 🔍 交叉验证: 东方财富 M2={cross['m2_yoy']:+.1f}% "
                         f"(差异{cross.get('diff_pct',0):.1f}%) {cross_icon}")
        lines.append("")
        lines.append(f"| 指标 | 数值 | 同比 | 趋势 |")
        lines.append(f"|------|------|------|------|")
        lines.append(f"| M2 | {money['m2']/10000:.1f}万亿 | **{m2_yoy:+.1f}%** | {trend} |")
        lines.append(f"| M1 | {money['m1']/10000:.1f}万亿 | {money['m1_yoy']:+.1f}% | |")
        lines.append(f"| M0 | {money['m0']:.1f}亿 | {money['m0_yoy']:+.1f}% | |")
        if money.get("time_series"):
            lines.append("")
            lines.append("| 近6月M2趋势 | M2(万亿) | 同比 |")
            lines.append("|------|------|------|")
            for ts in money["time_series"]:
                lines.append(f"| {ts['period']} | {ts['m2']/10000:.1f} | {ts['m2_yoy']:+.1f}% |")
        lines.append("")

    # ── 利率 ──
    lpr = data.get("lpr")
    rates = data.get("rates")
    if lpr or rates:
        lines.append("## 💰 利率环境")
        lines.append("")
        if lpr:
            lines.append(f"| LPR ({lpr.get('date','')}) | 1年期 | 5年期 |")
            lines.append(f"|------|------|------|")
            lines.append(f"| 最新 | **{lpr['lpr_1y']}%** | **{lpr['lpr_5y']}%** |")
            if lpr.get("prev_1y"):
                lines.append(f"| 前值 | {lpr['prev_1y']}% | {lpr['prev_5y']}% |")
            lines.append("")
        if rates and rates.get("deposit_rate"):
            dr = rates["deposit_rate"]
            lines.append(f"| 存款利率 | 活期 | 3个月 | 6个月 | 1年 |")
            lines.append(f"|------|------|------|------|------|")
            lines.append(f"| | {dr.get('demand','?')}% | {dr.get('fix_3m','?')}% | {dr.get('fix_6m','?')}% | {dr.get('fix_1y','?')}% |")
            lines.append("")
        if rates and rates.get("loan_rate"):
            lr = rates["loan_rate"]
            lines.append(f"| 贷款利率 | 6个月内 | 1年 | 5年以上 |")
            lines.append(f"|------|------|------|------|")
            lines.append(f"| | {lr.get('lt_6m','?')}% | {lr.get('lt_1y','?')}% | {lr.get('gt_5y','?')}% |")
            lines.append("")

    # ── 准备金率 ──
    rrr = data.get("reserve_ratio")
    if rrr:
        lines.append("## 🏛️ 存款准备金率")
        lines.append(f"> {rrr.get('date','')} | 大型 {rrr.get('large_bank','?')}% | 中小型 {rrr.get('small_bank','?')}%")
        lines.append("")

    # ── 日历 ──
    cal = data.get("calendar", {})
    if cal:
        lines.append("## 📅 近期关注")
        lines.append(f"> {cal.get('hint','')}")
        lines.append(f"> 筛选: {cal.get('filter_cn','')}")
        lines.append(f"> {cal.get('note','')}")
        lines.append("")

    # ── 世界银行背景 ──
    wb = data.get("worldbank")
    if wb:
        lines.append("## 🌍 全球背景 (世界银行)")
        lines.append(f"> 年度数据，最新为2024年")
        lines.append("")
        if wb.get("us_gdp_trillion"):
            lines.append(f"| 指标 | 美国 | 中国 |")
            lines.append(f"|------|------|------|")
            lines.append(f"| GDP | **${wb['us_gdp_trillion']}万亿** | **${wb['cn_gdp_trillion']}万亿** |")
            lines.append(f"| CPI | {wb.get('us_cpi_pct','?')}% | — |")
            lines.append("")

    # ── 美国宏观提示 ──
    us = data.get("us_macro", {})
    if us:
        lines.append("## 🇺🇸 美国宏观 (Jin10 快讯)")
        lines.append(f"> {us.get('hint','')}")
        lines.append(f"> 建议搜索词: {', '.join(us.get('search_keywords', []))}")
        lines.append("")

    # ── 验证状态 ──
    verifications = data.get("_verifications", {})
    if verifications:
        lines.append("## 🔍 交叉验证状态")
        lines.append("| 指标 | 数据源 | 差异 | 状态 | 备注 |")
        lines.append("|------|------|------|:--:|------|")
        for ind, v in verifications.items():
            sources = ", ".join(s["name"] for s in v.get("sources", []))
            disc = v.get("diff_pct", v.get("discrepancy_pct", 0))
            ok = "✅" if v.get("verified") else "⚠️"
            note = v.get("note", "")
            lines.append(f"| {ind} | {sources} | {disc}% | {ok} | {note} |")
        lines.append("")

    # ── 错误聚合 ──
    errors_list = data.get("_errors", [])
    if errors_list:
        lines.append("## ⚠️ 数据获取错误")
        for e in errors_list:
            lines.append(f"- **{e['source']}**: {e['message']}")
        lines.append("")

    # ── 脚注 ──
    lines.append("---")
    lines.append("📊 **数据来源**: 东方财富 API + Baostock + 中国货币网 + 世界银行")
    lines.append(f"⏱️ **数据时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CST")
    lines.append(f"🔧 **分析工具**: jw-investment-data v{version}")
    lines.append("⚠️ 宏观数据仅供参考，不构成投资建议")
    return "\n".join(lines)
