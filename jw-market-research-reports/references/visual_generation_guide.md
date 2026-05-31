# 市场研究报告可视化生成指南

市场研究报告中生成可视化的完整提示词和指导。

---

## 概述

市场研究报告应首先生成 **5-6个核心可视化** 以建立分析框架。在撰写具体章节时可按需生成额外的可视化。本指南为 `scientific-schematics` 和 `generate-image` 技能提供即用型提示词。

### 核心可视化（优先生成 - 优先级 1-6）

每份市场报告开始时请生成以下5-6个核心可视化：

1. **市场增长趋势图** - 展示市场规模变化趋势
2. **TAM/SAM/SOM 图** - 市场机会分解
3. **波特五力分析** - 竞争动态框架
4. **竞争定位矩阵** - 战略定位
5. **风险热力图** - 风险评估可视化
6. **执行摘要信息图**（可选） - 报告概览

### 扩展可视化（按需生成 - 优先级 7+）

在撰写需要可视化支持的特定章节时可生成额外的可视化：
- 区域分解图
- 细分分析
- 客户旅程图
- 技术路线图
- 监管时间线
- 财务预测
- 实施时间线

### 工具选择

| 可视化类型 | 工具 | 理由 |
|-------------|------|-----------|
| 图表（柱状图、折线图、饼图） | scientific-schematics | 精确的数据呈现 |
| 图表（流程图、结构图） | scientific-schematics | 清晰的技术布局 |
| 矩阵（2x2、定位） | scientific-schematics | 战略框架 |
| 时间线 | scientific-schematics | 顺序信息展示 |
| 信息图 | generate-image | 创意视觉合成 |
| 概念插图 | generate-image | 抽象概念表达 |

---

## 可视化命名规范

### 核心可视化（优先生成）
```
figures/
├── 01_market_growth_trajectory.png      # PRIORITY 1
├── 02_tam_sam_som.png                   # PRIORITY 2
├── 03_porters_five_forces.png           # PRIORITY 3
├── 04_competitive_positioning.png       # PRIORITY 4
├── 05_risk_heatmap.png                  # PRIORITY 5
└── 06_exec_summary_infographic.png      # PRIORITY 6 (optional)
```

### 扩展可视化（按需生成）
```
figures/
├── 07_industry_ecosystem.png
├── 08_regional_breakdown.png
├── 09_segment_growth.png
├── 10_driver_impact_matrix.png
├── 11_pestle_analysis.png
├── 12_trends_timeline.png
├── 13_market_share.png
├── 14_strategic_groups.png
├── 15_customer_segments.png
├── 16_segment_attractiveness.png
├── 17_customer_journey.png
├── 18_technology_roadmap.png
├── 19_innovation_curve.png
├── 20_regulatory_timeline.png
├── 21_risk_mitigation.png
├── 22_opportunity_matrix.png
├── 23_recommendation_priority.png
├── 24_implementation_timeline.png
├── 25_milestone_tracker.png
├── 26_financial_projections.png
└── 27_scenario_analysis.png
```

---

## 核心可视化（优先级 1-6）- 优先生成

### 优先级 1：市场增长趋势图

**工具：** scientific-schematics

**用途：** 展示历史和预测市场规模的基础可视化

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "柱状图展示2020至2034年市场增长。2020-2024年历史数据柱为深蓝色，2025-2034年预测柱为浅蓝色。Y轴为十亿美元，X轴为年份。标注复合年增长率。每个柱状图上显示数据标签。2024与2025之间用垂直虚线分隔。标题：市场增长趋势。专业白色背景" \
  -o figures/01_market_growth_trajectory.png --doc-type report
```

---

### 优先级 2：TAM/SAM/SOM 图

**工具：** scientific-schematics

**用途：** 市场机会规模可视化

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "TAM SAM SOM同心圆图。外圈为TAM总潜在市场。中圈为SAM可服务可获取市场。内圈为SOM可服务可获得市场。每圈标注缩写、全称和美元金额占位符。箭头指向各圈并附说明。蓝色渐变从外圈最深到内圈最浅。白色背景专业外观" \
  -o figures/02_tam_sam_som.png --doc-type report
```

---

