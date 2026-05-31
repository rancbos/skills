#!/usr/bin/env python3
"""
build_summary_plan.py — build an auditable plan before writing SUMMARY.md.

Usage:
  python scripts/build_summary_plan.py books/<title>/clusters.json books/<title>/candidate_scores.json books/<title>/summary_plan.json

The plan selects high-quality clusters and explains what should enter the final
R/I/A1/A2/E/P/B units. It is a recommendation, not a final verdict.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# GRADE_RANK: 分级权重，用于 cluster 优先级计算。
# A≥85: 内容完整、有原文引用、有应用场景，可直接写入 SUMMARY。
# B≥70: 内容可用但需补边界或案例。
# C≥55: 内容弱，通常进附录或需返回阶段 2 补证。
# D<55: 默认不展开，除非用户明确要求。
GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_by_ref(scores: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {s["ref"]: s for s in scores.get("candidates", [])}


def member_ref(member: dict[str, Any]) -> str:
    if member.get("ref"):
        return member["ref"]
    return f"{Path(member.get('file','')).name}#{member.get('id')}"


def cluster_priority(cluster: dict[str, Any], score_map: dict[str, dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    member_scores = [score_map.get(member_ref(m), {}) for m in cluster.get("members", [])]
    numeric = [s.get("score", 0) for s in member_scores]
    grades = [s.get("grade", "D") for s in member_scores]
    avg = sum(numeric) / len(numeric) if numeric else 0
    best = max(numeric) if numeric else 0
    grade_bonus = max((GRADE_RANK.get(g, 1) for g in grades), default=1) * 2
    type_bonus = min(len(cluster.get("types", [])), 4) * 2
    evidence_bonus = min(cluster.get("evidence_count", 1), 5) * 1.5
    warning_penalty = len(cluster.get("warnings", [])) * 4
    priority_score = avg * 0.55 + best * 0.25 + grade_bonus + type_bonus + evidence_bonus - warning_penalty
    meta = {
        "avg_score": round(avg, 2),
        "best_score": best,
        "best_grade": max(grades, key=lambda g: GRADE_RANK.get(g, 1)) if grades else "D",
        "type_count": len(cluster.get("types", [])),
        "evidence_count": cluster.get("evidence_count", 1),
        "warnings": cluster.get("warnings", []),
    }
    return priority_score, meta


def why_include(cluster: dict[str, Any], meta: dict[str, Any]) -> str:
    parts = []
    if meta["best_grade"] in ("A", "B"):
        parts.append(f"最高候选为 {meta['best_grade']} 级")
    if meta["evidence_count"] >= 2:
        parts.append(f"有 {meta['evidence_count']} 个候选互证")
    if meta["type_count"] >= 2:
        parts.append("跨多个 extractor 类型")
    if not parts:
        parts.append("候选质量一般，需人工复核")
    return "；".join(parts)


def risks(cluster: dict[str, Any], meta: dict[str, Any]) -> list[str]:
    out = []
    if meta["evidence_count"] <= 1:
        out.append("单成员 cluster，可能只是孤立洞见")
    if meta["avg_score"] < 70:
        out.append("平均质量分低于 70，写入正文前需补证或降级")
    if "boundary" not in cluster.get("types", []):
        out.append("缺少边界视角，阶段 3 写 B 段时需主动补足")
    if cluster.get("warnings"):
        out.extend(cluster.get("warnings", []))
    return out


def build_plan(clusters: dict[str, Any], scores: dict[str, Any]) -> dict[str, Any]:
    score_map = score_by_ref(scores)
    ranked = []
    for cl in clusters.get("clusters", []):
        pscore, meta = cluster_priority(cl, score_map)
        ranked.append((pscore, cl, meta))
    ranked.sort(key=lambda x: -x[0])

    recommended = []
    appendix = []
    weak = []
    for idx, (pscore, cl, meta) in enumerate(ranked, 1):
        refs = [member_ref(m) for m in cl.get("members", [])]
        unit = {
            "unit_id": f"u{idx:02d}",
            "title": cl.get("canonical_title"),
            "cluster_id": cl.get("cluster_id"),
            "priority_score": round(pscore, 2),
            "quality": meta,
            "why_include": why_include(cl, meta),
            "source_candidates": refs,
            "required_sections": ["R", "I", "A1", "A2", "E", "P", "B"],
            "risks": risks(cl, meta),
        }
        # 纯质量门控：只评判应不应该输出，不设数量上限。
        # A/B 级 + 平均分 ≥65 → 推荐完整展开
        if meta["best_grade"] in ("A", "B") and meta["avg_score"] >= 65:
            recommended.append(unit)
        elif meta["best_grade"] in ("B", "C"):
            appendix.append(unit)
        else:
            weak.append(unit)

    return {
        "ok": True,
        "inputs": {
            "candidate_count": clusters.get("candidate_count"),
            "cluster_count": clusters.get("cluster_count"),
            "grade_distribution": scores.get("grade_distribution"),
        },
        "decision_policy": "A/B clusters with avg_score>=65 enter recommended_units; B/C clusters go to appendix; D/low-score clusters go to excluded_or_weak. No quantity cap.",
        "recommended_units": recommended,
        "appendix_units": appendix,
        "excluded_or_weak": weak,
        "gate_questions": [
            "按 recommended_units 写完整七段，appendix_units 简写或附录？",
            "是否需要返回阶段 2 补 boundary？",
            "是否要收紧到只写 A 级候选？",
        ],
    }


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: build_summary_plan.py <clusters_json> <candidate_scores_json> <out_json>", file=sys.stderr)
        return 2
    clusters_path = Path(sys.argv[1]).expanduser().resolve()
    scores_path = Path(sys.argv[2]).expanduser().resolve()
    out = Path(sys.argv[3]).expanduser().resolve()
    if not clusters_path.exists() or not scores_path.exists():
        print(json.dumps({"ok": False, "error": "clusters_json or candidate_scores_json not found"}, ensure_ascii=False))
        return 1
    plan = build_plan(load_json(clusters_path), load_json(scores_path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "recommended_units": len(plan["recommended_units"]),
        "appendix_units": len(plan["appendix_units"]),
        "excluded_or_weak": len(plan["excluded_or_weak"]),
        "out": str(out),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
