#!/usr/bin/env python3
"""
format_market.py — A股行情 Markdown 格式化器 v1.0
═══════════════════════════════════════════════════

从 fetch_market_data.py 独立出来的展示层。

用法:
  from format_market import format_market
  print(format_market(output_dict))
"""

from typing import Dict


def format_market(out: Dict) -> str:
    """将 JSON 输出渲染为人类可读的 Markdown。"""
    q = out.get("query", {})
    v = out.get("verification", {})
    d = out.get("data", {})
    results = d.get("results", {})
    errors = d.get("errors", [])

    conf_icon = {"high": "🟢", "medium": "🟡", "acceptable": "🔵", "low": "🔴"}.get(v.get("confidence", ""), "❓")
    lines = []

    # 标题行
    name = ""
    for eng_data in results.values():
        if isinstance(eng_data, dict) and eng_data.get("name"):
            name = f"（{eng_data['name']}）"
            break
    lines.append(f"## 📊 {q.get('symbol','?')}{name}")
    lines.append("")

    # 校验摘要
    lines.append(f"```")
    lines.append(f"{conf_icon} {v.get('status','N/A')}  |  置信度: {v.get('confidence','?')}  |  采纳价: ¥{v.get('adopted_value','?')}")
    lines.append(f"```")
    lines.append("")

    # 各引擎明细
    engine_names = {"tencent": "腾讯 HTTP", "sina": "新浪 HTTPS", "baostock": "Baostock EOD",
                    "akshare": "AkShare 1.18", "yfinance": "yfinance", "efinance": "efinance",
                    "baidu": "百度股市通", "tushare": "Tushare", "xueqiu": "雪球"}
    for eng, edata in results.items():
        if isinstance(edata, dict):
            label = engine_names.get(eng, eng)
            p = edata.get("price", "?")
            pct = edata.get("change_pct")
            dt = edata.get("date", "")
            extra = f"  {pct:+.2f}%" if pct is not None else ""
            extra += f"  ({dt})" if dt else ""
            lines.append(f"| {label:<14} | ¥ {str(p):>10} {extra} |")

    # 失败引擎
    if errors:
        lines.append("")
        lines.append("| ❌ 失败 | 原因 |")
        for e in errors:
            lines.append(f"| {e.split(':')[0]:<14} | {e} |")

    # 脚注
    lines.append("")
    lines.append("---")
    lines.append("📊 **数据来源**: " + ", ".join(engine_names.get(e, e) for e in results.keys()))
    lines.append(f"⏱️ **数据时间**: {q.get('timestamp','')[:19]} CST")
    lines.append(f"📡 **引擎状态**: {len(results)}成功, {len(errors)}失败")
    lines.append(f"🔗 **引擎链**: {', '.join(results.keys())}")
    nc = v.get("distinct_origins", 0)
    lines.append(f"🔍 **独立校验**: {v.get('status','')}（{nc}个独立源）")
    lines.append("🔧 **分析工具**: jw-investment-data v3.5")
    lines.append("⚠️ *数据仅供参考，不构成投资建议*")
    return "\n".join(lines)
