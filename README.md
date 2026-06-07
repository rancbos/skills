# Hermes Skills Collection

[![GitHub](https://img.shields.io/badge/GitHub-rancbos%2Fskills-blue)](https://github.com/rancbos/skills)
[![GitCode](https://img.shields.io/badge/GitCode-rancbos%2Fskills-green)](https://gitcode.com/rancbos/skills)

Hermes Agent 的自定义技能集合，覆盖投研分析、内容处理、浏览器自动化、技能管理等领域。

## 技能列表

### 投研分析（jw- 系列）

| Skill | 说明 |
|-------|------|
| **jw-company-analysis** | 深度分析A股/港股/美股公司是否值得长期持有，基于巴菲特/芒格价值投资哲学，五维加权评估 |
| **jw-investment-data** | 投资数据获取层：综合财务画像(18源)+资金流向+5年多维财务+7引擎行情+技术指标+宏观全景 |
| **jw-daily-market-judgment** | A股盘后大势研判：基于数据、事件、情绪、资金和板块轮动，输出结论先行的市场走势理解 |
| **jw-macro-analysis** | 中国宏观经济周期位置判断，基于四周期嵌套模型（康波+房地产+朱格拉+库存周期） |
| **jw-hv-analysis** | 横纵分析法深度研究，融合横向对标与纵向趋势的公司分析框架 |
| **jw-maoism** | 毛泽东思想智慧长者，五大思维大法+应用维度+分层决策 |
| **jw-news** | 从权威中文媒体和金十数据查询最新新闻和财经数据 |
| **jw-stock-value-analyzer** | 基于邱国鹭《投资中最简单的事》的股票价值分析器（已归档） |

### 内容处理

| Skill | 说明 |
|-------|------|
| **jw-bili-summary** | B站视频→逐字稿→Obsidian 自动化：下载音频、whisper转写、生成Markdown文档 |
| **jw-content-summary** | 将一本书或长文蒸馏为可实操的方法论单元（R/I/A1/A2/E/P/B 七段） |
| **jw-ebook-organizer** | 电子书文件的整理、排序、分类 |
| **humanizer-zh** | 中文去 AI 痕迹，使文本更自然、更像人类书写 |

### 浏览器与网络

| Skill | 说明 |
|-------|------|
| **browser-use** | 浏览器自动化：web测试、表单填写、截图、数据提取（CDP Python + 多会话） |
| **web-access** | 通用网页访问：搜索、抓取、CDP 代理自动化，处理登录墙和反爬 |

### 技能管理

| Skill | 说明 |
|-------|------|
| **skill-creator** | 创建、修改和评测技能，含 eval 框架、审计检查、优化方法论 |
| **skill-review** | 技能质量审查与审计，分析结构、描述质量、工作流完整性 |
| **find-skills** | 帮助用户发现和安装 agent skills |

### 其他

| Skill | 说明 |
|-------|------|
| **pua** | PUA 模式：显式请求时激活，含各大厂方法论参考 |

## 使用方式

将本仓库克隆到 `~/.hermes/skills/` 目录，Hermes Agent 会自动加载所有技能：

```bash
git clone git@github.com:rancbos/skills.git ~/.hermes/skills
```

## 目录结构

```
~/.hermes/skills/
├── SKILL.md          # 技能主文件（必须）
├── references/       # 参考文档
├── scripts/          # 辅助脚本
├── templates/        # 输出模板
└── _meta.json        # 元数据（可选）
```

## 许可

MIT License