### 优先级 3：波特五力分析图

**工具：** scientific-schematics

**用途：** 竞争动态框架

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "波特五力分析图。中心方框为竞争激烈程度及评级。四个周围方框通过箭头指向中心：顶部为新进入者威胁，左侧为供应商议价能力，右侧为买方议价能力，底部为替代品威胁。颜色编码：高为红色，中为黄色，低为绿色。每个方框包含2-3个关键因素。专业外观" \
  -o figures/03_porters_five_forces.png --doc-type report
```

---

### 优先级 4：竞争定位矩阵

**工具：** scientific-schematics

**用途：** 主要市场参与者的战略定位

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2x2竞争定位矩阵。X轴市场聚焦从细分到广泛。Y轴解决方案方式从产品到平台。象限：右上为平台领导者，左上为细分平台，右下为产品领导者，左下为专才型企业。绘制8-10个公司圆圈并标注名称。圆圈大小代表市场份额。附大小图例。专业外观" \
  -o figures/04_competitive_positioning.png --doc-type report
```

---

### 优先级 5：风险热力图

**工具：** scientific-schematics

**用途：** 视觉化风险评估矩阵

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "风险热力图矩阵。X轴影响程度：低、中、高、严重。Y轴发生概率：不太可能、有可能、很可能、非常可能。单元格颜色：绿色为低风险，黄色为中等，橙色为高风险，红色为严重风险。绘制10-12个编号风险点R1、R2等作为标注点。图例列出风险名称。专业清晰" \
  -o figures/05_risk_heatmap.png --doc-type report
```

---

### 优先级 6：执行摘要信息图（可选）

**工具：** generate-image

**用途：** 用于封面或执行摘要的高层级视觉综合

**命令：**
```bash
python skills/generate-image/scripts/generate_image.py \
  "市场研究报告执行摘要信息图，单页布局，中央显示市场规模大数字，四个象限分别展示增长率、主要参与者、顶级细分市场、区域领导者，现代扁平化设计，专业蓝绿配色方案，干净白色背景，商务美学" \
  --output figures/06_exec_summary_infographic.png
```

---

## 扩展可视化 - 在撰写过程中按需生成

以下可视化可在撰写需要它们的特定章节时生成。

---

## 前置内容可视化

### 扩展：封面图 / 主视觉图

**工具：** generate-image

**提示词：**
```
[市场名称]市场研究报告的专业执行摘要信息图。
现代数据可视化风格，展示关键指标：市场规模、增长率、主要参与者。
蓝绿色配色方案，匹配企业设计。
简洁的图标化极简设计。
高分辨率，出版品质。
无文字叠加，仅图像。
```

**命令：**
```bash
python skills/generate-image/scripts/generate_image.py \
  "[市场名称]市场研究报告的专业执行摘要信息图，现代数据可视化风格，关键指标展示，蓝绿企业配色方案，简洁图标化极简设计，高分辨率出版品质" \
  --output figures/01_cover_image.png
```

### 2. 执行摘要信息图

**工具：** generate-image

**提示词：**
```
单页执行摘要信息图，展示：
- 中央大数字：XX十亿美元市场规模
- 四个象限：增长率、主要参与者、顶级细分市场、区域领导者
- 现代扁平化设计，含数据可视化元素
- 专业蓝（#003366）绿（#008060）配色方案
- 干净白色背景
- 商务/企业美学
```

**命令：**
```bash
python skills/generate-image/scripts/generate_image.py \
  "市场研究报告执行摘要信息图，单页布局，中央显示市场规模大数字，四个象限分别展示增长率、主要参与者、顶级细分市场、区域领导者，现代扁平化设计，专业蓝绿配色方案，干净白色背景，商务美学" \
  --output figures/02_exec_summary_infographic.png
```

---

## 第一章：市场概述可视化

### 3. 产业生态系统图

**工具：** scientific-schematics

**提示词：**
```
产业生态系统价值链图，展示从左到右的水平流向：
[供应商/原材料] → [制造商/加工者] → [分销商/渠道] → [终端用户/客户]

