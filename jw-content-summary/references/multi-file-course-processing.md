# 多文件课程材料批量处理指南

> 适用场景：用户提供一个目录，内含多个课程文件（PPTX/DOCX/PDF），需逐个处理并生成 SUMMARY.md。

## 处理流程

### Phase 1：文件发现与文本提取

```python
import os

# 扫描目录，按扩展名分类
files = []
for f in os.listdir(directory):
    if f.endswith('.docx'):
        files.append((f, 'docx'))
    elif f.endswith('.pptx'):
        files.append((f, 'pptx'))
    elif f.endswith('.pdf'):
        files.append((f, 'pdf'))
```

为每个文件创建对应的 TXT：
- 输出目录：`<源目录>/texts/<文件名>.txt`
- 文件名清理：将中文标点（：，）替换为连字符，空格替换为下划线

### Phase 2：批量预处理

对每个 TXT 文件运行：
1. `clean_text.py` → 生成 `cleaned_text.txt`
2. `build_book_index.py` → 生成 `book-index.json` + `chapters/`

**注意**：build_book_index.py 的输出目录是源文件所在目录下的子目录，以文件名（去扩展名）命名。

### Phase 3：批量阶段1分析

为每个文件创建 `stage1-understanding.md`：
- 读取 `book-index.json` 获取结构信息
- 分析四问（理解策略）
- 识别书籍类型和提取建议

### Phase 4：批量候选提取

为每个文件创建 `candidates/frameworks.md`：
- 读取章节内容
- 手动识别框架/原则/程序/边界
- 按标准格式写入候选文件

**Pitfall 1**：candidates 文件格式必须严格遵循 schema（id/title/type/keywords/source_line/content/related/confidence），否则 validate_candidates.py 会失败。

**Pitfall 2**：对于课程讲义（非标准书籍），validate_candidates.py 可能因缺少字段（source_chapter/source_quote/summary/v3_pass/v3_reason）而报错。此时可跳过 validate，直接手动编写 SUMMARY.md。

### Phase 5：批量 SUMMARY 生成

两种路径：
1. **标准路径**：运行 pipeline_phase2.py → 生成 summary_plan.json → 按 plan 写 SUMMARY.md
2. **手动路径**（课程讲义推荐）：直接读取 candidates，手动编写五问+七段方法论单元

### Phase 6：课程体系整合

创建 `<源目录>/course_summary/COURSE_SUMMARY.md`：
- 整合所有课程的核心内容
- 按主题分类（认知基础/系统构建/估值方法/基本面分析）
- 提供学习建议和课程间关联

## 输出目录结构

```
<源目录>/texts/
├── <文件1>/
│   ├── cleaned_text.txt
│   ├── cleaned_text/
│   │   ├── book-index.json
│   │   ├── chapters/
│   │   └── snippets/
│   ├── stage1-understanding.md
│   ├── candidates/
│   │   └── frameworks.md
│   └── SUMMARY.md
├── <文件2>/
│   └── ...
└── course_summary/
    └── COURSE_SUMMARY.md
```

## 时间估算

- 文本提取：每文件 1-3 秒
- 预处理（clean+index）：每文件 1-5 秒
- 阶段1分析：每文件 1-2 分钟（手动）
- 候选提取：每文件 2-5 分钟（手动）
- SUMMARY 生成：每文件 3-10 分钟（手动）
- 体系整合：5-10 分钟

9个文件总计约 1-2 小时。

## Pitfall 3：课程讲义 vs 标准书籍

课程讲义（PPTX/DOCX）通常：
- 无标准章节结构（build_book_index 可能只识别到 1-3 个 chunks）
- 无目录（TOC ratio = 0）
- 内容碎片化（每张幻灯片独立）
- 包含大量视觉元素描述（"--- 幻灯片分隔 ---"）

处理建议：
- book_type_hint 通常为 "methodology_treatise"，但实际更接近"课程讲义"
- 阶段1分析应重点关注内容主题而非结构
- 候选提取应注重实用性而非完整性
- SUMMARY 可简化为"核心方法论+实践要点"格式

## Pitfall 4：批量处理时的文件名冲突

多个文件可能有相似的文件名（如"第一课.pptx"和"第一课.pdf"）。建议：
- 使用完整文件名（含扩展名）作为目录名的一部分
- 或在文件名后添加序号（如"第一课_1"）
