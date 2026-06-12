#!/usr/bin/env python3
"""
批量修复 SUMMARY.md 中的章节引用格式（v4.60 Pitfall）。

实战背景：SUMMARY.md 写完后，validator 报 `[MISSING] No R-section chapter
citations found`。根因：章节引用未使用 validator 正则要求的标准格式。

validator 正则（v4.60 修复后）：
    r'> ——\s*第[零一二三四五六七八九十0-9篇章节]+'

要求：
1. 必须以 "> ——" 开头
2. 紧跟"第"字（无空格）
3. 数字+章/篇/讲/部分（无空格）
4. 支持中文数字（一二三四五六七八九十）和阿拉伯数字（0-9）

实战常见错误格式：
- `> ——邱国鹭/2017.03，第1章` （作者/时间/职位在第N章前）
- `> ——邱国鹭，2017.03，第1章` （作者/时间在第N章前）
- `> ——《投资中最简单的事》` （无章节号）
- `> ——（第1章）` （章节号在括号内）

正确格式（v4.60 实战验证）：
- `> ——第1章（邱国鹭）` （章节号开头 + 作者在括号）
- `> ——第1章` （最简）
- `> ——第N讲` / `> ——第N部分` / `> ——第N篇`

用法：
    python3 scripts/fix_chapter_citations.py /path/to/SUMMARY.md

修复策略（按优先级）：
1. `> ——<作者>/<时间>，<职位>，第N章` → `> ——第N章（<作者>）`
2. `> ——<作者>，<时间>，第N章` → `> ——第N章（<作者>）`
3. `> ——<作者>，第N章` → `> ——第N章（<作者>）`
4. `> ——<书名>`（无章节号）→ `> ——第N章（<作者>）`（需手动指定 N）

实战来源：2026-06-12《投资中不简单的事》+《投资中最简单的事》两本书都遇到
`> ——邱国鹭，第N章` 格式 → 12 处引用全部 0 匹配 → 修复后 12 处 PASS。
"""

import sys
import re
from pathlib import Path


def count_citations(content: str) -> int:
    """统计符合 validator 正则的章节引用数。"""
    return len(re.findall(r'> ——\s*第[零一二三四五六七八九十0-9篇章节]+', content))


def fix_chapter_citations(content: str) -> tuple[str, int]:
    """
    批量修复章节引用格式。

    Returns:
        (fixed_content, n_fixed)
    """
    n_fixed = 0
    original = content

    # 模式 1: > ——<作者>/<时间>，<职位>，第N章 → > ——第N章（<作者>）
    pattern1 = r'> ——(.+?)/([0-9]{4}\.[0-9]{2}?)，([^，]+?)，第([0-9]+)章'
    content = re.sub(pattern1, r'> ——第\4章（\1）', content)
    n_fixed += len(re.findall(pattern1, original))

    # 模式 2: > ——<作者>，<时间>，第N章 → > ——第N章（<作者>）
    pattern2 = r'> ——(.+?)，([0-9]{4}\.[0-9]{2}?)，第([0-9]+)章'
    content = re.sub(pattern2, r'> ——第\3章（\1）', content)

    # 模式 3: > ——<作者>，第N章 → > ——第N章（<作者>） （最常见）
    pattern3 = r'> ——(.+?)，第([0-9]+)章'
    content = re.sub(pattern3, r'> ——第\2章（\1）', content)

    # 模式 4: 修复"章 N" → "第N章"（中间空格）
    content = re.sub(r'第 (\d+) 章', r'第\1章', content)

    # 模式 5: > ——<书名> （无章节号）→ 保留（不修复，需手动指定章节）

    return content, n_fixed


def main():
    if len(sys.argv) < 2:
        print("用法: python3 fix_chapter_citations.py <SUMMARY.md>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"错误: 找不到 {path}")
        sys.exit(1)

    content = path.read_text(encoding='utf-8')
    before_count = count_citations(content)
    new_content, n_fixed = fix_chapter_citations(content)
    after_count = count_citations(new_content)

    if n_fixed > 0 or before_count != after_count:
        path.write_text(new_content, encoding='utf-8')
        print(f"修复章节引用: {before_count} → {after_count} 处")
        print("   立即运行 validate_summary.py 验证")
    else:
        print(f"章节引用已正确: {after_count} 处")


if __name__ == "__main__":
    main()
