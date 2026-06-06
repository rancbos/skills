# 课程讲义处理指南

## 场景

课程讲义（PPTX、DOCX、PDF）通常具有以下特点：
- 文件数量多（多个课时）
- 每个文件内容相对较少
- 结构不规则（非标准书籍格式）
- 包含实践性内容（案例、步骤、工具）

## 处理流程

### 1. 文件转换

将课程讲义转换为 TXT 格式：

- **PPTX**：使用 zipfile + XML 解析提取幻灯片文本
- **DOCX**：使用 python-docx 提取段落文本
- **PDF**：使用 pdftotext 提取文本

### 2. 批量预处理

使用批量处理脚本处理多个文件：

```bash
# 预处理所有文件
python3 scripts/clean_text.py /path/to/lecture.txt /path/to/output
python3 scripts/build_book_index.py /path/to/cleaned_text.txt /path/to/output
```

### 3. 单章主导型识别

课程讲义通常满足单章主导型条件：
- `meaningful_chapter_count: 1`
- `fragmentation_ratio: 0.0` 或较低

### 4. 手动提取 candidates

由于课程讲义结构不规则，建议手动提取：

1. **读取章节内容**：快速扫读，识别核心概念
2. **提取方法论单元**：
   - 框架（framework）：核心概念体系
   - 原则（principle）：指导性规则
   - 程序（procedure）：操作步骤
   - 边界（boundary）：限制条件
3. **创建 candidates 文件**：按照标准格式创建

### 5. 编写 SUMMARY.md

由于 pipeline 可能无法正常运行，直接编写 SUMMARY.md：

1. **五问分析**：分析作者意图、核心论点、论证逻辑、局限性、启发
2. **方法论单元**：为每个核心概念创建七段方法论单元
3. **审计信息**：记录提炼过程和注意事项

## 最佳实践

### 1. 文件命名规范化
- 移除特殊字符（：，、等）
- 使用下划线或连字符分隔
- 保持一致性（如：第一课、第二讲、第三课）

### 2. 内容整合
- 识别课程间的逻辑关系
- 提取共同的方法论框架
- 创建课程体系总结

### 3. 质量控制
- 确保七段完整性
- 验证引用出处
- 检查反直觉洞见

### 4. 实践导向
- 强调可操作性
- 提供具体步骤
- 包含案例说明

## 注意事项

1. **格式兼容性**：PPTX 提取可能丢失格式信息
2. **文本质量**：转换后的文本可能需要人工清理
3. **章节识别**：自动章节识别可能不准确
4. **candidates 格式**：手动创建的 candidates 需要补充必需字段

## 示例：课程讲义目录结构

```
/root/mydata/1/texts/
├── 第一课/
│   ├── cleaned_text.txt
│   ├── cleaned_text/
│   │   ├── book-index.json
│   │   ├── chapters/
│   │   └── snippets/
│   ├── stage1-understanding.md
│   ├── candidates/
│   │   └── frameworks.md
│   └── SUMMARY.md
├── 第二讲/
│   ├── cleaned_text.txt
│   ├── cleaned_text/
│   ├── stage1-understanding.md
│   ├── candidates/
│   └── SUMMARY.md
├── 第三课/
│   ├── cleaned_text.txt
│   ├── cleaned_text/
│   ├── stage1-understanding.md
│   ├── candidates/
│   └── SUMMARY.md
└── course_summary/
    └── COURSE_SUMMARY.md
```

## 版本

- 2026年6月5日：创建课程讲义处理指南