每个阶段下方用小方框展示3-4个示例参与者类型。
用箭头展示产品/服务流（实线）和资金流（虚线）。
在链条上方将监管机构作为监督层。
专业蓝色配色方案。
干净白色背景。
所有文字清晰可读。
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "产业生态系统价值链图。水平流向从左到右：供应商方框 → 制造商方框 → 分销商方框 → 终端用户方框。每个主方框下方展示3-4个带示例参与者类型的小方框。实线箭头表示产品流，虚线箭头表示资金流。上方为监管监督层。专业蓝色配色方案，白色背景，清晰标注" \
  -o figures/03_industry_ecosystem.png --doc-type report
```

### 4. 市场结构图

**工具：** scientific-schematics

**提示词：**
```
市场结构图，展示同心矩形：
- 中心：核心市场（标注市场名称）
- 第二层：相邻市场（标注4-5个相邻市场名称）
- 第三层：使能技术（标注关键技术）
- 外层：监管框架

每层使用不同深浅的蓝色。
包含关键元素的小图标或标签。
专业外观。
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "同心矩形市场结构图。中心：核心市场[市场名称]。第二层：相邻市场含4-5个标签。第三层：使能技术含关键技术标签。外层：监管框架。每层使用不同深浅蓝色，专业外观，清晰标注" \
  -o figures/03b_market_structure.png --doc-type report
```

---

## 第二章：市场规模与增长可视化

### 5. 市场增长趋势图

**工具：** scientific-schematics

**提示词：**
```
柱状图展示2020至2034年市场增长。
历史年份（2020-2024）：深蓝色柱
预测年份（2025-2034）：浅蓝色柱
Y轴：市场规模，单位十亿美元（0至$XXX）
X轴：年份
标注"XX.X% 复合年增长率（2024-2034）"
每个柱状图顶部显示数据标签
垂直虚线分隔历史和预测部分
标题："[市场名称]市场增长趋势"
专业外观，白色背景
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "柱状图展示2020至2034年市场增长。2020-2024年历史数据柱为深蓝色，2025-2034年预测柱为浅蓝色。Y轴为十亿美元，X轴为年份。标注复合年增长率XX.X%（2024-2034）。每个柱状图显示数据标签。2024与2025之间垂直虚线分隔。标题：市场增长趋势。专业白色背景" \
  -o figures/04_market_growth_trajectory.png --doc-type report
```

### 6. TAM/SAM/SOM 图

**工具：** scientific-schematics

**提示词：**
```
TAM SAM SOM 同心圆图：
- 外圈：TAM（总潜在市场） - $XXX十亿
- 中圈：SAM（可服务可获取市场） - $XX十亿
- 内圈：SOM（可服务可获得市场） - $X十亿

每个圆圈标注：
- 加粗的缩写
- 全称
- 美元金额

箭头指向各圆圈并附说明
使用蓝色渐变（TAM最深，SOM最浅）
专业外观
白色背景
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "TAM SAM SOM同心圆。外圈TAM总潜在市场[数值]B。中圈SAM可服务可获取市场[数值]B。内圈SOM可服务可获得市场[数值]B。每圈标注缩写、全称和美元金额。箭头指向各圈并附说明。蓝色渐变从外圈最深到内圈最浅。白色背景专业外观" \
  -o figures/05_tam_sam_som.png --doc-type report
```

### 7. 区域市场分解

**工具：** scientific-schematics

**提示词：**
```
饼图或树图展示区域市场分解：
- 北美：XX%（$X.XB） - 深蓝色
- 欧洲：XX%（$X.XB） - 中蓝色
- 亚太：XX%（$X.XB） - 青绿色
- 拉丁美洲：X%（$X.XB） - 浅蓝色
- 中东与非洲：X%（$X.XB） - 灰蓝色

每个区域同时显示百分比和美元金额
图例位于右侧
标题："2024年区域市场规模"
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "饼图展示区域市场分解。北美XX%深蓝色，欧洲XX%中蓝色，亚太XX%青绿色，拉丁美洲XX%浅蓝色，中东与非洲XX%灰蓝色。每个扇区显示百分比和美元金额。图例在右侧。标题：2024年区域市场规模。专业外观" \
  -o figures/06_regional_breakdown.png --doc-type report
