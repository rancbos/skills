# PPTX/DOCX 文本提取指南

> 适用场景：用户提供的课程材料为 PPTX 或 DOCX 格式，需先转为 TXT 再进入三阶段流水线。

## PPTX 提取（无 python-pptx 时的备选方案）

PPTX 本质是 ZIP 包，内含 XML 文件。可用 zipfile + xml.etree 直接提取文本：

```python
import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_pptx(pptx_path):
    """从 PPTX 文件提取文本，无需 python-pptx"""
    text_content = []
    with zipfile.ZipFile(pptx_path, 'r') as z:
        slide_files = [f for f in z.namelist()
                       if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
        for slide_file in sorted(slide_files):
            with z.open(slide_file) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                slide_text = []
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        slide_text.append(elem.text.strip())
                if slide_text:
                    text_content.append("\n".join(slide_text))
    return text_content
```

**注意**：此方法提取的是纯文本，丢失格式、图片、图表。对于课程讲义足够，对于复杂排版文档建议安装 python-pptx。

## DOCX 提取

优先用系统包管理器安装 python3-docx（避免 pip --break-system-packages）：

```bash
apt-get install -y python3-docx
```

```python
from docx import Document

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return [para.text.strip() for para in doc.paragraphs if para.text.strip()]
```

## PDF 提取

需要 poppler-utils（pdftotext 命令行工具）：

```bash
apt-get install -y poppler-utils
```

```bash
pdftotext -layout input.pdf output.txt
```

## 输出格式建议

- **PPTX**：按幻灯片分隔，每张幻灯片文本用 `\n\n--- 幻灯片分隔 ---\n\n` 连接
- **DOCX**：保留段落结构，用 `\n\n` 分隔段落
- **PDF**：保留布局（-layout 参数），用 `\n` 分隔行

## Pitfall 0：python-pptx 安装超时

pip install python-pptx 在某些环境下超时（>60s）。备选方案：
1. 优先用 zipfile+XML 提取（上文代码）
2. 如果需要保留格式，用 LibreOffice 命令行转换（需安装 libreoffice）
3. 如果以上都不行，用 unzip 解压后手动解析 XML
