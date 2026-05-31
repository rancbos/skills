#!/usr/bin/env python3
"""
cluster_candidates.py — soft cluster candidates without deleting anything.

Usage:
  python scripts/cluster_candidates.py books/<title>/candidates books/<title>/clusters.json

v4.4 upgrades clustering from title-only matching to multi-signal matching:
- title similarity
- keyword overlap
- related overlap
- summary token overlap

The script still does not delete or rewrite candidates. It only groups and warns.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def parse_listish(value: str | None) -> list[str]:
    if not value:
        return []
    value = value.strip().strip('"').strip("'")
    if value in ("", "[]"):
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            inner = value[1:-1]
            return [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
    return [x.strip() for x in re.split(r"[,，、;；]", value) if x.strip()]


def extract_field(text: str, name: str) -> str | None:
    # Support both "- field: value" and "- **field**: value" (bold format from subagents)
    m = re.search(rf"^\s*-?\s*\**\s*{re.escape(name)}\s*\**\s*:\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return None


def extract_heading(text: str) -> str | None:
    m = re.search(r"^#{1,3}\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def norm(s: str) -> str:
    s = re.sub(r"[\s\-—_:：，,。.!！?？（）()《》\[\]、；;]+", "", s.lower())
    return s


def token_set(s: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}|[\u4e00-\u9fff]{2,6}", s or "")
    stop = set("我们 你们 他们 一个 这个 那个 因为 所以 但是 如果 不是 就是 可以 没有 什么 这些 那些 以及 进行 通过 作者 读者 问题 方法 时候 可能 核心 关键 重要".split())
    return {t.lower() for t in tokens if t and t not in stop}


def title_similarity(a: str, b: str) -> float:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na in nb or nb in na:
        return 0.92
    return SequenceMatcher(None, na, nb).ratio()


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def read_candidates(cdir: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for p in sorted(cdir.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        blocks = re.split(r"\n(?=\s*-?\s*\*{0,2}\s*id\s*\*{0,2}\s*:|##\s+)", "\n" + text)
        for idx, b in enumerate(blocks):
            if not b.strip():
                continue
            # Check for id field (support both "- id:" and "- **id**:" formats)
            has_id = bool(re.search(r"^\s*-?\s*\**\s*id\s*\**\s*:", b, re.M))
            has_source_chapter = bool(re.search(r"^\s*-?\s*\**\s*source_chapter\s*\**\s*:", b, re.M))
            has_type = bool(re.search(r"^\s*-?\s*\**\s*type\s*\**\s*:", b, re.M))
            has_heading = bool(re.search(r"^#{1,3}\s+", b, re.M))
            
            if not has_id and not has_source_chapter and not has_heading:
                continue
            # Skip header-only blocks (title lines without actual candidate fields)
            if not has_id and not has_source_chapter and not has_type:
                continue
            cid = extract_field(b, "id") or f"{p.stem}-{idx}"
            title = extract_field(b, "title") or extract_heading(b) or cid
            summary = extract_field(b, "summary") or b[:300]
            typ = extract_field(b, "type") or p.stem
            keywords = parse_listish(extract_field(b, "keywords"))
            related = parse_listish(extract_field(b, "related"))
            source_chapter = extract_field(b, "source_chapter") or ""
            items.append({
                "id": cid,
                "file": str(p),
                "title": title.strip(),
                "type": typ.strip(),
                "summary": summary.strip()[:800],
                "keywords": keywords,
                "related": related,
                "source_chapter": source_chapter,
                "ref": f"{p.name}#{cid}",
            })
    return items


def pair_score(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    title_sim = title_similarity(a["title"], b["title"])
    ka, kb = set(a.get("keywords") or []), set(b.get("keywords") or [])
    ra, rb = set(a.get("related") or []), set(b.get("related") or [])
    keyword_overlap = jaccard(ka, kb)
    related_overlap = jaccard(ra, rb)
    summary_overlap = jaccard(token_set(a.get("summary", "")), token_set(b.get("summary", "")))
    score = 0.40 * title_sim + 0.30 * keyword_overlap + 0.15 * related_overlap + 0.15 * summary_overlap
    return {
        "score": round(score, 4),
        "title_similarity": round(title_sim, 4),
        "keyword_overlap_score": round(keyword_overlap, 4),
        "related_overlap_score": round(related_overlap, 4),
        "summary_overlap_score": round(summary_overlap, 4),
        "keyword_overlap": sorted(ka & kb),
        "related_overlap": sorted(ra & rb),
    }


def should_merge(metrics: dict[str, Any], threshold: float) -> bool:
    if metrics["score"] >= threshold:
        return True
    # Catch semantically close entries with different wording.
    if metrics["keyword_overlap_score"] >= 0.45 and metrics["summary_overlap_score"] >= 0.20:
        return True
    if metrics["related_overlap_score"] >= 0.50 and metrics["keyword_overlap_score"] >= 0.25:
        return True
    return False


def cluster(items: list[dict[str, Any]], threshold: float = 0.35) -> list[dict[str, Any]]:
    # Threshold 0.35: 经验值——原0.58对信件汇编/案例集类书籍太高，导致每个candidate独立成cluster。
    # 0.35 允许 keyword_overlap 0.5 或 title_similarity 0.6 即可合并，适合碎片化候选。
    # 方法论专著/学术书可传 0.58 保持精度。
    # 加权后，0.58 约等于"标题相似 >0.6 且关键词重叠 >0.3"的保守合并边界。
    # 更低（如 0.50）会过度合并不同方法论；更高（如 0.70）会遗漏语义相近但措辞不同的候选。
    clusters: list[dict[str, Any]] = []
    for item in items:
        best_idx = None
        best_metrics = None
        best_score = -1.0
        for idx, cl in enumerate(clusters):
            rep = cl["representative"]
            metrics = pair_score(item, rep)
            if metrics["score"] > best_score:
                best_idx, best_metrics, best_score = idx, metrics, metrics["score"]
        if best_idx is not None and best_metrics and should_merge(best_metrics, threshold):
            cl = clusters[best_idx]
            cl["members"].append(item)
            cl["merge_evidence"].append({
                "member": item["ref"],
                "against": cl["representative"]["ref"],
                **best_metrics,
            })
        else:
            clusters.append({
                "cluster_id": f"c{len(clusters)+1:03d}",
                "canonical_title": item["title"],
                "representative": item,
                "members": [item],
                "merge_evidence": [],
            })

    for cl in clusters:
        members = cl["members"]
        cl["evidence_count"] = len(members)
        cl["types"] = sorted(set(m["type"] for m in members))
        cl["chapters"] = sorted(set(m.get("source_chapter", "") for m in members if m.get("source_chapter")))
        cl["keywords"] = sorted(set(k for m in members for k in m.get("keywords", [])))[:30]
        cl["related"] = sorted(set(r for m in members for r in m.get("related", [])))[:30]
        warnings: list[str] = []
        if len(members) == 1:
            warnings.append("single_member_cluster")
        if len(members) > 1 and not cl["keywords"] and not cl["related"]:
            warnings.append("merged_without_keywords_or_related")
        cl["warnings"] = warnings
        cl.pop("representative", None)
    return clusters


def detect_granularity(items: list[dict[str, Any]]):
    file_groups: dict[str, list[dict[str, Any]]] = {}
    for it in items:
        fname = Path(it["file"]).name
        file_groups.setdefault(fname, []).append(it)
    per_file = {k: len(v) for k, v in file_groups.items()}
    if any(v > 2 for v in per_file.values()):
        return "per_entry", per_file
    return "per_file", per_file


def detect_quality(clusters: list[dict[str, Any]], items: list[dict[str, Any]]) -> dict[str, Any]:
    single_count = sum(1 for cl in clusters if len(cl["members"]) == 1)
    suggested_merges = []
    suspicious_merges = []

    # Suggested merge: unmerged entries with strong keyword/summary signal.
    reps = [cl["members"][0] for cl in clusters]
    for i, a in enumerate(reps):
        for b in reps[i + 1:]:
            metrics = pair_score(a, b)
            if metrics["title_similarity"] < 0.45 and metrics["keyword_overlap_score"] >= 0.45:
                suggested_merges.append({"a": a["ref"], "b": b["ref"], **metrics})
            if metrics["title_similarity"] >= 0.75 and metrics["keyword_overlap_score"] == 0 and metrics["related_overlap_score"] == 0:
                suspicious_merges.append({"a": a["ref"], "b": b["ref"], **metrics})

    return {
        "single_member_ratio": round(single_count / len(clusters), 3) if clusters else 0.0,
        "single_member_count": single_count,
        "suggested_merge_count": len(suggested_merges),
        "suspicious_similarity_count": len(suspicious_merges),
        "suggested_merges": suggested_merges[:20],
        "suspicious_similar_pairs": suspicious_merges[:20],
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: cluster_candidates.py <candidates_dir> <out_json>", file=sys.stderr)
        return 2
    cdir = Path(sys.argv[1]).expanduser().resolve()
    out = Path(sys.argv[2]).expanduser().resolve()
    if not cdir.exists():
        print(json.dumps({"ok": False, "error": f"Directory not found: {cdir}"}, ensure_ascii=False))
        return 1
    items = read_candidates(cdir)
    clusters = cluster(items)
    granularity, entries_per_file = detect_granularity(items)
    quality = detect_quality(clusters, items)

    # v4.55: warn if per_file granularity detected with high single_member_ratio
    # This is the root cause of §9.2 "全单成员碎片" — per_file creates N×2 single-member clusters
    if granularity == "per_file" and quality["single_member_ratio"] > 0.8:
        print(f"⚠️ WARNING: granularity='per_file' detected with single_member_ratio={quality['single_member_ratio']}. "
              f"This is likely the §9.2 per_file granularity bug. "
              f"Re-run with --granularity by_type to fix.", file=sys.stderr)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "candidate_count": len(items),
        "file_count": len(entries_per_file),
        "entries_per_file": entries_per_file,
        "granularity": granularity,
        "cluster_count": len(clusters),
        "quality": quality,
        "clusters": clusters,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "candidate_count": len(items),
        "cluster_count": len(clusters),
        "granularity": granularity,
        "single_member_ratio": quality["single_member_ratio"],
        "suggested_merge_count": quality["suggested_merge_count"],
        "out": str(out),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