```

### 8. 细分市场增长比较

**工具：** scientific-schematics

**提示词：**
```
水平柱状图比较各细分市场增长率：
- Y轴：细分市场名称（5-7个细分）
- X轴：复合年增长率百分比（0%至30%）
- 柱状图按增长率着色：绿色（最高）到蓝色（最低）
- 每个柱状图显示精确百分比的数据标签
- 按增长率从高到低排列
- 标题："细分市场增长率比较（复合年增长率2024-2034）"
- 包含平均线或标记
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "水平柱状图细分市场增长比较。Y轴5-7个细分市场名称，X轴复合年增长率0-30%。柱状图颜色从绿色（最高）到蓝色（最低）。数据标签显示精确百分比。按从高到低排列。标题：细分市场增长率比较 复合年增长率2024-2034。包含市场平均线" \
  -o figures/07_segment_growth.png --doc-type report
```

---

## 第三章：行业驱动因素与趋势可视化

### 9. 驱动因素影响矩阵

**工具：** scientific-schematics

**提示词：**
```
2x2市场驱动因素评估矩阵：
- X轴：对市场的影响（低 → 高）
- Y轴：发生概率（低 → 高）
- 右上象限："关键驱动因素"（红色/橙色背景）
- 左上象限："监测关注"（黄色背景）
- 右下象限："密切关注"（黄色背景）
- 左下象限："较低优先级"（绿色背景）

绘制8-10个驱动因素作为标注圆圈：
- 圆圈大小代表当前市场影响
- 位置基于评级

包含圆圈大小图例
专业外观，标注清晰
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2x2驱动因素影响评估矩阵。X轴影响程度从低到高，Y轴发生概率从低到高。象限：右上关键驱动因素红色，左上监测关注黄色，右下密切关注黄色，左下较低优先级绿色。绘制8-10个标注驱动因素圆圈在适当位置。圆圈大小表示当前影响。专业清晰标注" \
  -o figures/08_driver_impact_matrix.png --doc-type report
```

### 10. PESTLE分析图

**工具：** scientific-schematics

**提示词：**
```
PESTLE分析六边形图：
- 中心六边形："[市场名称]"
- 六个周围六边形连接到中心：
  - 政治（红色/橙色）
  - 经济（蓝色）
  - 社会（绿色）
  - 技术（橙色）
  - 法律（紫色）
  - 环境（青绿色）

每个外部六边形包含2-3个关键要点
中心与外部六边形之间用连接线
专业外观
每个六边形内文字清晰可读
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "PESTLE六边形分析图。中心六边形标注市场名称。六个周围六边形：政治红色，经济蓝色，社会绿色，技术橙色，法律紫色，环境青绿色。每个外部六边形含2-3个关键因素要点。连接线从中心到各六边形。专业外观清晰可读文字" \
  -o figures/09_pestle_analysis.png --doc-type report
```

### 11. 行业趋势时间线

**工具：** scientific-schematics

**提示词：**
```
水平时间线展示2024至2030年的新兴趋势：
- 主水平轴含年份标记
- 在时间线不同位置绘制6-8个趋势
- 每个趋势显示：
  - 图标或符号
  - 趋势名称
  - 下方3-5个词的简要描述

按趋势类别进行颜色编码：
- 技术趋势：蓝色
- 市场趋势：绿色
- 监管趋势：橙色

在2024年标注"当前"标记
专业外观，标注清晰
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "水平时间线2024至2030年。在不同年份绘制6-8个新兴趋势。每个趋势含图标、名称和简要描述。颜色编码：技术趋势蓝色，市场趋势绿色，监管趋势橙色。2024年标注当前标记。专业清晰标注" \
  -o figures/10_trends_timeline.png --doc-type report
```

---

## 第四章：竞争格局可视化

### 12. 波特五力分析图

**工具：** scientific-schematics

**提示词：**
```
波特五力分析图，含中心方框和四个周围方框：

中心方框："竞争激烈程度"，评级为[高/中/低]

周围方框通过箭头连接到中心：
- 顶部："新进入者威胁" [评级]
- 左侧："供应商议价能力" [评级]
- 右侧："买方议价能力" [评级]
- 底部："替代品威胁" [评级]

