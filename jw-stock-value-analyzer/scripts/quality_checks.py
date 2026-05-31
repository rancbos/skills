#!/usr/bin/env python3
"""
quality_checks.py — 投资标的质控引擎 v1.0
═══════════════════════════════════════════

三项核心能力:
  1. red_flags()  — 自动扫描ST/负PE/零股息/异常换手/连续亏损/高质押/商誉炸弹
  2. reason()     — 为每个评分维度生成人类可读的解释
  3. checkpoints() — 分析前7步数据完整性校验

参考: daisy screen_a_share 的 red_flags()+reason(), stock-data-acquisition 的 57检查点体系

用法:
  python quality_checks.py --data analysis_data.json
  python quality_checks.py --data analysis_data.json --format markdown
  python quality_checks.py --schema

输出: 标准信封 {ok, data: {red_flags, reasons, checkpoints}, meta}
"""

import argparse, json, math, re, sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── 内部模块 ─────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))
try:
    from output_contract import envelope_ok, envelope_error
except ImportError:
    def envelope_ok(s, d, meta=None): return {"ok": True, "source": s, "data": d, "ts": int(datetime.now().timestamp()), "meta": meta or {}}
    def envelope_error(c, m, source="", retryable=False, meta=None):
        return {"ok": False, "source": source, "error": {"code": c, "message": m, "retryable": retryable}, "ts": int(datetime.now().timestamp()), "meta": meta or {}}

VERSION = "1.0.0"


# ═══════════════════════════════ 红线扫描 ═══════════════════════════
def red_flags(data: Dict) -> Dict:
    """自动扫描投资标的的红线信号

    对标 daisy screen_a_share red_flags() + 邱国鹭六大陷阱

    Args:
        data: 包含 fields 的分析数据
            {name, code, pe, pb, roe, div_yield, turnover, debt_ratio,
             cashflow_3y, goodwill_pct, pledge_pct, profit_growth_3y,
             st_flag, industry}

    Returns:
        {flags: [...], severity: "safe"|"warning"|"danger", score_impact: int}
    """
    flags = []

    # ── 1. ST/退市风险 ──
    name = str(data.get("name", ""))
    code = str(data.get("code", ""))
    if "ST" in name.upper() or "退" in name:
        flags.append({"type": "ST", "severity": "danger",
                       "desc": "ST/退市风险标记，一票否决",
                       "score_impact": -100})

    # ── 2. PE 异常 ──
    pe = to_float(data.get("pe"))
    if pe is not None:
        if pe <= 0:
            flags.append({"type": "negative_pe", "severity": "danger",
                          "desc": f"PE={pe} — 公司亏损，不能用PE估值",
                          "score_impact": -20})
        elif pe > 200:
            flags.append({"type": "extreme_pe", "severity": "warning",
                          "desc": f"PE={pe:.0f} — 极高估值，若增速不匹配是泡沫",
                          "score_impact": -10})

    # ── 3. PB 过低（可能净资产虚高） ──
    pb = to_float(data.get("pb"))
    if pb is not None and pb < 0.3:
        flags.append({"type": "ultra_low_pb", "severity": "warning",
                      "desc": f"PB={pb} — 破净严重，可能资产质量存疑或行业衰退",
                      "score_impact": -5})

    # ── 4. ROE 过高（可能加杠杆） ──
    roe = to_float(data.get("roe"))
    debt = to_float(data.get("debt_ratio"))
    if roe is not None and roe > 50 and debt is not None and debt > 70:
        flags.append({"type": "leveraged_roe", "severity": "warning",
                      "desc": f"ROE={roe}%但资产负债率={debt}% — 高ROE靠杠杆撑，不可持续",
                      "score_impact": -10})

    # ── 5. 零股息 ──
    div = to_float(data.get("div_yield"))
    if div is not None and div <= 0:
        flags.append({"type": "no_dividend", "severity": "info",
                      "desc": "无股息 — 如果成长股可接受，但价值股需关注",
                      "score_impact": -3})

    # ── 6. 换手率异常 ──
    turnover = to_float(data.get("turnover"))
    if turnover is not None and turnover < 0.1:
        flags.append({"type": "illiquid", "severity": "warning",
                      "desc": f"换手率={turnover}% — 流动性差，进出困难",
                      "score_impact": -5})

    # ── 7. 现金流持续为负 ──
    cf = to_float(data.get("cashflow_3y"))
    if cf is not None and cf < 0:
        flags.append({"type": "negative_cashflow", "severity": "danger",
                      "desc": "连续3年经营现金流为负 — 利润可能是纸面富贵",
                      "score_impact": -20})

    # ── 8. 商誉炸弹 ──
    gw = to_float(data.get("goodwill_pct"))
    if gw is not None and gw > 50:
        flags.append({"type": "goodwill_bomb", "severity": "danger",
                      "desc": f"商誉占净资产{gw}% — 减值风险极大（并购后遗症）",
                      "score_impact": -15})
    elif gw is not None and gw > 30:
        flags.append({"type": "high_goodwill", "severity": "warning",
                      "desc": f"商誉占净资产{gw}% — 需关注被并购标的业绩",
                      "score_impact": -8})

    # ── 9. 大股东高质押 ──
    pledge = to_float(data.get("pledge_pct"))
    if pledge is not None and pledge > 50:
        flags.append({"type": "high_pledge", "severity": "danger",
                      "desc": f"大股东质押{pledge}% — 爆仓风险，可能已出逃",
                      "score_impact": -20})
    elif pledge is not None and pledge > 30:
        flags.append({"type": "elevated_pledge", "severity": "warning",
                      "desc": f"大股东质押{pledge}% — 需关注资金链",
                      "score_impact": -8})

    # ── 10. 利润增速连续下滑 ──
    growth = to_float(data.get("profit_growth_3y"))
    if growth is not None and growth < -20:
        flags.append({"type": "declining_profit", "severity": "danger",
                      "desc": f"近3年利润增速{growth}% — 持续恶化，可能基本面出问题",
                      "score_impact": -15})

    # ── 判定严重度 ──
    danger_count = sum(1 for f in flags if f["severity"] == "danger")
    warning_count = sum(1 for f in flags if f["severity"] == "warning")
    total_impact = sum(f["score_impact"] for f in flags)

    if danger_count > 0:
        severity = "danger"
    elif warning_count >= 3:
        severity = "warning"
    elif warning_count >= 1:
        severity = "caution"
    else:
        severity = "safe"

    return {
        "flags": flags,
        "flag_count": len(flags),
        "severity": severity,
        "total_score_impact": total_impact,
        "summary": f"{danger_count}🔴 {warning_count}🟡 → {severity}"
    }


