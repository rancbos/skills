#!/usr/bin/env python3
"""
Markdown to PDF converter with beautiful formatting for research reports.
Based on WeasyPrint with custom CSS styling.
"""

import argparse
import markdown
from weasyprint import HTML
import os
import sys

def convert_md_to_pdf(input_file, output_file, title=None, author=None):
    """Convert Markdown file to PDF with custom styling."""
    
    # Read Markdown content
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert Markdown to HTML
    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    html_content = md.convert(md_content)
    
    # Use filename as title if not provided
    if not title:
        title = os.path.splitext(os.path.basename(input_file))[0]
    
    # Generate complete HTML with styling
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 25mm 20mm 20mm 20mm;
            @top-center {{
                content: "{title} | 横纵分析法深度研究报告";
                font-size: 8pt;
                color: #666;
            }}
            @bottom-center {{
                content: "第 " counter(page) " 页";
                font-size: 8pt;
                color: #666;
            }}
        }}
        
        @page:first {{
            @top-center {{
                content: none;
            }}
            @bottom-center {{
                content: none;
            }}
        }}
        
        body {{
            font-family: "Droid Sans Fallback", "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 10.5pt;
            line-height: 1.75;
            color: #2c3e50;
            text-align: justify;
        }}
        
        /* Cover page styling */
        .cover {{
            page-break-after: always;
            text-align: center;
            padding-top: 150px;
        }}
        
        .cover h1 {{
            font-size: 28pt;
            color: #1a5276;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        
        .cover .subtitle {{
            font-size: 16pt;
            color: #2e86c1;
            margin-bottom: 30px;
        }}
        
        .cover .meta {{
            font-size: 11pt;
            color: #555;
            margin-top: 50px;
        }}
        
        .cover .divider {{
            width: 200px;
            height: 3px;
            background-color: #1a5276;
            margin: 30px auto;
        }}
        
        /* Heading styles */
        h1 {{
            font-size: 22pt;
            color: #1a5276;
            border-bottom: 2px solid #1a5276;
            padding-bottom: 5px;
            margin-top: 40px;
        }}
        
        h2 {{
            font-size: 18pt;
            color: #1e8449;
            margin-top: 30px;
        }}
        
        h3 {{
            font-size: 14pt;
            color: #2e86c1;
            margin-top: 20px;
        }}
        
        h4 {{
            font-size: 12pt;
            color: #5b2c6f;
            margin-top: 15px;
        }}
        
        /* Paragraph and text */
        p {{
            margin-bottom: 12px;
            text-align: justify;
        }}
        
        strong {{
            font-weight: bold;
        }}
        
        em {{
            font-style: italic;
        }}
        
        /* Blockquote */
        blockquote {{
            border-left: 3px solid #1a5276;
            padding-left: 15px;
            margin: 15px 0;
            background-color: #f8f9fa;
            padding: 10px 15px;
            border-radius: 4px;
        }}
        
        /* Lists */
        ul, ol {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        
        li {{
            margin-bottom: 5px;
        }}
        
        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        
        th {{
            background-color: #1a5276;
            color: white;
            font-weight: bold;
            padding: 8px;
            text-align: left;
        }}
        
        td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        /* Code */
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
            font-size: 10pt;
        }}
        
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        /* Horizontal rule */
        hr {{
            border: none;
            height: 1px;
            background-color: #ddd;
            margin: 30px 0;
        }}
        
        /* Page breaks for major sections */
        h2 {{
            page-break-before: always;
        }}
        
        h2:first-of-type {{
            page-break-before: avoid;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>{title}</h1>
        <div class="subtitle">横纵分析法深度研究报告</div>
        <div class="divider"></div>
        <div class="meta">
            <p>作者：{author if author else '数字生命卡兹克'}</p>
        </div>
    </div>
    
    {html_content}
    
    <div style="margin-top: 50px; border-top: 1px solid #ddd; padding-top: 20px; font-size: 9pt; color: #777;">
        <p>本报告采用横纵分析法（Horizontal-Vertical Analysis）生成，融合了语言学中的历时-共时分析、社会科学中的纵向-横截面研究设计、商学院案例研究法、以及竞争战略分析的核心思想。</p>
    </div>
</body>
</html>
"""
    
    # Save HTML file (for debugging)
    html_file = os.path.splitext(output_file)[0] + '.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    # Generate PDF
    HTML(string=full_html).write_pdf(output_file)
    
    print(f"PDF generated successfully: {output_file}")
    print(f"HTML file saved: {html_file}")

def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF with beautiful formatting')
    parser.add_argument('input', help='Input Markdown file')
    parser.add_argument('output', help='Output PDF file')
    parser.add_argument('--title', help='Report title', default=None)
    parser.add_argument('--author', help='Author name', default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    convert_md_to_pdf(args.input, args.output, args.title, args.author)

if __name__ == '__main__':
    main()