颜色编码评级：
- 高：红色/橙色背景
- 中：黄色背景
- 低：绿色背景

箭头指向中心
每个方框包含关键因素要点
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "波特五力分析图。中心方框为竞争激烈程度[评级]。四个周围方框通过箭头指向中心：顶部为新进入者威胁[评级]，左侧为供应商议价能力[评级]，右侧为买方议价能力[评级]，底部为替代品威胁[评级]。颜色编码：高为红色，中为黄色，低为绿色。每个方框含2-3个关键因素。专业外观" \
  -o figures/11_porters_five_forces.png --doc-type report
```

### 13. 市场份额图

**工具：** scientific-schematics

**提示词：**
```
饼图或环形图展示市场份额：
- 前10家公司，使用不同颜色
- A公司：XX%（最大扇区，深蓝色）
- B公司：XX%（中蓝色）
- [继续列出前10家]
- 其他：XX%（灰色）

包含：
- 每个扇区的百分比标签
- 图例或扇区上的公司名称
- 总市场规模标注
- 标题："2024年各公司市场份额"

专业外观
色盲友好配色方案
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "饼图展示前10家公司市场份额。A公司XX%深蓝色，B公司XX%中蓝色，[列出公司和份额]，其他XX%灰色。扇区显示百分比标签。图例含公司名称。标注总市场规模。标题：2024年各公司市场份额。色盲友好颜色，专业外观" \
  -o figures/12_market_share.png --doc-type report
```

### 14. 竞争定位矩阵

**工具：** scientific-schematics

**提示词：**
```
2x2竞争定位矩阵：
- X轴：市场聚焦（细分 ← → 广泛）
- Y轴：解决方案方式（产品 ← → 平台）

象限标签：
- 右上："平台领导者"
- 左上："细分平台"
- 右下："产品领导者"
- 左下："专才型企业"

绘制8-10家公司作为标注圆圈：
- 圆圈大小代表市场份额
- 位置基于战略

包含圆圈大小图例
公司名称标签
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2x2竞争定位矩阵。X轴市场聚焦从细分到广泛。Y轴解决方案方式从产品到平台。象限：右上平台领导者，左上细分平台，右下产品领导者，左下专才型企业。绘制8-10个公司圆圈并标注名称。圆圈大小等于市场份额。附大小图例。专业外观" \
  -o figures/13_competitive_positioning.png --doc-type report
```

### 15. 战略群组图

**工具：** scientific-schematics

**提示词：**
```
战略群组图展示竞争对手集群：
- X轴：地理范围（区域 ← → 全球）
- Y轴：产品广度（窄 ← → 宽）

绘制4-5个椭圆形"气泡"代表战略群组：
- 每个气泡包含2-4个公司名称
- 气泡大小代表该群组的集体市场份额
- 每个战略群组使用不同颜色

标注每个战略群组：
- "全球综合型企业"
- "区域专才型企业"
- "聚焦创新型"
- 等等

专业外观
公司名称标签清晰
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "战略群组图。X轴地理范围从区域到全球。Y轴产品广度从窄到宽。绘制4-5个椭圆形气泡代表战略群组。每个气泡含2-4个公司名称。气泡大小等于集体市场份额。标注群组：全球综合型、区域专才型、聚焦创新型等。每组不同颜色。专业清晰标注" \
  -o figures/14_strategic_groups.png --doc-type report
```

---

## 第五章：客户分析可视化

### 16. 客户细分分解

**工具：** scientific-schematics

**提示词：**
```
树图或饼图展示客户细分：
- 大型企业：XX%（深蓝色）
- 中型市场：XX%（中蓝色）
- 中小企业：XX%（浅蓝色）
- 消费者：XX%（青绿色）

大小代表市场份额
每个细分包含：
- 细分名称
- 百分比
- 美元金额

标题："按市场份额划分的客户细分"
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "树图客户细分。大型企业XX%深蓝色，中型市场XX%中蓝色，中小企业XX%浅蓝色，消费者XX%青绿色。每个细分显示名称、百分比和美元金额。标题：按市场份额划分的客户细分。专业外观" \
  -o figures/15_customer_segments.png --doc-type report