# ═══════════════════════════════ 理由外显 ═══════════════════════════
def reason(dimension: str, score: int, data: Dict) -> str:
    """为评分维度生成人类可读的解释

    对标 daisy screen_a_share reason()

    Args:
        dimension: "industry" | "company" | "valuation"
        score: 该维度的得分
        data: 相关指标数据
    """
    if dimension == "industry":
        return _reason_industry(score, data)
    elif dimension == "company":
        return _reason_company(score, data)
    elif dimension == "valuation":
        return _reason_valuation(score, data)
    return f"得分{score}分"


def _reason_industry(score: int, d: Dict) -> str:
    parts = []
    konzentration = d.get("konzentration", "")
    if konzentration:
        parts.append(f"行业格局：{konzentration}")
    pricing = d.get("pricing_power", "")
    if pricing:
        parts.append(f"定价权：{pricing}")
    moat = d.get("entry_barrier", "")
    if moat:
        parts.append(f"进入壁垒：{moat}")
    return "；".join(parts) if parts else f"行业得分{score}分"


def _reason_company(score: int, d: Dict) -> str:
    parts = []
    roe = to_float(d.get("roe"))
    if roe: parts.append(f"ROE={roe}%")
    margin = to_float(d.get("net_margin"))
    if margin: parts.append(f"净利率={margin}%")
    fcf = to_float(d.get("fcf"))
    if fcf is not None:
        parts.append("FCF充沛" if fcf > 0 else "FCF为负")
    moat_type = d.get("moat_type", "")
    if moat_type: parts.append(f"护城河：{moat_type}")
    return "；".join(parts) if parts else f"公司得分{score}分"


