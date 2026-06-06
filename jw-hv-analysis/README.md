# jw-hv-analysis

横纵分析法深度研究

## 简介

横纵分析法（Horizontal-Vertical Analysis）深度研究Skill。由数字生命卡兹克提出，融合了索绪尔的历时-共时分析、社会科学的纵向-横截面研究设计、商学院案例研究法与竞争战略分析的核心思想。
当用户想要系统性研究一个产品、公司、概念、技术或人物时使用。核心是双轴分析：纵轴追踪从诞生到当下的完整生命历程（以叙事故事呈现），横轴在当下时间截面上与竞品/同类进行系统性横向对比，最终交叉两条轴产出独到洞察。最终产出一份排版精美的PDF研究报告。

## 版本

v1.0

## 更新时间

2025-06-03

## 目录结构

```
jw-hv-analysis/
├── SKILL.md                    # 主技能文件（五步全流程 + 写作规范）
├── README.md                   # 本文件
├── references/
│   ├── boundaries.md           # 触发边界与 skill 间关系
│   └── forbidden-words-guide.md # 禁区词速查与扩写防护
└── scripts/
    ├── quality_check.py        # 质检脚本（禁区词 + 章节 + 来源 + 字数）
    ├── md_to_pdf.py            # Markdown 转 PDF（需安装 weasyprint）
    └── save_checkpoint.py      # 中间产物保存/加载（断点续做）
```

## 安装和依赖

本技能作为 Hermes Agent 的一部分，无需单独安装。

### 可选依赖

- `weasyprint` + `markdown`：PDF 生成（`pip install weasyprint markdown --break-system-packages`）
- 飞书环境：通过 lark-cli 交付飞书文档

## 使用说明

在对话中触发相关关键词即可使用。例如：

- 深度研究：`"帮我用横纵分析法研究XX"`、`"帮我做个深度研究"`、`"帮我摸清楚XX是怎么回事"`
- 竞品分析：`"XX和YY的竞品分析"`、`"帮我搞懂这个东西是怎么回事"`
- 其他触发词见 SKILL.md 中的描述

## 功能特性

详见 SKILL.md 中的详细说明。

## 注意事项

- 本技能产出研究报告，供研究参考
- 使用前请阅读 SKILL.md 中的写作规范（绝对禁区）
