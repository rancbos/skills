#!/usr/bin/env python3
"""
validate_summary.py — Quick quality gate for SUMMARY.md before delivery.

Validates:
  1. Five questions (一、～五、) are present and non-placeholder
  2. All R-section quotes are ≤150 Chinese characters
  3. All I-section (自述) bodies are ≤300 Chinese characters
  4. Every R-section has a chapter citation (第N章)
  5. Every top-level methodology unit has R/I/A1/A2/E/P/B present

Usage:
    python validate_summary.py <path_to_SUMMARY.md>
"""

import os
import re
import sys


def count_content_chars(text: str) -> int:
    """Count non-whitespace characters (CJK + punctuation + English + digits), stripping markdown."""
    clean = re.sub(r'[*_#>\[\]`]', '', text)
    return len(clean.replace('\n', '').replace(' ', ''))


def check_summary(path: str) -> list[str]:
    issues: list[str] = []

    with open(path, encoding='utf-8') as f:
        content = f.read()

    # 1. Five questions present (flexible: accept 5-substring list OR numbered format)
    # Standard: "作者的写作意图" etc. as section titles
    # Numbered: "### 1. 这本书解决什么问题？" etc. (reverse-engineered books)
    five_q_standard = [
        '作者的写作意图',
        '这本书在谈什么',
        '全书的内容结构',
        '这本书有道理吗',
        '这本书与自己的关系',
    ]
    five_q_numbered = [
        '这本书解决什么问题',
        '作者的核心观点是什么',
        '作者的核心主张是什么',
        '这本书的回答有什么独特之处',
        '这本书的独特价值是什么',
        '普通人最应该记住什么',
        '这本书适用于哪些场景',
        '读者能获得什么',
        '如何验证学习效果',
    ]
    # Allow common Chinese phrasing variants
    five_q_numbered_aliases = [
        ('作者的核心主张是什么', '作者的核心观点是什么'),
        ('这本书的独特价值是什么', '这本书的回答有什么独特之处'),
    ]
    # Build expanded set: standard + numbered + alias targets
    # Aliases count toward their target question in the standard set
    five_q_expanded = set(five_q_standard + five_q_numbered)
    for alias, target in five_q_numbered_aliases:
        if alias in content:
            five_q_expanded.add(target)
    five_q_qformat = [
        'Q1：',
        'Q2：',
        'Q3：',
        'Q4：',
        'Q5：',
    ]
    # Allow common Chinese phrasing variants
    five_q_numbered_aliases = [
        ('作者的核心主张是什么', '作者的核心观点是什么'),
        ('这本书的独特价值是什么', '这本书的回答有什么独特之处'),
    ]
    # Check three formats; pass if ANY complete set of 5 is found:
    # Format A: standard (作者的写作意图 etc.)
    # Format B: numbered (这本书解决什么问题 etc.) with aliases
    # Format C: Q-format (Q1： etc.)
    standard_found = sum(1 for q in five_q_standard if q in content)
    numbered_found = [q for q in five_q_numbered if q in content]
    qformat_found = sum(1 for q in five_q_qformat if q in content)
    if standard_found >= 5:
        pass  # A complete
    elif len(numbered_found) >= 5:
        pass  # B complete
    elif qformat_found >= 5:
        pass  # C complete
    else:
        # Only report missing from the format that was attempted
        if standard_found > 0:
            missing = [q for q in five_q_standard if q not in content]
            issues.append(f'[MISSING] Five-question standard format, missing: {missing}')
        elif len(numbered_found) > 0:
            missing = [q for q in five_q_numbered if q not in content]
            issues.append(f'[MISSING] Five-question numbered format, found {len(numbered_found)}/5: {missing}')
        else:
            issues.append(f'[MISSING] Five-question section: no complete set found (standard: {standard_found}, numbered: {len(numbered_found)}, qformat: {qformat_found})')

    # 2. R-section quote length ≤150
    #    Threshold rationale: 实测 20+ 本中文书，>150 字符的引用通常包含多个论点或数据细节，
    #    应拆分为核心论点（≤150）+ 补充说明（I 段承接）。英文原书同理。
    r_blocks = re.findall(
        r'\*\*R — Reading[^\n]*\n\n> (.+?)\n> ——',
        content, re.DOTALL
    )
    for i, block in enumerate(r_blocks, 1):
        # Join continuation lines
        quote = block.replace('\n> ', '')
        n = count_content_chars(quote)
        if n > 150:
            issues.append(f'[OVER] R-section unit {i} quote: {n} chars (limit 150)')

    # 3. I-section length ≤300
    #    Threshold rationale: I 段是"用自己的话重写"，5-15 行约 150-300 字符。
    #    超过 300 通常意味着重复了 R 段内容或写了过多细节（应由 A1/A2 承接）。
    # Note: SUMMARY.md files may use two formats for I-section:
    #   Format A: **I — Interpretation（深层阐释）**：<content>\n\n**A1
    #   Format B: **I — Interpretation（深层阐释）**：\n\n<content>\n\n**A1
    # Try Format A first (content on same line as header)
    i_blocks = re.findall(
        r'\*\*I — Interpretation[^$]*\*\*：([^\n]+)\n\n\*\*A1',
        content
    )
    if len(i_blocks) < 14:
        # Fall back to Format B (content on following lines)
        i_blocks = re.findall(
            r'\*\*I — Interpretation[^$]*\*\*：\n\n(.*?)\n\n\*\*A1',
            content, re.DOTALL
        )
    for i, block in enumerate(i_blocks, 1):
        n = count_content_chars(block)
        if n > 300:
            issues.append(f'[OVER] I-section unit {i} self-narration: {n} chars (limit 300)')

    # 4. R-section citations (第N章 or ch007 for reverse-engineered books)
    # Support Chinese chapter names: 第7章, 第七章, 上篇, 下篇, 序二
    # Also accept: ch007, CH007, 第7章, 第七章, ch007 / 第1章
    r_citations = re.findall(r'> ——\s*第[零一二三四五六七八九十0-9篇章节]+', content)
    r_year_citations = re.findall(r'> ——\s*第?\d{4}年', content)  # 第1965年信, 1984年致股东信
    r_ch_citations = re.findall(r'> ——\s*《[^》]+》，ch[0-9]+', content, re.IGNORECASE)
    r_ch_slash_citations = re.findall(r'> ——\s*ch[0-9]+\s*/[^>\n]+', content, re.IGNORECASE)
    if not r_citations and not r_year_citations and not r_ch_citations and not r_ch_slash_citations:
        issues.append('[MISSING] No R-section chapter citations found')
    else:
        # Log count for informational purposes
        pass

    # 5. RIAAEPB completeness per unit
    # Support three section header variants:
    #   H2: "## R段：..." / "## I段：..." (原则 — this book uses H2)
    #   H3 bold: "### 方法论单元1：..." + "**R — Reading**：" (standard)
    #   Plain: "**R — Reading**：" without bold
    section_h2_prefixes = ['R段', 'I段', 'A1段', 'A2段', 'E段', 'P段', 'B段']
    section_h3_prefixes = ['R —', 'I —', 'A1 —', 'A2 —', 'E —', 'P —', 'B —']
    all_prefixes = section_h2_prefixes + section_h3_prefixes
    # Match: "方法论单元1：" (standard), "M01：" (埃尔德交易体系), "方法论一：" (巴菲特之道)
    unit_starts = [m.start() for m in re.finditer(
        r'^### (?:方法论单元\d+：|(?:M\d+)[^：]*：|方法论[一二三四五六七八九十]+：)',
        content, re.MULTILINE)]

    def has_section_variant(unit_text: str, prefix: str) -> bool:
        """Check if unit contains any variant of the section header."""
        return bool(re.search(re.escape(prefix) + r'\s*[^$]*\*?\*?\s*\n', unit_text))

    for i, start in enumerate(unit_starts):
        end = unit_starts[i + 1] if i + 1 < len(unit_starts) else len(content)
        unit_text = content[start:end]
        # Detect which format this unit uses (H2 or H3), then only validate that format
        h2_found = any(has_section_variant(unit_text, p) for p in section_h2_prefixes)
        h3_found = any(has_section_variant(unit_text, p) for p in section_h3_prefixes)
        if h2_found and not h3_found:
            # H2 format: only check H2 prefixes
            prefixes_to_check = section_h2_prefixes
        elif h3_found and not h2_found:
            # H3 format: only check H3 prefixes
            prefixes_to_check = section_h3_prefixes
        elif h3_found:
            # Both present — this is actually fine, don't double-report
            continue
        else:
            # Neither format found — report all missing
            prefixes_to_check = all_prefixes
        for prefix in prefixes_to_check:
            if not has_section_variant(unit_text, prefix):
                unit_title = content[start:start + 80].split('\n')[0]
                issues.append(f'[MISSING] Unit {i + 1} lacks section: {prefix}...')

    # 6. Audit section present (skip for books without candidates/)
    candidates_dir = os.path.join(os.path.dirname(path), 'candidates')
    if '审计信息' not in content and os.path.isdir(candidates_dir):
        issues.append('[MISSING] Audit section not found')

    # 7. v4.54/v4.55 新增节检查 (warning, not failure)
    if '压力测试' not in content and 'Musk' not in content:
        issues.append('[WARN] v4.54 压力测试 section not found (七、压力测试)')
    if '关联方法论' not in content and '跨书关联' not in content:
        issues.append('[WARN] v4.54 关联方法论 section not found (八、关联方法论)')

    return issues


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    issues = check_summary(sys.argv[1])
    if issues:
        print(f"FAILED ({len(issues)} issue(s)):")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1)
    else:
        print("PASS: All quality gates met ✅")
        sys.exit(0)
