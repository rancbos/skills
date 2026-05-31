#!/usr/bin/env python3
"""
cross_validate.py — V1 cross-domain corroboration for jw-content-summary

Purpose:
- Detect overlapping source_quotes across different candidate types.
- Detect conflicting V3 judgments.
- Generate a "corroboration report" that the main agent can use
  in Stage 3 to prioritize units and resolve conflicts.

Usage:
  python scripts/cross_validate.py <candidates_dir> <out_json>

Output JSON fields:
  - overlaps: list of overlapping quote groups (same quote in ≥2 types)
  - conflicts: list of conflicting judgments
  - missing_coverage: concepts that appear in only one type and may need
    additional evidence from other types
  - suggestions: auto-generated recommendations for the main agent
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Dict, Any


def norm_quote(q: str) -> str:
    """Normalize a source quote for fuzzy matching."""
    s = re.sub(r'[\s\u3000"「」『』""'']+', '', q)
    return s.lower()


def quote_sim(a: str, b: str) -> float:
    """Fuzzy similarity between two source quotes."""
    if not a or not b:
        return 0.0
    na, nb = norm_quote(a), norm_quote(b)
    if len(na) < 10 or len(nb) < 10:
        return 0.0
    if na in nb or nb in na:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def read_candidates(cdir: Path) -> List[Dict[str, Any]]:
    """Read all candidate entries from the candidates directory."""
    items = []
    for p in sorted(cdir.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        # Same parsing as cluster_candidates.py
        blocks = re.split(r"\n(?=-?\s*id\s*:|##\s+)", text)
        for b in blocks:
            if not b.strip():
                continue
            cid = extract_field(b, "id")
            if not cid:
                continue
            title = extract_field(b, "title") or ""
            typ = extract_field(b, "type") or p.stem
            source_quote = extract_field(b, "source_quote") or ""
            summary = extract_field(b, "summary") or ""
            v3_pass = extract_field(b, "v3_pass") or ""
            source_chapter = extract_field(b, "source_chapter") or ""
            v3_reason = extract_field(b, "v3_reason") or ""

            items.append({
                "id": cid.strip(),
                "file": str(p),
                "title": title.strip(),
                "type": typ.strip(),
                "source_quote": source_quote.strip(),
                "summary": summary.strip(),
                "source_chapter": source_chapter.strip(),
                "v3_pass": v3_pass.strip().lower() in ("true", "yes", "1"),
                "v3_reason": v3_reason.strip(),
            })
    return items


def extract_field(text: str, name: str) -> str:
    """Extract a YAML field value from a candidate block."""
    m = re.search(rf"^-?\s*{name}\s*:\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip().strip('"')
    return ""


def detect_overlaps(items: List[Dict], sim_threshold: float = 0.75) -> List[Dict]:
    """Detect overlapping source_quotes across different types."""
    overlaps = []
    seen_groups = set()

    for i, a in enumerate(items):
        for j, b in enumerate(items):
            if j <= i:
                continue
            if a["type"] == b["type"]:
                continue
            if not a["source_quote"] or not b["source_quote"]:
                continue

            sim = quote_sim(a["source_quote"], b["source_quote"])
            if sim >= sim_threshold:
                group_key = tuple(sorted([a["id"], b["id"]]))
                if group_key in seen_groups:
                    continue
                seen_groups.add(group_key)

                overlaps.append({
                    "ids": [a["id"], b["id"]],
                    "types": [a["type"], b["type"]],
                    "titles": [a["title"], b["title"]],
                    "source_quote_a": a["source_quote"][:200],
                    "source_quote_b": b["source_quote"][:200],
                    "similarity": round(sim, 3),
                    "v3_pass_a": a["v3_pass"],
                    "v3_pass_b": b["v3_pass"],
                    "conflict": a["v3_pass"] != b["v3_pass"],
                })
    return overlaps


def detect_conflicts(items: List[Dict]) -> List[Dict]:
    """Detect conflicting V3 judgments on the same/similar concepts."""
    conflicts = []
    for i, a in enumerate(items):
        for j, b in enumerate(items):
            if j <= i:
                continue
            if a["v3_pass"] == b["v3_pass"]:
                continue
            # Check title similarity
            title_sim = SequenceMatcher(None,
                re.sub(r'[\s\-_:：，,。]', '', a["title"].lower()),
                re.sub(r'[\s\-_:：，,。]', '', b["title"].lower())
            ).ratio()
            if title_sim > 0.6:
                conflicts.append({
                    "ids": [a["id"], b["id"]],
                    "types": [a["type"], b["type"]],
                    "titles": [a["title"], b["title"]],
                    "v3_pass_a": a["v3_pass"],
                    "v3_pass_b": b["v3_pass"],
                    "title_similarity": round(title_sim, 3),
                })
    return conflicts


def detect_missing_coverage(items: List[Dict]) -> List[Dict]:
    """Detect concepts that only appear in one type and may benefit from
    cross-type evidence."""
    type_coverage = {}
    for it in items:
        typ = it["type"]
        if typ not in type_coverage:
            type_coverage[typ] = []
        type_coverage[typ].append(it["title"])

    all_types = set(type_coverage.keys())
    suggestions = []

    # For each type, find titles that are unique to that type
    for typ, titles in type_coverage.items():
        other_titles = set()
        for ot, ot_titles in type_coverage.items():
            if ot != typ:
                for t in ot_titles:
                    other_titles.add(re.sub(r'[\s\-_:：，,。]', '', t.lower()))

        for title in titles:
            norm_t = re.sub(r'[\s\-_:：，,。]', '', title.lower())
            if norm_t not in other_titles and len(title) > 3:
                # Check if any item from another type has a similar title
                related = []
                for it in items:
                    if it["type"] == typ:
                        continue
                    ts = SequenceMatcher(None, norm_t,
                        re.sub(r'[\s\-_:：，,。]', '', it["title"].lower())
                    ).ratio()
                    if ts > 0.4:
                        related.append({"id": it["id"], "type": it["type"],
                                        "title": it["title"],
                                        "similarity": round(ts, 3)})
                if not related:
                    suggestions.append({
                        "title": title,
                        "type": typ,
                        "suggestion": f"Consider adding evidence from other types (e.g., a principle needs a case, a framework needs a boundary)",
                    })
                else:
                    suggestions.append({
                        "title": title,
                        "type": typ,
                        "suggestion": f"Has partial cross-type evidence",
                        "related": related,
                    })
    return suggestions


def generate_suggestions(overlaps: List, conflicts: List, coverage: List,
                         item_count: int) -> List[str]:
    """Generate human-readable suggestions for the main agent."""
    suggestions = []

    if conflicts:
        suggestions.append(
            f"⚠️ {len(conflicts)} CONFLICTING V3 judgments detected. "
            f"Main agent MUST resolve these before Stage 3 summary."
        )
        for c in conflicts[:5]:
            suggestions.append(
                f"  Conflict: {c['titles'][0]} ({c['types'][0]}, v3={c['v3_pass_a']}) "
                f"vs {c['titles'][1]} ({c['types'][1]}, v3={c['v3_pass_b']})"
            )

    if overlaps:
        suggestions.append(
            f"ℹ️ {len(overlaps)} cross-type overlaps found. "
            f"These can be merged or one type can be dropped in Stage 3."
        )
        for o in overlaps[:5]:
            suggestions.append(
                f"  Overlap: {o['titles'][0]} ({o['types'][0]}) ↔ "
                f"{o['titles'][1]} ({o['types'][1]}) sim={o['similarity']}"
            )

    if coverage:
        suggestions.append(
            f"💡 {len(coverage)} concepts lack cross-type evidence. "
            f"Consider whether they need additional support."
        )

    type_counts = {}
    for it in range(item_count):
        pass  # Will count from actual data

    return suggestions


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: cross_validate.py <candidates_dir> <out_json>", file=sys.stderr)
        return 2

    cdir = Path(sys.argv[1]).expanduser().resolve()
    out = Path(sys.argv[2]).expanduser().resolve()

    if not cdir.is_dir():
        print(f"Error: {cdir} is not a directory", file=sys.stderr)
        return 1

    items = read_candidates(cdir)
    if not items:
        print(f"Warning: no candidates found in {cdir}", file=sys.stderr)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"status": "empty", "candidate_count": 0},
                      ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    overlaps = detect_overlaps(items)
    conflicts = detect_conflicts(items)
    coverage = detect_missing_coverage(items)
    suggestions = generate_suggestions(overlaps, conflicts, coverage, len(items))

    type_counts = {}
    for it in items:
        type_counts[it["type"]] = type_counts.get(it["type"], 0) + 1

    report = {
        "candidate_count": len(items),
        "type_counts": type_counts,
        "overlap_count": len(overlaps),
        "conflict_count": len(conflicts),
        "missing_coverage_count": len(coverage),
        "overlaps": overlaps,
        "conflicts": conflicts,
        "missing_coverage": coverage[:20],  # cap at 20 to keep file size manageable
        "suggestions": suggestions,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "candidate_count": len(items),
        "overlap_count": len(overlaps),
        "conflict_count": len(conflicts),
        "out": str(out),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
