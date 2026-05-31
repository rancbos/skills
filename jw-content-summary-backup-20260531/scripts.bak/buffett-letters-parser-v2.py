#!/usr/bin/env python3
"""
巴菲特致股东的信 — 章节提取脚本v2
策略：找所有"第X章"标题，过滤掉目录区（前856行），从第二册正文开始提取
"""
import sys, re, json, os

def is_chapter_heading(line):
    return bool(re.match(r'^第[一二三四五六七八九十百千万\d]+章[　\s]', line))

def extract_chapters(filepath, out_dir):
    with open(filepath, encoding='utf-8') as f:
        lines = f.read().splitlines()

    # 找所有章节标题
    all_headings = []
    for i, line in enumerate(lines):
        if is_chapter_heading(line.strip()):
            all_headings.append((i, line.strip()))

    print(f"Total chapter headings found: {len(all_headings)}")
    for idx, (ln, t) in enumerate(all_headings):
        print(f"  [{idx}] line {ln+1}: {t}")

    # 确定正文起始点：第一个"第1章"出现在856行之后
    body_start_idx = None
    for idx, (ln, title) in enumerate(all_headings):
        if ln > 856 and '第1章' in title:
            body_start_idx = idx
            break

    if body_start_idx is None:
        print("ERROR: Could not find body start")
        return None

    print(f"\nBody starts at heading index {body_start_idx}: line {all_headings[body_start_idx][0]+1}")

    # 从body_start_idx到末尾的所有标题
    body_headings = all_headings[body_start_idx:]
    print(f"Body headings count: {len(body_headings)}")

    # 构建章节
    chapters = []
    for idx, (start_line, start_title) in enumerate(body_headings):
        end_line = body_headings[idx+1][0] if idx+1 < len(body_headings) else len(lines)
        body = '\n'.join(lines[start_line:end_line]).strip()
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

    print(f"\nTotal chapters: {len(chapters)}")
    for c in chapters:
        print(f"  {c['id']}: {c['title']} ({c['char_count']} chars, lines {c['start_line']}-{c['end_line']})")

    # 写book-index.json
    data = {
        'source': filepath,
        'total_chars': sum(c['char_count'] for c in chapters),
        'chapter_count': len(chapters),
        'chapters': chapters
    }
    out_json = f"{out_dir}/book-index.json"
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_json}")

    # 写章节文件
    chapters_dir = f"{out_dir}/chapters"
    os.makedirs(chapters_dir, exist_ok=True)
    for c in chapters:
        with open(f"{chapters_dir}/{c['id']}.txt", 'w', encoding='utf-8') as f:
            f.write(c['text'])
    print(f"Wrote {len(chapters)} chapter files")

    return chapters

if __name__ == '__main__':
    filepath = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    extract_chapters(filepath, out_dir)