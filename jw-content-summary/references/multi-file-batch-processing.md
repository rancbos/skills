# 多文件批量处理指南

## 场景

当需要处理多个相关文件（如课程讲义、系列文章、多册合集）时，逐个处理效率低下。批量处理可以一次性完成预处理阶段。

## 批量处理流程

### 1. 文件转换

将非 TXT 文件转换为 TXT 格式：

```python
import os
import zipfile
import xml.etree.ElementTree as ET
import subprocess

def extract_text_from_pptx(pptx_path):
    """从 PPTX 文件提取文本"""
    text_content = []
    try:
        with zipfile.ZipFile(pptx_path, 'r') as z:
            slide_files = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
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
    except Exception as e:
        print(f"读取 {pptx_path} 失败: {e}")
    return text_content

def extract_text_from_docx(docx_path):
    """从 DOCX 文件提取文本"""
    try:
        from docx import Document
        doc = Document(docx_path)
        return [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    except Exception as e:
        print(f"读取 {docx_path} 失败: {e}")
        return []

def extract_text_from_pdf(pdf_path):
    """从 PDF 文件提取文本"""
    try:
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True)
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        else:
            print(f"pdftotext 失败: {result.stderr}")
            return []
    except Exception as e:
        print(f"PDF 提取失败: {e}")
        return []
```

### 2. 批量预处理

使用 subprocess 批量运行 clean_text.py 和 build_book_index.py：

```python
import subprocess
import json

def batch_preprocess(files, base_dir, skill_dir):
    """批量预处理多个文件"""
    results = []
    
    for filename in files:
        txt_path = os.path.join(base_dir, f"{filename}.txt")
        if not os.path.exists(txt_path):
            print(f"文件不存在: {txt_path}")
            continue
        
        print(f"处理文件: {filename}")
        
        # 1. clean_text
        clean_cmd = f'cd {skill_dir} && python3 scripts/clean_text.py "{txt_path}" "{base_dir}"'
        try:
            result = subprocess.run(clean_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                clean_output = json.loads(result.stdout)
                print(f"  clean_text: {clean_output['ok']}")
            else:
                print(f"  clean_text 失败: {result.stderr}")
                continue
        except Exception as e:
            print(f"  clean_text 异常: {e}")
            continue
        
        # 2. build_book_index
        cleaned_text_path = clean_output['cleaned_text']
        index_cmd = f'cd {skill_dir} && python3 scripts/build_book_index.py "{cleaned_text_path}" "{base_dir}"'
        try:
            result = subprocess.run(index_cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                index_output = json.loads(result.stdout)
                print(f"  build_book_index: {index_output['ok']}, 章节数: {index_output['chapter_count']}")
            else:
                print(f"  build_book_index 失败: {result.stderr}")
                continue
        except Exception as e:
            print(f"  build_book_index 异常: {e}")
            continue
        
        results.append({
            'filename': filename,
            'cleaned_text': cleaned_text_path,
            'book_index_dir': index_output['out_dir'],
            'chapter_count': index_output['chapter_count']
        })
    
    return results
```

### 3. 批量阶段1分析

为每个文件创建 stage1-understanding.md：

```python
def batch_create_stage1(files, base_dir):
    """批量创建 stage1-understanding.md"""
    for filename in files:
        stage1_path = os.path.join(base_dir, filename, "stage1-understanding.md")
        if os.path.exists(stage1_path):
            print(f"stage1 已存在: {stage1_path}")
            continue
        
        content = f"""# 阶段1：理解分析 - {filename}

## 书籍基本信息
- **书名**: {filename}
- **作者**: 未明确
- **类型**: 方法论专著（methodology_treatise）
- **总字符数**: 参见 book-index.json
- **章节数**: 参见 book-index.json

## 四问分析（理解策略）
1. **这本书在讲什么？**
   - 核心主题和内容
   - 主要方法论和框架

2. **作者如何论证？**
   - 论证逻辑和结构
   - 案例和证据

3. **这本书有道理吗？**
   - 逻辑清晰度
   - 实践可行性

4. **这本书有什么意义？**
   - 对读者的价值
   - 实践应用意义

## 提取建议
- **书籍类型**: 方法论专著
- **重点提取**: framework, principle, procedure, boundary
- **可简化**: glossary（术语较少）
"""
        
        with open(stage1_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"创建: {stage1_path}")
```

### 4. 批量创建目录结构

```python
def batch_create_directories(files, base_dir):
    """批量创建目录结构"""
    for filename in files:
        # 创建 stage1-understanding.md
        stage1_path = os.path.join(base_dir, filename, "stage1-understanding.md")
        if not os.path.exists(stage1_path):
            # 创建简化的 stage1 文件
            content = f"# 阶段1：理解分析 - {filename}\n\n## 书籍基本信息\n- **书名**: {filename}\n"
            with open(stage1_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 创建 candidates 目录
        candidates_dir = os.path.join(base_dir, filename, "candidates")
        os.makedirs(candidates_dir, exist_ok=True)
        
        # 创建简化的 candidates 文件
        candidates_path = os.path.join(candidates_dir, "frameworks.md")
        if not os.path.exists(candidates_path):
            content = f"""# Candidates for {filename}

- id: fw-01
  title: 核心框架
  type: framework
  keywords: [核心, 框架, 方法论]
  source_line: "核心内容"
  content: |
    核心框架内容，需要从原文提取。
  related: []
  confidence: 0.8
"""
            with open(candidates_path, 'w', encoding='utf-8') as f:
                f.write(content)
```

## 最佳实践

### 1. 文件命名规范化
- 移除特殊字符（：，、等）
- 使用下划线或连字符分隔
- 保持一致性

### 2. 错误处理
- 捕获并记录每个文件的处理错误
- 跳过失败的文件，继续处理其他文件
- 汇总处理结果

### 3. 进度跟踪
- 打印每个文件的处理状态
- 记录成功/失败数量
- 提供最终汇总报告

### 4. 资源管理
- 设置合理的超时时间
- 限制并发数量（避免资源耗尽）
- 及时释放文件句柄

## 注意事项

1. **文件格式兼容性**：PPTX 提取可能丢失格式信息，PDF 需要 pdftotext 工具
2. **文本质量**：转换后的文本可能需要人工清理
3. **章节识别**：自动章节识别可能不准确，需要人工验证
4. **candidates 格式**：批量创建的 candidates 可能需要手动补充必需字段

## 版本

- 2026年6月5日：创建批量处理指南
