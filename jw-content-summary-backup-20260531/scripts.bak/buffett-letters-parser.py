#!/usr/bin/env python3
"""
巴菲特致股东的信 — 章节提取脚本
特殊处理：跳过目录区（两册各一套TOC），直接提取正文章节
"""
import sys, re, json

def extract_buffett_letters_chapters(filepath):
    with open(filepath, encoding='utf-8') as f:
        text = f.read()

    lines = text.splitlines()

    # 策略：找"第一章"在正文中第一次出现有意义段落后的地方
    # 两册的正文章节标题都出现在"年平均投资收益"这类段落之后
    # 而目录区的章节标题前是空白或只有"第X章"

    # 我们直接找所有"第X章"位置，然后判断哪个是真正的正文起点
    chapter_pattern = re.compile(r'^第([一二三四五六七八九十百千万\d]+)章[　\s]')

    all_headings = []
    for i, line in enumerate(lines):
        m = chapter_pattern.match(line.strip())
        if m:
            all_headings.append((i, line.strip()))

    print(f"Found {len(all_headings)} chapter headings")
    for idx, (line_no, title) in enumerate(all_headings[:20]):
        print(f"  [{idx}] line {line_no+1}: {title}")

    # 关键启发：正文第一章之前应该有"年平均投资收益"这段引言
    # 找第一个"年平均投资收益"之后出现的"第1章"，那才是正文
    intro_anchor = None
    for i, line in enumerate(lines):
        if '年平均投资收益' in line or 'Lessons for Investors' in line:
            intro_anchor = i
            break

    print(f"\nIntro anchor (first 'Lessons for Investors' or '年平均投资收益'): line {intro_anchor+1 if intro_anchor else 'NOT FOUND'}")

    # 正文起始点：intro_anchor 之后最近的"第1章"
    if intro_anchor is not None:
        real_start = None
        for line_no, title in all_headings:
            if line_no > intro_anchor and '第1章' in title:
                real_start = line_no
                break
        print(f"Real body starts at line {real_start+1 if real_start else 'NOT FOUND'}: {[t for l,t in all_headings if l == real_start]}")

    # 用正文区重建章节：从 real_start 开始，每两个"第X章"之间是一个章节
    if intro_anchor is None:
        print("ERROR: Could not find intro anchor")
        return None

    # 收集intro_anchor之后的所有章节标题
    body_headings = [(ln, t) for ln, t in all_headings if ln >= intro_anchor]
    print(f"\nBody headings (from intro_anchor): {len(body_headings)}")
    for h in body_headings[:10]:
        print(f"  line {h[0]+1}: {h[1]}")

    # 构建章节：相邻两个标题之间是一个章节
    chapters = []
    for idx, (start_line, start_title) in enumerate(body_headings):
        end_line = body_headings[idx+1][0] if idx+1 < len(body_headings) else len(lines)
        body_lines = lines[start_line:end_line]
        body = '\n'.join(body_lines).strip()
        if len(body) < 100:
            continue
        ch_num = idx + 1
        chapters.append({
            'id': f'ch{ch_num:03d}',
            'title': start_title,
            'text': body,
            'char_count': len(body),
            'start_line': start_line + 1,
            'end_line': end_line + 1
        })

    print(f"\nTotal chapters extracted: {len(chapters)}")
    for c in chapters[:5]:
        print(f"  {c['id']}: {c['title']} ({c['char_count']} chars, lines {c['start_line']}-{c['end_line']})")

    return chapters

if __name__ == '__main__':
    filepath = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else '.'

    chapters = extract_buffett_letters_chapters(filepath)
    if chapters:
        data = {
            'source': filepath,
            'total_chars': sum(c['char_count'] for c in chapters),
            'chapter_count': len(chapters),
            'chapters': chapters
        }
        out_json = f"{out_dir}/book-index.json"
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {out_json}")

        # 写章节文件
        import os
        chapters_dir = f"{out_dir}/chapters"
        os.makedirs(chapters_dir, exist_ok=True)
        for c in chapters:
            with open(f"{chapters_dir}/{c['id']}.txt", 'w', encoding='utf-8') as f:
                f.write(c['text'])
        print(f"Wrote {len(chapters)} chapter files to {chapters_dir}")