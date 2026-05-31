#!/usr/bin/env python3
"""
score_candidates.py — deterministic quality scoring for jw-content-summary candidates.

Usage:
  python scripts/score_candidates.py books/<title>/candidates books/<title>/clusters.json books/<title>/candidate_scores.json

The score is not a deletion rule. It is a gate signal for review:
- A: ready for SUMMARY consideration
- B: usable with caution
- C: weak; usually appendix or rework
- D: reject/re-extract candidate
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


def parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_listish(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if value is None:
        return []
    value = str(value).strip()
    if not value or value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        value = value[1:-1]
    return [x.strip().strip('"').strip("'") for x in re.split(r"[,，、;；]", value) if x.strip()]


def extract_field(text: str, name: str) -> Any:
    # Support both "- field: value" and "- **field**: value" (bold format from subagents)
    m = re.search(rf"^\s*-?\s*\**\s*{re.escape(name)}\s*\**\s*:\s*(.*)$", text, re.M)
    if m:
        return parse_scalar(m.group(1))
    return None


def extract_heading(text: str) -> str | None:
    m = re.search(r"^#{1,3}\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def read_candidates(cdir: Path) -> list[dict[str, Any]]:
    items = []
    for p in sorted(cdir.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        blocks = re.split(r"\n(?=\s*-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:|##\s+)", "\n" + text)
        for idx, block in enumerate(blocks):
            if not block.strip():
                continue
            # Check for id field (support both "- id:" and "- **id**:" formats)
            has_id = bool(re.search(r"^\s*-?\s*\**\s*id\s*\**\s*:", block, re.M))
            has_source_chapter = bool(re.search(r"^\s*-?\s*\**\s*source_chapter\s*\**\s*:", block, re.M))
            has_type = bool(re.search(r"^\s*-?\s*\**\s*type\s*\**\s*:", block, re.M))
            has_heading = bool(re.search(r"^#{1,3}\s+", block, re.M))
            
            if not has_id and not has_source_chapter and not has_heading:
                continue
            # Skip header-only blocks (title lines without actual candidate fields)
            if not has_id and not has_source_chapter and not has_type:
                continue
            cid = extract_field(block, "id") or f"{p.stem}-{idx}"
            item = {
                "id": str(cid),
                "file": str(p),
                "ref": f"{p.name}#{cid}",
                "title": extract_field(block, "title") or extract_heading(block) or str(cid),
                "type": extract_field(block, "type") or p.stem,
                "source_chapter": extract_field(block, "source_chapter"),
                "source_quote": extract_field(block, "source_quote"),
                "source_line": extract_field(block, "source_line"),
                "summary": extract_field(block, "summary"),
                "keywords": parse_listish(extract_field(block, "keywords")),
                "related": parse_listish(extract_field(block, "related")),
                "v3_pass": extract_field(block, "v3_pass"),
                "v3_reason": extract_field(block, "v3_reason"),
                "v2_scenario": extract_field(block, "v2_scenario"),
                "v1_status": extract_field(block, "v1_status"),
            }
            items.append(item)
    return items


def cluster_evidence_map(clusters_path: Path) -> dict[str, dict[str, Any]]:
    if not clusters_path.exists():
        return {}
    data = json.loads(clusters_path.read_text(encoding="utf-8"))
    mapping = {}
    for cl in data.get("clusters", []):
        for m in cl.get("members", []):
            ref = m.get("ref") or f"{Path(m.get('file','')).name}#{m.get('id')}"
            mapping[ref] = {
                "cluster_id": cl.get("cluster_id"),
                "cluster_title": cl.get("canonical_title"),
                "cluster_evidence_count": cl.get("evidence_count", len(cl.get("members", []))),
                "cluster_types": cl.get("types", []),
                "cluster_warnings": cl.get("warnings", []),
            }
    return mapping


def valid_source_line(v: Any) -> bool:
    """Accept: positive int, numeric string, or descriptive chapter reference."""
    if isinstance(v, int):
        return v > 0
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return False
        if re.fullmatch(r"\d+", s):
            return int(s) > 0
        if re.search(r'\d{4}年|ch\d+|第[零一二三四五六七八九十\d]+[章篇节]|序|前言|附录|致股东|致合伙', s, re.I):
            return True
        if len(s) >= 2 and re.search(r'[\u4e00-\u9fff]', s):
            return True
    return False


def grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def score_candidate(item: dict[str, Any], cluster_info: dict[str, Any]) -> dict[str, Any]:
    score = 100
    penalties = []
    quote = str(item.get("source_quote") or "")

    def penalize(points: int, reason: str):
        nonlocal score
        score -= points
        penalties.append({"points": points, "reason": reason})

    if not quote:
        penalize(30, "missing_source_quote")
    elif len(quote) > 150:
        penalize(20, f"source_quote_too_long:{len(quote)}")

    if not valid_source_line(item.get("source_line")):
        penalize(15, "missing_or_invalid_source_line")

    v3 = item.get("v3_pass")
    v3_pass = v3 is True or (isinstance(v3, str) and v3.lower() == "true")
    if not v3_pass:
        penalize(30, "v3_not_passed")
    if not item.get("v3_reason"):
        penalize(10, "missing_v3_reason")
    if not item.get("v2_scenario") and item.get("type") not in ("glossary", "boundary"):
        penalize(10, "missing_v2_scenario")

    v1 = str(item.get("v1_status") or "").lower()
    if v1 in ("weak", "false", "failed", "fail"):
        penalize(15, f"v1_status:{v1}")

    if len(item.get("related") or []) == 0:
        penalize(5, "empty_related")

    evidence_count = int(cluster_info.get("cluster_evidence_count") or 1)
    if evidence_count <= 1:
        penalize(5, "single_member_cluster")

    score = max(0, min(100, score))
    return {
        "id": item["id"],
        "file": Path(item["file"]).name,
        "ref": item["ref"],
        "title": item.get("title"),
        "type": item.get("type"),
        "score": score,
        "grade": grade(score),
        "signals": {
            "has_source_quote": bool(quote),
            "quote_length_ok": bool(quote) and len(quote) <= 150,
            "has_source_line": valid_source_line(item.get("source_line")),
            "v3_pass": v3_pass,
            "v1_status": item.get("v1_status") or "unknown",
            "has_v2_scenario": bool(item.get("v2_scenario")),
            "related_count": len(item.get("related") or []),
            "cluster_evidence_count": evidence_count,
            "cluster_id": cluster_info.get("cluster_id"),
        },
        "penalties": penalties,
    }


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: score_candidates.py <candidates_dir> <clusters_json> <out_json>", file=sys.stderr)
        return 2
    cdir = Path(sys.argv[1]).expanduser().resolve()
    clusters_path = Path(sys.argv[2]).expanduser().resolve()
    out = Path(sys.argv[3]).expanduser().resolve()
    if not cdir.exists():
        print(json.dumps({"ok": False, "error": f"Directory not found: {cdir}"}, ensure_ascii=False))
        return 1

    items = read_candidates(cdir)
    cmap = cluster_evidence_map(clusters_path)
    scored = [score_candidate(item, cmap.get(item["ref"], {})) for item in items]
    scored.sort(key=lambda x: (-x["score"], x["ref"]))
    distribution = {g: sum(1 for s in scored if s["grade"] == g) for g in ["A", "B", "C", "D"]}
    payload = {
        "ok": True,
        "candidate_count": len(scored),
        "grade_distribution": distribution,
        "average_score": round(sum(s["score"] for s in scored) / len(scored), 2) if scored else 0,
        "top": scored[:10],
        "bottom": sorted(scored, key=lambda x: (x["score"], x["ref"]))[:10],
        "candidates": scored,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "candidate_count": len(scored),
        "grade_distribution": distribution,
        "average_score": payload["average_score"],
        "out": str(out),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
