#!/usr/bin/env python3
"""
check_i_section_capture.py
诊断 SUMMARY.md 的 I 段是否会被 Format B fallback 跨 unit 误捕获。
v4.60 新增：用于检测 v4.58 Pitfall 12（I 段后接列表）+ v4.59 重组副作用。

用法：
  python3 scripts/check_i_section_capture.py <SUMMARY.md>
  python3 scripts/check_i_section_capture.py <dir>/              # 检查目录下所有 SUMMARY.md
  python3 scripts/check_i_section_capture.py                       # 检查默认 /root/books 下所有书的 SUMMARY.md

输出：
  - Format A 匹配数（inline 格式的 I 段数）
  - Format B fallback 匹配数 + 每个 block 字符数
  - OVER 300 字符的 block 详细列出（哪个 unit 的 I 段超长）
  - 修复建议

实战 2026-06-12：4 本书全部命中（unit 1 报超长但实际是 unit 10-12 误捕获）。
"""

import re
import sys
from pathlib import Path


def count_chinese_chars(text: str) -> int:
    """与 validate_summary.py 兼容的字符计数（与 SKILL 中描述的 count_chinese_chars 一致）。"""
    clean = re.sub(r'[*_#>\[\]`]', '', text)
    return len(clean.replace('\n', '').replace(' ', ''))


def analyze_i_sections(content: str):
    """分析 I 段抓取情况，返回 (format_a_count, format_b_blocks, over_blocks)。"""
    # Format A: inline 格式 - header 同行有内容
    format_a_pattern = r'\*\*I — Interpretation[^$]*\*\*：([^\n]+)\n\n\*\*A1'
    format_a_blocks = re.findall(format_a_pattern, content)

    # Format B: 独立行格式 - header 后换行
    format_b_pattern = r'\*\*I — Interpretation[^$]*\*\*：\n\n(.*?)\n\n\*\*A1'
    format_b_blocks = re.findall(format_b_pattern, content, re.DOTALL)

    over_blocks = []
    for i, b in enumerate(format_b_blocks, 1):
        n = count_chinese_chars(b)
        if n > 300:
            over_blocks.append((i, n, b))

    return len(format_a_blocks), format_b_blocks, over_blocks


def find_unit_boundaries(content: str):
    """定位每个方法论单元的标题行号，用于报告"超长 I 段属于哪个 unit"。"""
    boundaries = []
    for m in re.finditer(r'^## 方法论单元[一二三四五六七八九十]+：', content, re.MULTILINE):
        line_no = content[:m.start()].count('\n') + 1
        title = m.group(0)
        # 找下一个 R/I 段位置估算实际 I 段位置
        # 这里我们标记 unit 标题位置
        boundaries.append((line_no, title))
    return boundaries


def find_over_block_location(content: str, over_block_text: str):
    """找到超长 I 段块的位置（行号 + 所在 unit）。"""
    # 找 I 段 header
    pattern = r'\*\*I — Interpretation[^$]*\*\*：\n\n.*?\n\n\*\*A1'
    for m in re.finditer(pattern, content, re.DOTALL):
        if m.group(0) == over_block_text or over_block_text in m.group(0):
            line_no = content[:m.start()].count('\n') + 1
            # 找最近的 unit 标题
            unit = "未知"
            for uline, utitle in find_unit_boundaries(content):
                if uline <= line_no:
                    unit = utitle
                else:
                    break
            return line_no, unit
    return None, None


def analyze_file(summar_md_path: Path):
    """分析单个 SUMMARY.md 文件。"""
    print(f"\n{'=' * 80}")
    print(f"文件：{summar_md_path}")
    print('=' * 80)

    if not summar_md_path.exists():
        print(f"  ❌ 文件不存在")
        return False

    try:
        content = summar_md_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ❌ 读取失败：{e}")
        return False

    # 基本信息
    unit_count = len(re.findall(r'^## 方法论单元[一二三四五六七八九十]+：', content, re.MULTILINE))
    r_count = len(re.findall(r'^\*\*R — Reading', content, re.MULTILINE))
    i_count = len(re.findall(r'^\*\*I — Interpretation', content, re.MULTILINE))
    a1_count = len(re.findall(r'^\*\*A1 — Past Application', content, re.MULTILINE))
    a2_count = len(re.findall(r'^\*\*A2 — Future Application', content, re.MULTILINE))
    e_count = len(re.findall(r'^\*\*E — Exception', content, re.MULTILINE))
    p_count = len(re.findall(r'^\*\*P — Procedure', content, re.MULTILINE))
    b_count = len(re.findall(r'^\*\*B — Belief', content, re.MULTILINE))
    citation_count = len(re.findall(r'> ——\s*第[零一二三四五六七八九十0-9篇章节]+', content))
    has_audit = '审计信息' in content

    print(f"\n  单元数：{unit_count}")
    print(f"  R 段数：{r_count} | I 段数：{i_count} | A1：{a1_count} | A2：{a2_count} | E：{e_count} | P：{p_count} | B：{b_count}")
    print(f"  章节引用：{citation_count}")
    print(f"  审计信息字面量：{'✓' if has_audit else '❌'}")

    # I 段分析
    fa_count, fb_blocks, over_blocks = analyze_i_sections(content)
    print(f"\n  Format A 匹配（inline I 段）：{fa_count}")
    print(f"  Format B fallback 匹配：{len(fb_blocks)}")

    if over_blocks:
        print(f"\n  ❌ 发现 {len(over_blocks)} 个超长 I 段 block（>300 字符）：")
        for idx, n, text in over_blocks:
            line_no, unit = find_over_block_location(content, text)
            preview = text[:200].replace('\n', ' ')
            print(f"\n    Block {idx}（{n} 字符）: 位于第 {line_no or '?'} 行，unit：{unit or '?'}")
            print(f"    预览：{preview}...")
            print(f"    修复建议：")
            print(f"      - 将列表/对比内容重组到 A1 段（首选）")
            print(f"      - 删除 I 段后的'对比'子段（次选）")
            print(f"      - 合并列表到 I 段单行（次选）")
        return False
    else:
        print(f"\n  ✅ 所有 I 段 ≤300 字符")
        return True


def main():
    if len(sys.argv) < 2:
        # 默认扫描 /root/books
        target = Path('/root/books')
    else:
        target = Path(sys.argv[1])

    files = []
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.rglob('SUMMARY.md'))
    else:
        print(f"路径不存在：{target}")
        sys.exit(1)

    if not files:
        print(f"未找到 SUMMARY.md")
        sys.exit(1)

    print(f"扫描 {len(files)} 个 SUMMARY.md")
    all_pass = True
    for f in files:
        if not analyze_file(f):
            all_pass = False

    print(f"\n{'=' * 80}")
    print(f"总结：{'✅ 全部 PASS' if all_pass else '❌ 有文件需要修复'}")
    print('=' * 80)
    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()
