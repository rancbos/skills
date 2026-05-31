#!/usr/bin/env python3
"""
md_to_html.py — 将 SUMMARY.md 转换为带样式的 HTML 文件。

用法:
    python md_to_html.py <path_to_summary_md> [output_dir]

输出: <output_dir>/SUMMARY.html（与 SUMMARY.md 同目录）
"""

import sys
import pathlib

try:
    import markdown
except ImportError:
    print("ERROR: python-markdown not installed. Run: pip install markdown")
    sys.exit(1)

# 嵌入式 CSS 样式 — 基于 GitHub 风格，稍微调整适合阅读长文
CSS = """
<style>
  :root {
    --bg: #ffffff;
    --text: #24292f;
    --blockquote-border: #d8e0e8;
    --code-bg: #f6f8fa;
    --hr: #e1e4e8;
    --a: #0969da;
    --h1-border: #d8e0e8;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0d1117;
      --text: #c9d1d9;
      --blockquote-border: #30363d;
      --code-bg: #161b22;
      --hr: #30363d;
      --a: #58a6ff;
      --h1-border: #30363d;
    }
  }
  body {
    font-family: var(--font-sans);
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    font-size: 16px;
  }
  h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
    line-height: 1.25;
  }
  h1 {
    font-size: 1.6em;
    border-bottom: 1px solid var(--h1-border);
    padding-bottom: 0.3em;
  }
  h2 { font-size: 1.3em; }
  h3 { font-size: 1.1em; }
  a { color: var(--a); text-decoration: none; }
  a:hover { text-decoration: underline; }
  blockquote {
    margin: 1em 0;
    padding: 0.5em 1em;
    border-left: 4px solid var(--blockquote-border);
    color: #6e7781;
  }
  code {
    font-family: var(--font-mono);
    font-size: 0.875em;
    background: var(--code-bg);
    padding: 0.2em 0.4em;
    border-radius: 4px;
  }
  pre code {
    display: block;
    padding: 1em;
    overflow-x: auto;
  }
  hr {
    border: none;
    border-top: 1px solid var(--hr);
    margin: 2em 0;
  }
  ul, ol { padding-left: 1.5em; }
  li { margin: 0.25em 0; }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
  }
  table th, table td {
    border: 1px solid var(--hr);
    padding: 0.4em 0.8em;
    text-align: left;
  }
  table th { background: var(--code-bg); font-weight: 600; }
  strong { font-weight: 600; }
  em { font-style: italic; }
  /* 方法论单元样式 */
  .methodology-unit {
    margin: 2em 0;
    padding: 1em 1.2em;
    border: 1px solid var(--hr);
    border-radius: 6px;
  }
  .methodology-unit h3 {
    margin-top: 0;
    color: var(--a);
  }
  .section-label {
    font-size: 0.8em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #6e7781;
    margin-right: 0.5em;
  }
  .audit-info {
    font-size: 0.85em;
    color: #6e7781;
    border-top: 1px solid var(--hr);
    padding-top: 1em;
    margin-top: 2em;
  }
</style>
"""

HTML_WRAPPER = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{CSS}
</head>
<body>
<article class="summary">
{content}
</article>
</body>
</html>"""


def md_to_html(md_path: str, output_dir: str | None = None) -> str:
    md_path = pathlib.Path(md_path).resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"Source file not found: {md_path}")

    if output_dir:
        out_dir = pathlib.Path(output_dir)
    else:
        out_dir = md_path.parent

    html_path = out_dir / f"{md_path.stem}.html"

    raw_md = md_path.read_text(encoding="utf-8")

    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "nl2br",
            "sane_lists",
            "toc",
        ],
        extension_configs={
            "toc": {"title": "目录", "toc_depth": 2}
        },
    )
    html_body = md.convert(raw_md)

    # 提取标题用于 <title>
    first_line = raw_md.split("\n", 1)[0].lstrip("# ").strip()
    title = first_line if first_line else md_path.stem

    html_full = HTML_WRAPPER.format(
        title=title,
        CSS=CSS,
        content=html_body,
    )

    html_path.write_text(html_full, encoding="utf-8")
    return str(html_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    md_file = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = md_to_html(md_file, out_dir)
        print(f"OK: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)