def _reason_valuation(score: int, d: Dict) -> str:
    parts = []
    pe = to_float(d.get("pe"))
    pe_percentile = to_float(d.get("pe_percentile"))
    if pe and pe_percentile:
        parts.append(f"PE={pe:.1f}x，{pe_percentile:.0f}%分位")
    elif pe:
        parts.append(f"PE={pe:.1f}x")
    safety = to_float(d.get("safety_margin"))
    if safety:
        parts.append(f"安全边际={safety:.0f}%")
    return "；".join(parts) if parts else f"估值得分{score}分"


# ═══════════════════════════════ 检查点体系 ═══════════════════════════
CHECKPOINTS = [
    {
        "id": "CP1", "name": "数据完整性检查",
        "description": "是否已完成Step 0.0 API取数+Step 0多源校验?",
        "validate": lambda d: d.get("step0_complete", False),
        "fail_action": "必须先完成API取数和多源校验才能进入分析",
    },
    {
        "id": "CP2", "name": "价格数据验证",
        "description": "当前价格是否≥3个独立源且差异≤2%?",
        "validate": lambda d: d.get("price_sources", 0) >= 3 and d.get("price_discrepancy_pct", 999) <= 2,
        "fail_action": "价格数据不可信，必须补源或标注'数据存疑'",
    },
    {
        "id": "CP3", "name": "近30天事件扫描",
        "description": "是否已完成Step 0.5事件扫描?",
        "validate": lambda d: d.get("step05_complete", False),
        "fail_action": "未扫描近期事件，分析可能遗漏重大信息",
    },
    {
        "id": "CP4", "name": "估值数据合理性",
        "description": "PE>0? PB>0? ROE在合理范围?",
        "validate": lambda d: all([
            to_float(d.get("pe", -1)) != -1,
            to_float(d.get("pb", -1)) != -1,
        ]),
        "fail_action": "估值数据缺失或异常，无法进行可靠估值分析",
    },
    {
        "id": "CP5", "name": "财务数据覆盖",
        "description": "是否有至少3年财务数据?",
        "validate": lambda d: d.get("financial_years", 0) >= 3,
        "fail_action": "数据不足3年，分析结论置信度降级",
    },
    {
        "id": "CP6", "name": "行业可比性",
        "description": "是否有行业对标数据?",
        "validate": lambda d: d.get("peer_data_available", False),
        "fail_action": "无行业对标，评分中行业分析部分置信度降低",
    },
    {
        "id": "CP7", "name": "红线扫描通过",
        "description": "是否存在一票否决项?",
        "validate": lambda d: all(
            f["severity"] != "danger"
            for f in d.get("red_flags_result", {}).get("flags", [{"severity": "safe"}])
        ),
        "fail_action": "触发一票否决红线，结论必须降级为'不推荐'或标注'高风险'",
    },
]


def run_checkpoints(data: Dict) -> Dict:
    """运行全部7个检查点

    Returns:
        {results: [{id, name, passed, note, fail_action}], passed_count, total, pass_rate}
    """
    results = []
    for cp in CHECKPOINTS:
        try:
            passed = cp["validate"](data)
        except Exception:
            passed = False
        results.append({
            "id": cp["id"],
            "name": cp["name"],
            "passed": passed,
            "note": "" if passed else cp["fail_action"],
        })

    passed = sum(1 for r in results if r["passed"])
    return {
        "results": results,
        "passed_count": passed,
        "total": len(CHECKPOINTS),
        "pass_rate": passed / len(CHECKPOINTS),
        "can_proceed": passed >= 6,  # 允许1个失败（CP6行业对标可选）
    }


# ═══════════════════════════════ 公式外显 ═══════════════════════════
def formula_show(name: str, formula: str, variables: Dict, result: float, unit: str = "") -> str:
    """生成可验证的公式展示"""
    var_str = ", ".join(f"{k}={v}" for k, v in variables.items())
    r = f"{result:.2f}{unit}" if unit else f"{result:.2f}"
    return f"**{name}** = {formula} = {r}（{var_str}）"


# ═══════════════════════════════ 工具 ═══════════════════════════════
def to_float(v) -> Optional[float]:
    if v is None: return None
    try: return float(v)
    except: return None