```

### 17. 细分吸引力矩阵

**工具：** scientific-schematics

**提示词：**
```
2x2细分吸引力矩阵：
- X轴：细分规模（小 ← → 大）
- Y轴：增长率（低 ← → 高）

象限标签和行动：
- 右上："优先 - 重点投入"
- 左上："投资增长"
- 右下："收割"
- 左下："降低优先级"

绘制客户细分作为标注圆圈
圆圈大小代表盈利能力
每个细分使用不同颜色
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2x2细分吸引力矩阵。X轴细分规模从小到大。Y轴增长率从低到高。象限：右上优先重点投入，左上投资增长，右下收割，左下降低优先级。绘制客户细分为圆圈。圆圈大小等于盈利能力。不同颜色。专业外观" \
  -o figures/16_segment_attractiveness.png --doc-type report
```

### 18. 客户旅程图

**工具：** scientific-schematics

**提示词：**
```
客户旅程水平流程图，展示5-6个阶段：
认知 → 考虑 → 决策 → 实施 → 使用 → 推荐

每个阶段展示三行：
1. 关键活动（客户做什么）
2. 痛点（面临的挑战）
3. 触点（如何互动）

每个阶段使用图标
颜色从浅到深随旅程进展
专业外观
标注清晰
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "客户旅程水平流程图。5个阶段从左到右：认知、考虑、决策、实施、使用、推荐。每个阶段下方显示关键活动、痛点、触点三行。每个阶段使用图标。颜色渐变从浅到深。专业清晰标注" \
  -o figures/17_customer_journey.png --doc-type report
```

---

## 第六章：技术格局可视化

### 19. 技术路线图

**工具：** scientific-schematics

**提示词：**
```
2024至2030年技术路线图时间线：
三条平行水平轨道：
1. 核心技术（蓝色） - 当前基础
2. 新兴技术（绿色） - 发展中的能力
3. 使能技术（橙色） - 基础设施/支持

每条轨道展示里程碑和技术引入标记
垂直线连接跨轨道的相关技术
每年的时间线标记
技术名称在引入点标注
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2024至2030年技术路线图。三条平行水平轨道：核心技术蓝色，新兴技术绿色，使能技术橙色。每条轨道标注里程碑和技术引入。垂直线连接相关技术。年份标记。技术名称标注。专业外观" \
  -o figures/18_technology_roadmap.png --doc-type report
```

### 20. 创新/采纳曲线

**工具：** scientific-schematics

**提示词：**
```
Gartner炒作周期或技术采纳曲线：
从左到右五个阶段：
1. 创新触发期（上升）
2. 期望膨胀期（顶峰）
3. 泡沫破裂期（谷底）
4. 复苏期（上升）
5. 生产力稳定期（平稳）

在曲线不同位置绘制6-8项技术
每项技术标注名称
按技术类别进行颜色编码
专业外观
坐标轴标注清晰
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "Gartner炒作周期曲线。五个阶段：创新触发期上升，期望膨胀期在顶部，泡沫破裂期在底部，复苏期上升，生产力稳定期平稳。在曲线上绘制6-8项技术并标注名称。按类别着色。专业清晰标注" \
  -o figures/19_innovation_curve.png --doc-type report
```

---

## 第七章：监管环境可视化

### 21. 监管时间线

**工具：** scientific-schematics

**提示词：**
```
2020至2028年监管时间线：
水平时间线含年份标记
标注关键监管事件：
- 过去的法规（深蓝色标记，实线）
- 当前法规（当前年份绿色标记）
- 即将到来的法规（浅蓝色标记，虚线）

每个标记显示：
- 法规名称
- 生效日期
- 简要描述（5-7个词）

在当前年份（2024）标注垂直"现在"线
如有多个法域则按区域分组
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2020至2028年监管时间线。过去法规深蓝色实线标记，当前绿色标记，即将到来浅蓝色虚线。每个标记显示法规名称、日期和简要描述。2024年标注垂直现在线。专业外观清晰标注" \
  -o figures/20_regulatory_timeline.png --doc-type report
```

---

## 第八章：风险分析可视化

### 22. 风险热力图

**工具：** scientific-schematics

**提示词：**
```
风险评估热力图/矩阵：
- X轴：影响（低 → 中 → 高 → 严重）
- Y轴：概率（不太可能 → 有可能 → 很可能 → 非常可能）

