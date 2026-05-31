#!/usr/bin/env python3
"""
clean_text.py — jw-content-summary document cleaning (v3.20)

Purpose:
- Remove high-confidence noise (copyright, ISBN, page numbers, e-book markers)
- Mark uncertain regions (TOC areas, editor/translator notes) — NEVER delete
- Normalize formatting (chapter headings, broken line breaks, quotes)
- Output cleaned text + clean_report.json with suspicious block annotations

Usage:
  python scripts/clean_text.py <book.txt> <books_parent_dir>

Output:
  <book.txt所在目录>/金钱心理学：财富、人性和幸福的永恒真相/
  ├── clean_report.json
  └── cleaned_text.txt
  stdout: path to cleaned text + report summary (JSON)

Note:
  - 输出目录始终为源文件所在目录，第二个参数仅保留CLI兼容
"""

from __future__ import annotations
import json, re, sys
from pathlib import Path
from typing import List, Dict, Tuple

# ============================================================
# HIGH-CONFIDENCE NOISE — safe to remove (near-zero false positive)
# ============================================================
NOISE_PATTERNS = [
    # Copyright / publishing metadata
    r"版权所有\s*[，,]?\s*侵权必究",
    r"ISBN\s*[：:]\s*\d[\d\-]+",
    r"图书在版编目",
    r"出版发行\s*[：:]",
    r"版\s*次\s*[：:]",
    r"印\s*次\s*[：:]",
    r"开\s*本\s*[：:]",
    r"印\s*张\s*[：:]",
    r"字\s*数\s*[：:]",
    r"定\s*价\s*[：:]",
    r"责任编辑\s*[：:]",
    r"封面设计\s*[：:]",
    # E-book platform markers
    r"更多电子书请访问",
    r"扫描二维码",
    r"微信关注",
    r"公众号",
    r"仅供个人学习",
    r"请勿用于商业用途",
    # Pure separator lines (30+ repeating chars)
    r"^[=－\-\*·•]{30,}$",
    r"^[─═]{15,}$",
    # Page numbers
    r"^第[一二三四五六七八九十百千\d]+\s*页\s*$",
    # Pure whitespace / empty lines → handled by normalize()
]

# ============================================================
# UNCERTAIN / SUSPICIOUS — mark only, never delete
# ============================================================
SUSPICIOUS_PATTERNS = {
    "toc_area": [
        # Consecutive chapter-like headings with no body text between them
        r"^(第[一二三四五六七八九十百千\d]+[章节篇部])",
        r"^[一二三四五六七八九十]+[、．.]?\s*$",
        # Short lines with page references (TOC signature)
        r"^\s*.{1,40}\.\.+\s*\d+\s*$",
    ],
    "editor_note": [
        r"编者按[：:]",
        r"编者注[：:]",
        r"\[编者.*?\]",
        r"译者按[：:]",
        r"译者注[：:]",
        r"\[译者.*?\]",
        r"出版说明",
        r"前言",
        r"序\s*言",
    ],
    "footer_header": [
        r"^.{1,30}\s*\|\s*\d+\s*$",  # e.g. "第六章 | 123"
        r"^第[一二三四五六七八九十\d]+章\s*\d+\s*$",  # "第一章 1" pattern
    ],
}

# ============================================================
# FORMAT NORMALIZATION
# ============================================================

