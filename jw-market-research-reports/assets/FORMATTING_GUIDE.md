# 市场研究报告排版指南

`market_research.sty` 样式包快速参考手册。

## 配色方案

### 主色
| 颜色名称 | RGB | Hex | 用途 |
|----------|-----|-----|------|
| `primaryblue` | (0, 51, 102) | `#003366` | 标题、题目、链接 |
| `secondaryblue` | (51, 102, 153) | `#336699` | 子章节、次要元素 |
| `lightblue` | (173, 216, 230) | `#ADD8E6` | 核心洞察框背景 |
| `accentblue` | (0, 120, 215) | `#0078D7` | 强调高亮、机会框 |

### 辅助色
| 颜色名称 | RGB | Hex | 用途 |
|----------|-----|-----|------|
| `accentgreen` | (0, 128, 96) | `#008060` | 市场数据框、正向指标 |
| `lightgreen` | (200, 230, 201) | `#C8E6C9` | 市场数据框背景 |
| `warningorange` | (255, 140, 0) | `#FF8C00` | 风险框、警告 |
| `alertred` | (198, 40, 40) | `#C62828` | 严重风险 |
| `recommendpurple` | (103, 58, 183) | `#673AB7` | 建议框 |

### 中性色
| 颜色名称 | RGB | Hex | 用途 |
|----------|-----|-----|------|
| `darkgray` | (66, 66, 66) | `#424242` | 正文文字 |
| `mediumgray` | (117, 117, 117) | `#757575` | 次要文字 |
| `lightgray` | (240, 240, 240) | `#F0F0F0` | 背景、提示框 |
| `tablealt` | (245, 247, 250) | `#F5F7FA` | 表格交替行 |

---

## 框环境

### 核心洞察框（蓝色）
用于重大发现、洞察和重要结论。

```latex
\begin{keyinsightbox}[核心发现]
该市场预计以 15.3% 的复合年均增长率增长至 2030 年，主要受企业
加速采用和有利的监管环境驱动。
\end{keyinsightbox}
```

### 市场数据框（绿色）
用于市场统计数据、指标和数据亮点。

```latex
\begin{marketdatabox}[市场概览]
\begin{itemize}
    \item \textbf{市场规模（2024）：} \marketsize{452 亿元}
    \item \textbf{预测规模（2030）：} \marketsize{987 亿元}
    \item \textbf{复合年均增长率：} \growthrate{15.3}
\end{itemize}
\end{marketdatabox}
```

### 风险提示框（橙色/警告）
用于风险因素、警告和注意事项。

```latex
\begin{riskbox}[市场风险]
欧盟监管变化可能在未来 18 个月内影响 40% 的市场参与者。
\end{riskbox}
```

### 严重风险框（红色）
用于高严重性或关键风险。

```latex
\begin{criticalriskbox}[严重风险：供应链中断]
重大供应链中断可能导致 6-12 个月的延迟和 30% 的成本上升。
\end{criticalriskbox}
```

### 建议框（紫色）
用于战略建议和行动事项。

```latex
\begin{recommendationbox}[战略建议]
\begin{enumerate}
    \item 优先进入亚太市场
    \item 与当地分销商建立战略合作
    \item 投资产品本地化
\end{enumerate}
\end{recommendationbox}
```

### 提示框（灰色）
用于定义、注释和补充信息。

```latex
\begin{calloutbox}[定义：TAM]
全部可及市场（TAM）代表在 100% 市场份额假设下的总营收机会。
\end{calloutbox}
```

### 执行摘要框
执行摘要亮点的特殊样式。

```latex
\begin{executivesummarybox}[执行摘要]
报告的关键发现和要点……
\end{executivesummarybox}
```

### 机会框（蓝绿色/强调蓝）
用于机会和正向发现。

```latex
\begin{opportunitybox}[增长机会]
亚太市场代表 150 亿元的机会，以 22% 的复合年均增长率增长。
\end{opportunitybox}
```