单元格颜色渐变：
- 绿色：低风险（低概率、低影响）
- 黄色：中等风险
- 橙色：高风险
- 红色：严重风险（高概率、高影响）

在适当单元格中绘制10-12个风险作为标注点/圆圈
风险标签应清晰可读
包含风险编号（R1、R2等）
图例将编号对应风险名称
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "风险热力图矩阵。X轴影响程度：低、中、高、严重。Y轴概率：不太可能、有可能、很可能、非常可能。单元格颜色：绿色低风险，黄色中等，橙色高风险，红色严重。绘制10-12个编号风险点R1、R2等作为标注点。图例列出风险名称。专业清晰" \
  -o figures/21_risk_heatmap.png --doc-type report
```

### 23. 风险缓解框架

**工具：** scientific-schematics

**提示词：**
```
风险缓解图，展示风险及其缓解措施：
左列：风险（红色/橙色方框）
右列：缓解策略（绿色/蓝色方框）

用箭头将每个风险连接到其缓解措施
按类别分组风险（市场、监管、技术等）
同时包含预防和应对策略

风险严重程度由方框颜色强度表示
专业外观
标注清晰
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "风险缓解图。左列为橙色/红色方框的风险。右列为绿色/蓝色方框的缓解策略。箭头连接风险到缓解措施。按类别分组。风险严重程度由颜色强度表示。包含预防和应对策略。专业清晰标注" \
  -o figures/22_risk_mitigation.png --doc-type report
```

---

## 第九章：战略建议可视化

### 24. 机会矩阵

**工具：** scientific-schematics

**提示词：**
```
2x2机会评估矩阵：
- X轴：市场吸引力（低 ← → 高）
- Y轴：获胜能力（低 ← → 高）

象限标签和策略：
- 右上："积极追求"（绿色）
- 左上："能力建设"（黄色）
- 右下："选择性投资"（黄色）
- 左下："回避/退出"（红色）

绘制6-8个机会作为标注圆圈
圆圈大小代表机会规模（$）
包含机会名称
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2x2机会矩阵。X轴市场吸引力从低到高。Y轴获胜能力从低到高。象限：右上积极追求绿色，左上能力建设黄色，右下选择性投资黄色，左下回避红色。绘制6-8个机会圆圈并标注名称。大小等于机会价值。专业外观" \
  -o figures/23_opportunity_matrix.png --doc-type report
```

### 25. 建议优先级矩阵

**工具：** scientific-schematics

**提示词：**
```
2x2建议优先级矩阵：
- X轴：工作量/投入（低 ← → 高）
- Y轴：影响/价值（低 ← → 高）

象限标签：
- 左上："速赢项目"（绿色） - 优先执行
- 右上："重大项目"（蓝色） - 仔细规划
- 左下："填充项目"（灰色） - 有时间再做
- 右下："吃力不讨好"（红色） - 避免

绘制6-8个建议作为标注点
按优先级编号建议
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "2x2优先级矩阵。X轴工作量从低到高。Y轴影响从低到高。象限：左上速赢项目绿色优先执行，右上重大项目蓝色仔细规划，左下填充项目灰色有时间再做，右下吃力不讨好红色避免。绘制6-8个编号建议。专业外观" \
  -o figures/24_recommendation_priority.png --doc-type report
```

---

## 第十章：实施路线图可视化

### 26. 实施时间线/甘特图

**工具：** scientific-schematics

**提示词：**
```
甘特图式实施时间线，跨度24个月：
四个阶段以水平条形展示：
- 第一阶段：基础（第1-6个月） - 深蓝色
- 第二阶段：构建（第4-12个月） - 中蓝色
- 第三阶段：扩展（第10-18个月） - 青绿色
- 第四阶段：优化（第16-24个月） - 浅蓝色

各阶段按日期重叠
关键里程碑在时间线上用菱形标记
X轴为月份标记
Y轴为阶段名称
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "甘特图实施时间线24个月。第一阶段基础第1-6月深蓝色。第二阶段构建第4-12月中蓝色。第三阶段扩展第10-18月青绿色。第四阶段优化第16-24月浅蓝色。条形重叠。关键里程碑用菱形标记。X轴为月份。专业外观" \
  -o figures/25_implementation_timeline.png --doc-type report