def cn_num(num_str: str) -> str:
    """Convert Arabic numeral string to Chinese numeral."""
    mapping = {"0": "零", "1": "一", "2": "二", "3": "三", "4": "四",
               "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}
    result = []
    for ch in num_str:
        result.append(mapping.get(ch, ch))
    return "".join(result)

def normalize_chapter_heading(line: str) -> str:
    """Normalize chapter heading formats for consistent regex matching."""
    # "第 1 章" → "第一章"
    line = re.sub(r"第\s*(\d+)\s*章", lambda m: f"第{cn_num(m.group(1))}章", line)
    # "Chapter 1" → "Chapter 1" (keep as-is, but ensure spacing)
    line = re.sub(r"Chapter\s+(\d+)", r"Chapter \1", line)
    # "1. " → "1. " (normalize)
    line = re.sub(r"(\d+)\s*[\.．]\s+", r"\1. ", line)
    return line

def normalize_line_breaks(text: str) -> str:
    """Merge hard line breaks that break paragraphs mid-sentence."""
    # Don't merge if previous line ends with sentence-ending punctuation
    # or if next line starts with a chapter heading
    result = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if i < len(lines) - 1:
            next_line = lines[i + 1]
            # Merge if: current line doesn't end with sentence-ending char
            # AND next line doesn't start a chapter/title
            if (line and not re.search(r"[。！？\.!\?]$", line.rstrip())
                and not re.match(r"^(第[一二三四五六七八九十\d]+[章节]|Chapter|\d+[\.．、])", next_line.lstrip())
                and next_line.strip()):
                line = line.rstrip() + next_line.lstrip()
                i += 2
                result.append(line)
                continue
        result.append(line)
        i += 1
    return "\n".join(result)

def normalize_quotes(text: str) -> str:
    """Normalize quote characters."""
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    return text

# ============================================================
# MAIN LOGIC
# ============================================================

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
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()

def detect_suspicious_blocks(text: str) -> Tuple[List[Dict], Dict[str, int]]:
    """Scan entire text for suspicious regions. Returns (blocks, type_counts)."""
    lines = text.split("\n")
    suspicious_blocks = []
    type_counts = {}

    # --- TOC area detection v3.20: density-based in first 15% of document ---
    doc_len = len(lines)
    early_zone = int(doc_len * 0.15)
    early_lines = lines[:early_zone]
    
    chapter_hit_lines = []
    for i, line in enumerate(early_lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 80:
            continue
        if re.match(SUSPICIOUS_PATTERNS["toc_area"][0], stripped):
            chapter_hit_lines.append(i)
    
    # If >8 chapter-like headings in first 15%, flag as TOC
    if len(chapter_hit_lines) > 8:
        suspicious_blocks.append({
            "offset_line": 0,
            "end_line": early_zone,
            "length_lines": early_zone,
            "reason": f"likely TOC area: {len(chapter_hit_lines)} chapter-like headings found in first {early_zone} lines",
            "action": "mark_only — do NOT delete",
        })
        type_counts["toc_area"] = type_counts.get("toc_area", 0) + 1

    # --- Editor/translator notes ---
    for i, line in enumerate(lines):
        stripped = line.strip()
        for pat in SUSPICIOUS_PATTERNS["editor_note"]:
            if re.search(pat, stripped):
                suspicious_blocks.append({
                    "offset_line": i,
                    "end_line": i,
                    "length_lines": 1,
                    "reason": f"likely editor/translator note: matches '{pat}'",
                    "action": "mark_only — do NOT delete",
                })
                type_counts["editor_note"] = type_counts.get("editor_note", 0) + 1
                break

    # --- Footer/header patterns ---
    for i, line in enumerate(lines):
        stripped = line.strip()
        for pat in SUSPICIOUS_PATTERNS["footer_header"]:
            if re.match(pat, stripped):
                suspicious_blocks.append({
                    "offset_line": i,
                    "end_line": i,
                    "length_lines": 1,
                    "reason": f"likely footer/header: matches '{pat}'",
                    "action": "mark_only — do NOT delete",
                })
                type_counts["footer_header"] = type_counts.get("footer_header", 0) + 1
                break

    return suspicious_blocks, type_counts

def clean_text(text: str) -> Tuple[str, int]:
    """Remove high-confidence noise lines. Returns (cleaned_text, removed_count)."""
    lines = text.split("\n")
    cleaned = []
    removed = 0
    for line in lines:
        stripped = line.strip()
        should_remove = False
        for pat in NOISE_PATTERNS:
            if re.search(pat, stripped):
                should_remove = True
                break
        if should_remove:
            removed += 1
            continue
        cleaned.append(line)
    return "\n".join(cleaned), removed

def main():
    if len(sys.argv) != 3:
        print("Usage: clean_text.py <book.txt> <books_parent_dir>", file=sys.stderr)
        return 2

    src = Path(sys.argv[1]).expanduser().resolve()
    _books_parent = Path(sys.argv[2]).expanduser().resolve()  # kept for CLI compat, unused for output
    book_title = src.stem
    # Output to source file's directory, not books_parent_dir
    out_dir = src.parent / book_title
    out_dir.mkdir(parents=True, exist_ok=True)

    text = normalize(read_text(src))
    original_chars = len(text)

    # Step 1: Remove high-confidence noise
    text, removed_lines = clean_text(text)

    # Step 2: Detect suspicious regions
    suspicious_blocks, type_counts = detect_suspicious_blocks(text)

    # Step 3: Normalize formatting
    text = normalize_line_breaks(text)
    text = normalize_quotes(text)
    # Normalize chapter headings
    lines = text.split("\n")
    lines = [normalize_chapter_heading(l) for l in lines]
    text = "\n".join(lines)

    # Step 4: Final normalization
    text = normalize(text)

    # Write cleaned text
    cleaned_path = out_dir / "cleaned_text.txt"
    cleaned_path.write_text(text, encoding="utf-8")

    # Write report
    report = {
        "original_chars": original_chars,
        "cleaned_chars": len(text),
        "removed_noise_lines": removed_lines,
        "suspicious_blocks": suspicious_blocks,
        "suspicious_type_counts": type_counts,
        "cleaned_text_path": str(cleaned_path),
    }
    (out_dir / "clean_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({
        "ok": True,
        "cleaned_text": str(cleaned_path),
        "original_chars": original_chars,
        "cleaned_chars": len(text),
        "removed_noise_lines": removed_lines,
        "suspicious_blocks_count": len(suspicious_blocks),
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
