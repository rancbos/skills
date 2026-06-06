#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
横纵分析法报告质检脚本。

检查项：
1. 字数范围（固定阈值 10,000-25,000 字）
2. 禁区词汇（与 SKILL.md 绝对禁区保持一致）
3. 信息来源标注
4. 章节结构完整性

使用方法：
  python3 quality_check.py <markdown_file> [--verbose]

注意：质检是最终确认手段，不是发现禁区词的主要手段。
先手动用 search_files 扫描禁区词，再用本脚本做最终确认。

退出码语义：
  0 = 通过（可能有 warning，但不阻塞交付）
  1 = 存在必须修复的 error
"""

import argparse
import re
import sys
from pathlib import Path


# === 禁区词汇列表（与 SKILL.md 绝对禁区严格一致） ===
# 修改此列表时，必须同步修改 SKILL.md 的"绝对禁区"章节

# 套话
PHRASE_BANAL = ["首先", "其次", "最后", "综上所述", "值得注意的是", "不难发现"]

# 空洞形容词
PHRASE_HOLLOW = ["赋能", "抓手", "打造闭环"]

# 教科书开头
PHRASE_TEXTBOOK = ["在当今AI快速发展的时代", "随着技术的不断进步"]

# 高频踩雷词
PHRASE_Cliche = ["说白了", "意味着什么", "这意味着", "本质上", "换句话说", "不可否认"]

# 空泛工具名
PHRASE_VAGUE = ["AI工具", "某个模型"]

# 汇总
FORBIDDEN_WORDS = PHRASE_BANAL + PHRASE_HOLLOW + PHRASE_TEXTBOOK + PHRASE_Cliche + PHRASE_VAGUE

# 报告结构性禁区（需要上下文判断，只做弱提示）
STRUCTURAL_WARNINGS = [
    "年表流水账",
    "空洞概括",
]

# 必需章节
REQUIRED_SECTIONS = [
    "纵向分析",
    "横向分析",
    "横纵交汇",
    "信息来源",
]

# 信息来源标记
SOURCE_PATTERNS = [
    r"https?://",  # URL
    r"来源[:：]",
    r"参考[:：]",
    r"引用[:：]",
    r"据.*报道",
    r"根据.*",
]


def count_chinese_chars(text: str) -> int:
    """统计中文字符数（含中文标点）。"""
    chinese_chars = re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text)
    return len(chinese_chars)


def count_words(text: str) -> int:
    """统计总字数（中文字符 + 英文单词）。"""
    chinese_count = count_chinese_chars(text)
    # 移除中文后统计英文单词
    text_without_chinese = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', ' ', text)
    english_words = len(re.findall(r'\b[a-zA-Z]+', text_without_chinese))
    return chinese_count + english_words


def check_forbidden_words(content: str, verbose: bool = False) -> list:
    """检查禁区词汇。"""
    issues = []
    for word in FORBIDDEN_WORDS:
        count = content.count(word)
        if count > 0:
            issues.append(f"❌ 发现禁区词汇「{word}」出现 {count} 次")
            if verbose:
                # 找出具体位置
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if word in line:
                        issues.append(f"   第 {i} 行: ...{line[:80]}...")
    return issues


def check_structural_warnings(content: str) -> list:
    """检查结构性禁区（弱提示，不阻塞交付）。"""
    issues = []
    for phrase in STRUCTURAL_WARNINGS:
        if phrase in content:
            issues.append(f"⚠️ 疑似结构性问题「{phrase}」，请人工确认")
    return issues


def check_sections(content: str) -> list:
    """检查章节结构完整性。"""
    issues = []
    for section in REQUIRED_SECTIONS:
        if section not in content:
            issues.append(f"❌ 缺少必需章节「{section}」")
    return issues


def check_sources(content: str) -> list:
    """检查信息来源标注。"""
    issues = []
    has_sources = False
    for pattern in SOURCE_PATTERNS:
        if re.search(pattern, content):
            has_sources = True
            break
    if not has_sources:
        issues.append("⚠️ 未发现信息来源标注（URL或来源说明）")
    return issues


def check_word_count(content: str, verbose: bool = False) -> list:
    """检查字数范围。"""
    issues = []
    word_count = count_words(content)

    if verbose:
        print(f"📊 总字数: {word_count}")

    if word_count < 10000:
        issues.append(f"⚠️ 字数偏少（{word_count}字），建议至少 10,000 字以保证深度")
    elif word_count > 25000:
        issues.append(f"⚠️ 字数偏多（{word_count}字），建议精简至 25,000 字以内以提高可读性")

    return issues


def check_quality(content: str, verbose: bool = False) -> tuple:
    """执行所有质检项。"""
    all_issues = []

    # 1. 禁区词汇（error）
    forbidden_issues = check_forbidden_words(content, verbose)
    all_issues.extend(forbidden_issues)

    # 2. 结构性禁区（warning）
    structural_issues = check_structural_warnings(content)
    all_issues.extend(structural_issues)

    # 3. 章节结构（error）
    section_issues = check_sections(content)
    all_issues.extend(section_issues)

    # 4. 信息来源（warning）
    source_issues = check_sources(content)
    all_issues.extend(source_issues)

    # 5. 字数范围（warning）
    word_issues = check_word_count(content, verbose)
    all_issues.extend(word_issues)

    # 统计
    error_count = sum(1 for i in all_issues if i.startswith("❌"))
    warning_count = sum(1 for i in all_issues if i.startswith("⚠️"))

    return all_issues, error_count, warning_count


def main():
    parser = argparse.ArgumentParser(description='横纵分析法报告质检')
    parser.add_argument('input', help='Markdown文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息（禁区词位置）')

    args = parser.parse_args()

    # 读取文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 执行质检
    print(f"📝 检查文件: {input_path.name}")
    print("=" * 50)

    issues, error_count, warning_count = check_quality(content, args.verbose)

    # 输出结果
    if issues:
        print("\n发现以下问题:\n")
        for issue in issues:
            print(issue)
    else:
        print("\n✅ 所有检查项通过！")

    # 汇总
    print("\n" + "=" * 50)
    print(f"📊 质检结果: {error_count} 个错误, {warning_count} 个警告")

    if error_count > 0:
        print("❌ 存在必须修复的问题，请修改后重新检查")
        sys.exit(1)
    elif warning_count > 0:
        print("⚠️ 存在建议优化的项目，可酌情处理（不阻塞交付，但必须告知用户）")
        sys.exit(0)
    else:
        print("✅ 质检通过，可以交付")
        sys.exit(0)


if __name__ == '__main__':
    main()
