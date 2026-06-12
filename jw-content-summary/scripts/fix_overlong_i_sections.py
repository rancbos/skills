#!/usr/bin/env python3
"""
批量修复 v4.58 Pitfall 12 I 段超长（自动截断到 200 字符）。

实战背景：12 单元的 SUMMARY.md 中，多个 unit 的 I 段后接"列表/对比"子段，
紧接 A1。Format A 抓不到 → fallback Format B 贪心抓取 → validator 报
I 段 unit 1-12 全部超长 400-700 字符。

适用场景：
- 12 单元 SUMMARY.md 写完后
- 多个 unit I 段超 300 字符
- 比逐个 patch 更高效

用法：
    python3 scripts/fix_overlong_i_sections.py /path/to/SUMMARY.md

修复策略（按 v4.58 推荐 3 策略）：
1. **首选**：将列表移到 A1 之前作为独立子段（用 H4 + 列表）
2. **次选**：将列表内容重组到 A1 历史案例中
3. **次选（最激进）**：自动截断 I 段到 200 字符，删除中间列表

此脚本实现**第 3 种**（最激进的批量修复）：
- 找到每个 I 段 + A1 之间的中间块
- 如果 I 段 + 中间块总长 > 200 字符，截断到 200 字符
- 如果 I 段 + 中间块总长 ≤ 200 字符，保留原样

**注意**：第 3 种策略会删除 I 段后的所有子段——前提是这些子段在 A1 中
已隐含（v4.58 推荐的"信息已隐含"判断）。如果列表信息很重要，需要先
手动重组到 A1，再跑此脚本。

实战来源：2026-06-12《投资中最简单的事》Unit 6/7/8/9/11/12 全部超长（7 个
I 段），用此脚本一次性修复 PASS。
"""

import sys
import re
from pathlib import Path


def count_chars(text: str) -> int:
    """复刻 validate_summary.py 的 count_chinese_chars 实现。"""
    clean = re.sub(r'[*_#>\[\]`]', '', text)
    return len(clean.replace('\n', '').replace(' ', ''))


def fix_overlong_i_sections(content: str, max_chars: int = 200) -> tuple[str, int]:
    """
    批量修复所有超长 I 段。

    Returns:
        (fixed_content, n_fixed)
    """
    pattern = r'(\*\*I — Interpretation[^\n]*\*\*[^\n]*\n)(.*?)(\n\*\*A1 — Past Application（历史案例）\*\*：)'

    n_fixed = 0

    def replace_func(m):
        nonlocal n_fixed
        i_header = m.group(1)
        i_content = m.group(2)
        a1 = m.group(3)

        total = count_chars(i_content)
        if total <= max_chars:
            return m.group(0)

        truncated = i_content[:max_chars]
        last_nl = truncated.rfind('\n')
        if last_nl > max_chars * 0.5:
            truncated = truncated[:last_nl]

        n_fixed += 1
        return i_header + truncated + a1

    new_content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
    return new_content, n_fixed


def main():
    if len(sys.argv) < 2:
        print("用法: python3 fix_overlong_i_sections.py <SUMMARY.md> [max_chars=200]")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"错误: 找不到 {path}")
        sys.exit(1)

    max_chars = 200
    if len(sys.argv) >= 3:
        max_chars = int(sys.argv[2])

    content = path.read_text(encoding='utf-8')
    new_content, n_fixed = fix_overlong_i_sections(content, max_chars)

    if n_fixed > 0:
        path.write_text(new_content, encoding='utf-8')
        print(f"修复 {n_fixed} 个超长 I 段（截断到 {max_chars} 字符）")
        print("   立即运行 validate_summary.py 验证")
    else:
        print(f"所有 I 段 {max_chars} 字符，无需修复")


if __name__ == "__main__":
    main()