### 框架分析框
用于战略分析框架。

```latex
% SWOT 分析
\begin{swotbox}[SWOT 分析摘要]
内容……
\end{swotbox}

% 波特五力分析
\begin{porterbox}[波特五力分析]
内容……
\end{porterbox}
```

---

## 引用高亮

用于突出重要统计数据或引用。

```latex
\begin{pullquote}
"AI 与医疗的融合代表着到 2034 年 1990 亿元的机会。"
\end{pullquote}
```

---

## 数据指标框

用于突出关键统计数据（建议每行 3 个）。

```latex
\begin{center}
\statbox{452亿元}{2024年市场规模}
\statbox{15.3\%}{2024-2030 复合年均增长率}
\statbox{23\%}{市场领导者份额}
\end{center}
```

---

## 自定义命令

### 文本高亮
```latex
\highlight{重要文本}  % 蓝色加粗
```

### 市场规模格式化
```latex
\marketsize{452 亿元}   % 输出：绿色 $452 亿元
```

### 增长率格式化
```latex
\growthrate{15.3}           % 输出：绿色 15.3%
```

### 风险指示器
```latex
\riskhigh{}     % 输出：红色"高"
\riskmedium{}   % 输出：橙色"中"
\risklow{}      % 输出：绿色"低"
```

### 评级星级（1-5）
```latex
\rating{4}      % 输出：★★★★☆
```

### 趋势指示器
```latex
\trendup{}      % 绿色上升三角
\trenddown{}    % 红色下降三角
\trendflat{}    % 灰色右箭头
```

---

## 表格格式

### 标准表格（交替行色）
```latex
\begin{table}[htbp]
\centering
\caption{按区域划分的市场规模}
\begin{tabular}{@{}lrrr@{}}
\toprule
\textbf{区域} & \textbf{规模} & \textbf{份额} & \textbf{复合年均增长率} \\\\
\midrule
北美 & 182 亿元 & 40.3\% & 12.5\% \\\\
\rowcolor{tablealt} 欧洲 & 121 亿元 & 26.8\% & 14.2\% \\\\
亚太 & 105 亿元 & 23.2\% & 18.7\% \\\\
\rowcolor{tablealt} 其他地区 & 44 亿元 & 9.7\% & 11.3\% \\\\
\midrule
\textbf{合计} & \textbf{452 亿元} & \textbf{100\%} & \textbf{15.3\%} \\\\
\bottomrule
\end{tabular}
\label{tab:regional}
\end{table}
```

### 带趋势指示器的表格
```latex
\begin{tabular}{@{}lrrl@{}}
\toprule
\textbf{企业} & \textbf{营收} & \textbf{份额} & \textbf{趋势} \\\\
\midrule
企业A & 52 亿元 & 15.3\% & \trendup{} +12\% \\\\
企业B & 48 亿元 & 14.1\% & \trenddown{} -3\% \\\\
企业C & 42 亿元 & 12.4\% & \trendflat{} +1\% \\\\
\bottomrule
\end{tabular}
```

---

## 图片格式

### 标准图片
```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{../figures/market_growth.png}
\caption{市场增长趋势（2020-2030）}
\label{fig:growth}
\end{figure}
```

### 带来源标注的图片
```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{../figures/market_share.png}
\caption{市场份额分布（2024）}
\figuresource{企业年报、行业分析}
\label{fig:market_share}
\end{figure}
```

---

## 列表格式

### 无序列表
```latex
\begin{itemize}
    \item 第一项（自动蓝色圆点）
    \item 第二项
    \item 第三项
\end{itemize}
```

### 有序列表
```latex
\begin{enumerate}
    \item 第一项（蓝色编号）
    \item 第二项
    \item 第三项
\end{enumerate}
```

