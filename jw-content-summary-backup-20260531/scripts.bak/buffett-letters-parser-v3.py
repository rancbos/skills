#!/usr/bin/env python3
"""
巴菲特致股东的信 — 章节提取脚本 v3
找到正文第二册的第一章（line 858），提取9个正文章节
"""
import sys, re, json, os

def is_chapter_heading(line):
    return bool(re.match(r'^第[一二三四五六七八九十百千万\d]+章[　\s]', line.strip()))

def extract_chapters(filepath, out_dir):
    with open(filepath, encoding='utf-8') as f:
        lines = f.read().splitlines()

    all_headings = []
    for i, line in enumerate(lines):
        if is_chapter_heading(line.strip()):
            all_headings.append((i, line.strip()))

    print(f"Total chapter headings: {len(all_headings)}")
    for idx, (ln, t) in enumerate(all_headings):
        print(f"  [{idx}] line {ln+1}: {t}")

    # 正文从第二册开始（line 858 = index 857）
    # body_headings 是从 index 9（第二册第1章）到末尾
    body_start_idx = 9  # all_headings[9] is line 858
    body_headings = all_headings[body_start_idx:]
    print(f"\nUsing body headings from index {body_start_idx}: {len(body_headings)} headings")
    for h in body_headings:
        print(f"  line {h[0]+1}: {h[1]}")

    chapters = []
    for idx, (start_line, start_title) in enumerate(body_headings):
        end_line = body_headings[idx+1][0] if idx+1 < len(body_headings) else len(lines)
        body = '\n'.join(lines[start_line:end_line]).strip()
        if len(body) < 100:
            continue
        chapters.append({
            'id': f'ch{idx+1:03d}',
            'title': start_title,
            'text': body,
            'char_count': len(body),
            'start_line': start_line + 1,
            'end_line': end_line + 1
        })

    print(f"\nTotal chapters: {len(chapters)}")
    for c in chapters:
        print(f"  {c['id']}: {c['title']} ({c['char_count']} chars)")

    data = {
        'source': filepath,
        'total_chars': sum(c['char_count'] for c in chapters),
        'chapter_count': len(chapters),
        'chapters': chapters
    }
    out_json = f"{out_dir}/book-index.json"
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    chapters_dir = f"{out_dir}/chapters"
    os.makedirs(chapters_dir, exist_ok=True)
    for c in chapters:
        with open(f"{chapters_dir}/{c['id']}.txt", 'w', encoding='utf-8') as f:
            f.write(c['text'])

    print(f"\nDone. Wrote {len(chapters)} chapters to {chapters_dir}")
    return chapters

if __name__ == '__main__':
    extract_chapters(sys.argv[1], sys.argv[2])