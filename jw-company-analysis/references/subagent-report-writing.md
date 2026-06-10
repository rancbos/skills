# 子Agent报告写作最佳实践

> **场景**：jw-company-analysis 报告通常 1000-1500行/50-70KB，用 delegate_task 委托子agent撰写可节省父agent context 窗口。

## 委托模式

```
delegate_task(
  goal="Write a comprehensive investment analysis report for {公司名}({代码}) to {路径}",
  context="{所有采集到的数据，包含：行情、财务、研报、技术指标、宏观、近期事件}",
  toolsets=["terminal", "file"]
)
```

## Context 数据格式要求

在 context 中提供结构化数据块，包含：
- **KEY DATA**: 股票代码、当前价、总股本、市值、PE、PB
- **FINANCIAL DATA**: 3-5年关键财务指标（营收/净利/毛利率/净利率/ROE）
- **ANALYST CONSENSUS**: 评级、目标价、一致预期
- **COMPANY BACKGROUND**: 基本信息、发展历史
- **RECENT EVENTS**: 近30天事件（日期+事件+影响+来源）
- **MACRO DATA**: GDP/CPI/PMI/LPR
- **TECHNICAL**: MACD/RSI/布林带/七轨布林线
- **REPORT STRUCTURE**: 明确要求遵循的模板结构

## 必须包含的指令

在 goal 中明确要求：
1. "Use ALL the data below to write a COMPLETE report"
2. "Follow the exact structure specified"
3. "Every conclusion must have verifiable evidence (data + source label)"
4. "Use ASCII charts for key visualizations"
5. "Include 🟢🟢🟢🟢/🟢🟢🟢/🟢🟢/🟡/🔴 source labels"
6. "每个板块必须有风险分析"
7. "Report in Chinese"
8. ⚠️ "Step 5 逆向检查评分范围为 -50 到 +20（不是0-100），逆向调整分 = Step5得分 × 10% = -5到+2分。综合得分 = Step1×35% + Step2×20% + Step3×10% + Step4×25% + Step5得分×10%"

## ⚠️ 子agent反复犯的错误（必须在context中强调）

| 错误 | 正确做法 | 在context中怎么说 |
|------|---------|------------------|
| Step 5用0-100评分 | 用-50~+20评分 | "Step 5评分范围：-50到+20，不是0-100" |
| 综合得分漏算逆向调整分 | 必须加上Step5×10% | "综合得分必须包含Step5×10%的调整分" |
| read_file引入行号前缀 | 用terminal cat读取 | "读取文件用terminal cat，不要用read_file" |
| 信源标注缺失 | 每个定量数据必须标注 | "每个数字后面必须跟🟢🟡🔴信源标注" |

## 后处理检查清单

子agent报告生成后必须执行（按顺序）：

```bash
REPORT="/path/to/report.md"

# 1. 检查行号前缀污染（必做，两轮实战都触发过）
pollution=$(grep -c "^[0-9]*|" "$REPORT")
echo "行号污染行数: $pollution"
if [ "$pollution" -gt 0 ]; then
    sed -i 's/^[0-9]*|//' "$REPORT"
    echo "已修复"
fi

# 2. 验证章节完整性
for section in "Step 0" "Step 0.5" "Step 0.6" "Step 1" "Step 2" "Step 3" "Step 4" "Step 5" "Step 6" "Step 7" "Step 8" "信源索引"; do
    count=$(grep -c "$section" "$REPORT")
    echo "$section: $count"
done

# 3. 验证关键数据
grep -n "当前股价\|综合得分\|目标价\|PE.*倍\|股息率" "$REPORT"

# 4. ⚠️ 验证Step 5评分范围（必做，子agent常误用0-100而非-50~+20）
grep -n "Step 5\|逆向.*分\|安全阀\|风险控制" "$REPORT" | head -10
# 确认Step 5评分在 -50~+20 范围，逆向调整分 = Step5得分×10% = -5~+2

# 5. 验证综合得分公式
grep -A 5 "综合得分\|加权得分" "$REPORT"
# 确认：基础得分 = Step1×35% + Step2×20% + Step3×10% + Step4×25%
# 确认：综合得分 = 基础得分 + Step5得分×10%
```

## 常见问题

| 问题 | 症状 | 修复 |
|------|------|------|
| 行号前缀污染 | `1\|## 标题` | `sed -i 's/^[0-9]*\|//' file` |
| Step 5评分格式错 | 70/100 而非 -10/20 | 手动修正为 -50~+20 范围 |
| 综合得分计算错 | 缺少逆向调整分 | 添加 Step5得分×10% |
| 图表缺失 | 纯文字无ASCII图 | 补充关键图表 |
| 信源标注缺失 | 无🟢🟡🔴标记 | 补充数据来源标注 |