```

### 27. 里程碑追踪

**工具：** scientific-schematics

**提示词：**
```
里程碑追踪器，在水平时间线上展示8-10个关键里程碑：
每个里程碑显示：
- 日期/月份
- 里程碑名称
- 状态指示：
  - 已完成：绿色勾号 ✓
  - 进行中：黄色圆圈 ○
  - 待开始：灰色圆圈 ○

按阶段分组里程碑
用时间线连接里程碑
时间线上方标注阶段标签
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "里程碑追踪器水平时间线8-10个里程碑。每个显示日期、名称和状态：已完成绿色勾号，进行中黄色圆圈，待开始灰色圆圈。按阶段分组。阶段标签在上方。时间线连接。专业外观" \
  -o figures/26_milestone_tracker.png --doc-type report
```

---

## 第十一章：投资论证可视化

### 28. 财务预测图

**工具：** scientific-schematics

**提示词：**
```
柱状图与折线图组合展示5年财务预测：
- 柱状图：各年收入（主Y轴，单位百万美元）
- 折线图：增长率叠加（次Y轴，百分比）

展示三种情景：
- 保守：灰色柱
- 基准：蓝色柱
- 乐观：绿色柱

X轴：第1年至第5年
柱状图上显示数据标签
情景和增长线的图例
标题："财务预测（5年）"
专业外观
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "柱状图与折线图组合5年预测。柱状图收入主Y轴美元。折线图增长率次Y轴百分比。三种情景：保守灰色，基准蓝色，乐观绿色。X轴第1-5年。数据标签。图例。标题：财务预测5年。专业外观" \
  -o figures/27_financial_projections.png --doc-type report
```

### 29. 情景分析比较

**工具：** scientific-schematics

**提示词：**
```
分组柱状图比较三种情景下的关键指标：
X轴：指标（第5年收入、第5年EBITDA、市场份额、投资回报率）
Y轴：数值（适合各指标的刻度）

每个指标三根柱：
- 保守：灰色
- 基准：蓝色
- 乐观：绿色

每根柱上显示数据标签
情景图例
标题："情景分析比较"
专业外观
指标标签清晰
```

**命令：**
```bash
python skills/scientific-schematics/scripts/generate_schematic.py \
  "分组柱状图情景比较。X轴指标：第5年收入、第5年EBITDA、市场份额、投资回报率。每个指标三根柱：保守灰色，基准蓝色，乐观绿色。数据标签。图例。标题：情景分析比较。专业清晰标注" \
  -o figures/28_scenario_analysis.png --doc-type report
```

---

## 批量生成脚本

为方便使用，可使用 `generate_market_visuals.py` 脚本批量生成可视化：

```bash
# 仅生成核心5-6个可视化（报告起步推荐）
python skills/jw-market-research-reports/scripts/generate_market_visuals.py \
  --topic "Electric Vehicle Charging Infrastructure" \
  --output-dir figures/

# 生成全部27个可视化（核心+扩展，全面覆盖）
python skills/jw-market-research-reports/scripts/generate_market_visuals.py \
  --topic "Electric Vehicle Charging Infrastructure" \
  --output-dir figures/ \
  --all

# 跳过已生成的文件
python skills/jw-market-research-reports/scripts/generate_market_visuals.py \
  --topic "Your Market" \
  --output-dir figures/ \
  --skip-existing
```

**默认行为：** 仅生成5-6个核心优先可视化。如需所有章节的全面可视化覆盖，请使用 `--all` 参数。

---

## 质量检查清单

在将可视化纳入报告前，请验证：

- [ ] 所有文字在预期尺寸下清晰可读
- [ ] 所有可视化的颜色保持一致
- [ ] 配色方案对色盲友好
- [ ] 数据标签准确
- [ ] 图例清晰完整
- [ ] 标题描述性强
- [ ] 在适用处注明来源
- [ ] 分辨率为300 DPI或更高
- [ ] 文件格式为PNG
- [ ] 遵循命名规范