### 嵌套列表
```latex
\begin{itemize}
    \item 主要观点
    \begin{itemize}
        \item 子观点 A
        \item 子观点 B
    \end{itemize}
    \item 另一主要观点
\end{itemize}
```

---

## 封面页

### 使用自定义标题命令
```latex
\makemarketreporttitle
    {报告标题}              % 报告标题
    {副标题}                % 副标题
    {../figures/cover.png}  % 封面图片（留空则不显示）
    {2025年1月}             % 日期
    {市场情报部}            % 编制方
```

### 手动封面页
详见模板中的完整手动封面页代码。

---

## 附录章节

```latex
\appendix

\chapter{研究方法}

\appendixsection{数据来源}
目录中显示的内容……
```

---

## 常见模式

### 市场概览模块
```latex
\begin{marketdatabox}[市场概览]
\begin{itemize}
    \item \textbf{当前市场规模：} \marketsize{452 亿元}
    \item \textbf{预测规模（2030）：} \marketsize{987 亿元}
    \item \textbf{复合年均增长率：} \growthrate{15.3}
    \item \textbf{最大细分领域：} 企业级（42\% 份额）
    \item \textbf{增长最快区域：} 亚太（\growthrate{22.1} 复合年均增长率）
\end{itemize}
\end{marketdatabox}
```

### 风险登记表摘要
```latex
\begin{table}[htbp]
\centering
\caption{风险评估摘要}
\begin{tabular}{@{}llccl@{}}
\toprule
\textbf{风险} & \textbf{类别} & \textbf{概率} & \textbf{影响} & \textbf{评级} \\\\
\midrule
市场颠覆 & 市场 & 高 & 高 & \riskhigh{} \\\\
\rowcolor{tablealt} 监管变化 & 监管 & 中 & 高 & \riskhigh{} \\\\
新进入者 & 竞争 & 中 & 中 & \riskmedium{} \\\\
\rowcolor{tablealt} 技术淘汰 & 技术 & 低 & 高 & \riskmedium{} \\\\
汇率波动 & 财务 & 中 & 低 & \risklow{} \\\\
\bottomrule
\end{tabular}
\end{table}
```

### 竞争对比表
```latex
\begin{table}[htbp]
\centering
\caption{竞争对比}
\begin{tabular}{@{}lccccc@{}}
\toprule
\textbf{因素} & \textbf{企业A} & \textbf{企业B} & \textbf{企业C} & \textbf{企业D} \\\\
\midrule
市场份额 & \rating{5} & \rating{4} & \rating{3} & \rating{2} \\\\
\rowcolor{tablealt} 产品质量 & \rating{4} & \rating{5} & \rating{3} & \rating{4} \\\\
价格竞争力 & \rating{3} & \rating{3} & \rating{5} & \rating{4} \\\\
\rowcolor{tablealt} 创新能力 & \rating{5} & \rating{4} & \rating{2} & \rating{3} \\\\
客户服务 & \rating{4} & \rating{4} & \rating{4} & \rating{5} \\\\
\bottomrule
\end{tabular}
\end{table}
```

---

## 常见问题

### 框内容溢出
如框内容超出页面范围，拆分为多个框或使用分页：
```latex
\newpage
\begin{keyinsightbox}[续……]
```

### 图片位置
使用 `[htbp]` 灵活放置，或使用 `[H]`（需 `float` 包）精确放置：
```latex
\begin{figure}[H]  % 需要 \usepackage{float}
```

### 表格过宽
使用 `\resizebox` 或 `adjustbox`：
```latex
\resizebox{\textwidth}{!}{
\begin{tabular}{...}
...
\end{tabular}
}
```

### 颜色未显示
确保 `xcolor` 包加载了 `[table]` 选项（已在样式文件中包含）。

---

## 编译

使用 XeLaTeX 编译以获得最佳效果：
```bash
xelatex report.tex
bibtex report
xelatex report.tex
xelatex report.tex
```

或使用 latexmk：
```bash
latexmk -xelatex report.tex
```
