#!/usr/bin/env python3
"""
build_book_index.py — jw-content-summary deterministic preprocessing

Purpose:
- Build a lightweight book index without LLM tokens.
- Split text into chapters.
- Extract structural snippets, candidate definitions, cases, warnings.

Usage:
  python scripts/build_book_index.py /path/to/book.txt books/

Output:
  <book.txt所在目录>/金钱心理学：财富、人性和幸福的永恒真相/
  ├── book-index.json
  ├── chapters/ch001.txt ...
  ├── snippets/definitions.json
  ├── snippets/cases.json
  ├── snippets/warnings.json
  └── snippets/quotes.json

Note:
  - Output folder name is derived from the book title (filename without extension)
  - Folder name uses the original Chinese title, not an English slug
  - Output directory is always <book.txt所在目录>/，第二个参数仅保留CLI兼容
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any


CHAPTER_PATTERNS = [
    re.compile(r"^\s*(第[一二三四五六七八九十百千万0-9]+[章节讲篇部回].*)\s*$"),
    re.compile(r"^\s*(Chapter\s+\d+[:：]?.*)\s*$", re.I),
    re.compile(r"^\s*(\d+[\.、]\s+\S.*)$"),
]

DEF_PATTERNS = [
    r"所谓(.{1,30}?)[，,是指就是即]",
    r"(.{1,30}?)[，,]?是指",
    r"我把(.{1,30}?)[称叫]为",
    r"(.{1,30}?)[，,]?指的是",
    # v3.23: expanded definition patterns for better coverage
    r"(.{1,20}?)[，,]?即.{1,10}",
    r"(.{1,20}?)就是.{1,10}",
    r"(.{1,20}?)的核心是",
    r"(.{1,20}?)的本质是",
    r"(.{1,20}?)可以理解为",
    r"简言之[，,]?(.{1,20}?)即",
    r"(.{1,20}?)，又称",
    r"所谓(.{1,30}?)[，,]?就是",
]

CASE_HINTS = ["案例", "故事", "例如", "比如", "一次", "曾经", "实践", "应用", "实验"]
WARNING_HINTS = ["误区", "失败", "陷阱", "不要", "不能", "警惕", "风险", "反例", "错误"]
QUOTE_HINTS = ["重要", "关键", "核心", "因此", "所以", "换句话说", "结论"]


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "gb18030", "big5"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="ignore")


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_chapter_heading(line: str) -> bool:
    if len(line.strip()) > 80:
        return False
    return any(p.match(line) for p in CHAPTER_PATTERNS)


def split_chapters(text: str) -> tuple:
    """Returns (chapters, structure_type, toc_ratio).
    structure_type: 'chapters' | 'chunks' | 'toc_filtered'
    toc_ratio: fraction of headings filtered out as TOC (0.0-1.0)
    """
    lines = text.splitlines()
    headings = []
    for i, line in enumerate(lines):
        if is_chapter_heading(line):
            headings.append((i, line.strip()))

    if not headings:
        # fallback: split every ~5000 Chinese chars
        chunks = []
        size = 5000
        for idx, start in enumerate(range(0, len(text), size), 1):
            chunks.append({"id": f"ch{idx:03d}", "title": f"Chunk {idx}", "text": text[start:start+size]})
        return chunks, "chunks", 0.0

    total_headings = len(headings)

    # v3.14: TOC detection — if >30% of headings are clustered in first 15% of document,
    # mark as likely TOC compilation and filter them out
    doc_len = len(lines)
    toc_threshold_line = int(doc_len * 0.15)
    early_headings = sum(1 for line_no, _ in headings if line_no < toc_threshold_line)
    toc_ratio = early_headings / total_headings if total_headings else 0.0

    # Filter out TOC-style headings: headings with no substantive body between them
    real_headings = []
    for idx, (line_no, title) in enumerate(headings):
        next_heading_line = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
        between_lines = lines[line_no + 1:next_heading_line]
        content_lines = [l for l in between_lines if l.strip() and not is_chapter_heading(l)]
        if content_lines:
            real_headings.append((line_no, title))

    if not real_headings:
        real_headings = headings

    structure_type = "toc_filtered" if toc_ratio > 0.3 else "chapters"

    chapters = []
    for idx, (start_line, title) in enumerate(real_headings):
        end_line = real_headings[idx + 1][0] if idx + 1 < len(real_headings) else len(lines)
        body = "\n".join(lines[start_line:end_line]).strip()
        if len(body) < 50:
            continue
        chapters.append({"id": f"ch{idx+1:03d}", "title": title, "text": body})
    return chapters, structure_type, toc_ratio


def paragraphs(text: str) -> List[str]:
    ps = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [p for p in ps if len(p) >= 20]


def first_last_paras(text: str, n: int = 1, max_len: int = 200) -> Dict[str, List[str]]:
    """Return first n paragraphs, truncated to max_len chars. Last paragraphs omitted for size.

    ⚠️ 已验证安全阈值（v4.68 巴菲特书 pipeline 验证）：
    - max_len=200：足够暴露章节主题词，pipeline 输出与未截断版本完全一致
    - last=[]：last_paragraphs 对 stage1 路由无帮助，删除后 book-index.json 缩减 40.6%
    - 验证数据：62 candidates, avg_score=89.52, 61 recommended, 1 appendix（零质量损失）
    """
    ps = paragraphs(text)
    def truncate(lst):
        return [p[:max_len] + ("..." if len(p) > max_len else "") for p in lst]
    return {"first": truncate(ps[:n]), "last": []}


def headings_in(text: str) -> List[str]:
    hs = []
    for line in text.splitlines():
        s = line.strip()
        if 2 <= len(s) <= 60 and (s.startswith("#") or is_chapter_heading(s) or re.match(r"^\d+(\.\d+)*[、.\s]+\S+", s)):
            hs.append(s.lstrip("# "))
    return hs[:50]


def find_snippets(chapters: List[Dict[str, Any]], hints: List[str], max_per_ch: int = 5) -> List[Dict[str, str]]:
    out = []
    for ch in chapters:
        count = 0
        for p in paragraphs(ch["text"]):
            if any(h in p for h in hints):
                out.append({"chapter_id": ch["id"], "chapter_title": ch["title"], "text": p[:500]})
                count += 1
                if count >= max_per_ch:
                    break
    return out


def find_definitions(chapters: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    out = []
    regs = [re.compile(p) for p in DEF_PATTERNS]
    for ch in chapters:
        for p in paragraphs(ch["text"]):
            for rg in regs:
                m = rg.search(p)
                if m:
                    term = re.sub(r"[\s，,。；;：:]+", "", m.group(1))[:30]
                    if 1 < len(term) <= 30:
                        out.append({"term": term, "chapter_id": ch["id"], "chapter_title": ch["title"], "context": p[:500]})
                        break
    # de-dupe by term + chapter
    seen = set(); uniq = []
    for x in out:
        k = (x["term"], x["chapter_id"])
        if k not in seen:
            seen.add(k); uniq.append(x)
    return uniq[:200]


def keyword_counts(text: str) -> List[Dict[str, Any]]:
    # Simple Chinese/English token heuristic; deterministic and dependency-free.
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}|[\u4e00-\u9fff]{2,6}", text)
    stop = set("我们 你们 他们 一个 这个 那个 因为 所以 但是 如果 不是 就是 可以 没有 什么 这些 那些 以及 进行 通过 作者 读者 问题 方法 时候 可能".split())
    c = Counter(t for t in tokens if t not in stop)
    return [{"term": k, "count": v} for k, v in c.most_common(100)]


def compute_book_type_hint(text: str, definition_count: int, keyword_list: List[Dict]) -> str:
    """v3.14: compute a book type hint from structural density metrics.
    
    Returns one of: 'methodology_treatise' | 'essay_collection' | 'academic' |
                    'biography' | 'manual' | 'unknown'
    """
    total = len(text)
    
    # Definition density: terms per 10K chars
    def_density = (definition_count / total) * 10000 if total else 0
    
    # Argument connector density: logical connectors per 1K chars
    connectors = re.findall(r'因此|所以|但是|然而|综上所述|与此相反|换句话说|也就是说'
                           r'|因为|由于|由此可见|换言之|简而言之', text)
    arg_density = (len(connectors) / total) * 1000 if total else 0
    
    # Case hint density: case/example markers per 1K chars
    cases = re.findall(r'案例|故事|例如|比如|案例研究|实证|应用|经典案例', text)
    case_density = (len(cases) / total) * 1000 if total else 0
    
    # Procedure markers: numbered steps, lists
    procedures = re.findall(r'第[一二三四五六七八九十\d]+步|步骤[一二三四五六七八九十\d]+'
                           r'|^\s*\d+[\.、]\s+\S', text, re.M)
    proc_density = (len(procedures) / total) * 1000 if total else 0
    
    # Classification logic (v3.23: lowered academic threshold from def_d 8→5, arg_d 3→1.8)
    if def_density > 5 and arg_density >= 1.8:
        return 'academic'       # moderate-high definition + argument density
    elif proc_density > 2:
        return 'manual'         # many numbered steps
    elif case_density > 3:
        return 'biography'      # many case stories
    elif arg_density > 2.5:
        return 'methodology_treatise'  # systematic argumentation
    elif def_density > 3:
        return 'methodology_treatise'
    else:
        return 'essay_collection'  # low structural signals → likely fragmentary


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: build_book_index.py <book.txt> <books_parent_dir>", file=sys.stderr)
        return 2
    src = Path(sys.argv[1]).expanduser().resolve()
    _books_parent = Path(sys.argv[2]).expanduser().resolve()  # kept for CLI compat, unused for output

    # Derive folder name from book title (filename without extension)
    book_title = src.stem  # e.g. "金钱心理学：财富、人性和幸福的永恒真相"
    # Output to source file's directory, not books_parent_dir
    out = src.parent / book_title

    out.mkdir(parents=True, exist_ok=True)
    (out / "chapters").mkdir(exist_ok=True)
    (out / "snippets").mkdir(exist_ok=True)

    text = normalize(read_text(src))

    # v3.20: auto-trigger cleaning when TOC contamination or fragmentation detected
    cleaned_text_path = None
    clean_report = None
    try:
        from clean_text import clean_text as ct_clean, detect_suspicious_blocks
        # Quick pre-scan for TOC contamination
        temp_text = text
        text_blocks, _ = detect_suspicious_blocks(temp_text)
        toc_detected = any("toc_area" in b.get("reason", "") and "chapter-like" in b.get("reason", "") for b in text_blocks)
        if toc_detected:
            import subprocess, sys as _sys
            script = str(Path(__file__).parent / "clean_text.py")
            result = subprocess.run([_sys.executable, script, str(src), str(src.parent)],
                                   capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                rpt = json.loads(result.stdout)
                cleaned_text_path = rpt.get("cleaned_text")
                if cleaned_text_path and Path(cleaned_text_path).exists():
                    text = normalize(read_text(Path(cleaned_text_path)))
                    clean_report_path = src.parent / book_title / "clean_report.json"
                    if clean_report_path.exists():
                        clean_report = json.loads(clean_report_path.read_text(encoding="utf-8"))
                    print(f"[clean_text] TOC detected, using cleaned text: {cleaned_text_path}", file=sys.stderr)
    except Exception as e:
        print(f"[clean_text] auto-clean skipped: {e}", file=sys.stderr)

    chapters, structure_type, toc_ratio = split_chapters(text)

    # v3.19: compute fragmentation ratio and per-chapter meaningful flag
    # Threshold 500: 经验值——章节正文 <500 字符通常是 TOC 碎片、序言片段或空白页，
    # 不是真正的内容章节。实测《价值：我对投资的思考》8 章 TOC 碎片均 <100 字符。
    meaningful_threshold = 500  # chapters with <500 chars are likely TOC fragments
    fragmented_count = sum(1 for ch in chapters if len(ch["text"]) < meaningful_threshold)
    fragmentation_ratio = round(fragmented_count / len(chapters), 3) if chapters else 0.0

    chapter_index = []
    for ch in chapters:
        cid = ch["id"]
        (out / "chapters" / f"{cid}.txt").write_text(ch["text"], encoding="utf-8")
        fl = first_last_paras(ch["text"])
        is_meaningful = len(ch["text"]) >= meaningful_threshold
        chapter_index.append({
            "id": cid,
            "title": ch["title"],
            "char_count": len(ch["text"]),
            "is_meaningful": is_meaningful,
            "headings": headings_in(ch["text"]),
            "first_paragraphs": fl["first"],
            "last_paragraphs": fl["last"],
        })

    definitions = find_definitions(chapters)
    kws = keyword_counts(text)
    book_type_hint = compute_book_type_hint(text, len(definitions), kws)

    # v3.14: compute structure density metrics
    total = len(text)
    connectors = re.findall(r'因此|所以|但是|然而|综上所述|与此相反|换句话说|也就是说'
                           r'|因为|由于|由此可见|换言之|简而言之', text)
    arg_density = (len(connectors) / total) * 1000 if total else 0
    def_density = (len(definitions) / total) * 10000 if total else 0

    meaningful_chapters = sum(1 for ch in chapter_index if ch["is_meaningful"])

    index = {
        "source": str(src),
        "total_chars": len(text),
        "chapter_count": len(chapters),
        "meaningful_chapter_count": meaningful_chapters,
        "fragmentation_ratio": fragmentation_ratio,
        "structure_type": structure_type,
        "toc_ratio": round(toc_ratio, 3),
        "book_type_hint": book_type_hint,
        "cleaned": cleaned_text_path is not None,
        "clean_text_path": cleaned_text_path,
        "clean_report": clean_report,
        "structure_metrics": {
            "definition_density_per_10k": round(def_density, 2),
            "argument_connector_density_per_1k": round(arg_density, 2),
        },
        "chapters": chapter_index,
        "keywords": kws,
    }

    (out / "book-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "snippets" / "definitions.json").write_text(json.dumps(find_definitions(chapters), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "snippets" / "cases.json").write_text(json.dumps(find_snippets(chapters, CASE_HINTS), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "snippets" / "warnings.json").write_text(json.dumps(find_snippets(chapters, WARNING_HINTS), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "snippets" / "quotes.json").write_text(json.dumps(find_snippets(chapters, QUOTE_HINTS), ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "out_dir": str(out), "total_chars": len(text), "chapter_count": len(chapters)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