def _schema_json():
    return json.dumps({
        "name": "quality_checks",
        "version": VERSION,
        "description": "投资标的质控引擎 — 红线扫描 + 理由外显 + 7检查点",
        "capabilities": {
            "red_flags": "10项自动红线扫描（ST/负PE/破净/杠杆ROE/零股息/流动性/现金流/商誉/质押/利润下滑）",
            "reason": "为行业/公司/估值三维度生成人类可读解释",
            "checkpoints": "分析前7步数据完整性校验（CP1-CP7）",
            "formula_show": "公式外显——展示计算步骤便于验证",
        },
        "input_format": {
            "name": "str", "code": "str",
            "pe": "float", "pb": "float", "roe": "float",
            "div_yield": "float", "debt_ratio": "float",
            "turnover": "float", "cashflow_3y": "float",
            "goodwill_pct": "float", "pledge_pct": "float",
            "profit_growth_3y": "float",
            "step0_complete": "bool", "step05_complete": "bool",
            "price_sources": "int", "price_discrepancy_pct": "float",
            "financial_years": "int", "peer_data_available": "bool",
            "scores": {"industry": "int", "company": "int", "valuation": "int"},
        },
        "exit_codes": {"0": "ok", "1": "runtime", "3": "validation"},
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════ main ═══════════════════════════════
def main():
    p = argparse.ArgumentParser(f"quality_checks v{VERSION}")
    p.add_argument("--data", help="JSON数据文件路径")
    p.add_argument("--inline", help="内联JSON数据字符串")
    p.add_argument("--format", default="json", choices=["json", "markdown"])
    p.add_argument("--schema", action="store_true")
    args = p.parse_args()

    if args.schema:
        print(_schema_json())
        return 0

    # 加载数据
    try:
        if args.data:
            with open(args.data) as f:
                raw = json.load(f)
        elif args.inline:
            raw = json.loads(args.inline)
        else:
            print(json.dumps(envelope_error(3, "需要 --data 或 --inline", source="quality_checks")))
            return 3
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(json.dumps(envelope_error(3, str(e), source="quality_checks")))
        return 3

    # 红线扫描
    rf = red_flags(raw)

    # 理由生成
    scores = raw.get("scores", {})
    reasons = {
        "industry": reason("industry", scores.get("industry", 0), raw),
        "company": reason("company", scores.get("company", 0), raw),
        "valuation": reason("valuation", scores.get("valuation", 0), raw),
    }

    # 检查点
    raw["red_flags_result"] = rf
    cp = run_checkpoints(raw)

    output = {
        "red_flags": rf,
        "reasons": reasons,
        "checkpoints": cp,
    }

    if args.format == "markdown":
        print(_format_markdown(output, raw.get("name", ""), raw.get("code", "")))
    else:
        print(json.dumps(envelope_ok("quality_checks", output, meta={"version": VERSION}), ensure_ascii=False, indent=2))

    return 0 if cp["can_proceed"] else 1


def _format_markdown(output: Dict, name: str, code: str) -> str:
    lines = [f"## 🔍 质控报告 — {name}（{code}）", ""]

    # 红线
    rf = output["red_flags"]
    lines.append(f"### 🚨 红线扫描：{rf['flag_count']}项 ({rf['severity'].upper()})")
    lines.append("")
    if rf["flags"]:
        for f in rf["flags"]:
            icon = "🔴" if f["severity"] == "danger" else "🟡" if f["severity"] == "warning" else "🔵"
            lines.append(f"- {icon} **{f['type']}**：{f['desc']}（影响{f['score_impact']:+d}分）")
    else:
        lines.append("✅ 未触发任何红线")
    lines.append(f"**总影响**：{rf['total_score_impact']:+d}分")
    lines.append("")

    # 理由
    lines.append("### 💡 评分理由")
    for dim, r in output["reasons"].items():
        dim_cn = {"industry": "行业", "company": "公司", "valuation": "估值"}.get(dim, dim)
        lines.append(f"- **{dim_cn}**：{r}")
    lines.append("")

    # 检查点
    cp = output["checkpoints"]
    lines.append(f"### ✅ 检查点：{cp['passed_count']}/{cp['total']} 通过")
    lines.append("| 检查点 | 通过 | 说明 |")
    lines.append("|--------|:--:|------|")
    for r in cp["results"]:
        icon = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['name']} | {icon} | {r.get('note','')} |")
    lines.append("")
    lines.append(f"**分析许可**：{'可以继续' if cp['can_proceed'] else '请修复后再继续'}")

    lines.append("")
    lines.append("---")
    lines.append("🔧 jw-stock-value-analyzer / quality_checks v" + VERSION)
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
