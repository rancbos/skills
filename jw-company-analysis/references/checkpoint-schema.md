# 检查点 JSON 结构

> 每步结束时将中间结果写入临时文件，支持从中断处恢复。

## 文件路径

```
/root/data/.checkpoints/{股票代码}_{YYYYMMDD}/
├── step0_data.json        # Step 0 数据准备结果
├── step0_macro.json       # Step 0.5 宏观环境评估结果
├── step1_quality.json     # Step 1 企业质量评分
├── step2_financial.json   # Step 2 财务健康度评分
├── step3_industry.json    # Step 3 产业链评分
├── step4_valuation.json   # Step 4 估值结果
├── step5_reverse.json     # Step 5 逆向检查结果
├── step6_technical.json   # Step 6 技术面信号
├── step7_conclusion.json  # Step 7 综合结论
└── checkpoint.json        # 最后完成的步骤编号+时间戳+文件列表
```

## checkpoint.json 结构

```json
{
  "last_step": 3,
  "timestamp": "2026-06-05T10:30:00",
  "symbol": "600519",
  "market": "A",
  "files": ["step0_data.json", "step0_macro.json", "step1_quality.json", "step2_financial.json"],
  "pre_analysis": false,
  "version": "3.29.0"
}
```

**字段说明**：
- `last_step`：最后完成的步骤编号（0-7）
- `timestamp`：ISO格式时间戳
- `symbol`：股票代码
- `market`：市场（A/HK/US）
- `files`：已生成的step文件列表
- `pre_analysis`：是否由pre_analysis.py生成（true时agent需在Step 1-2基础上做定性分析）
- `version`：SKILL.md版本号（用于检查点兼容性）

## 各Step JSON结构

```json
// step0_data.json（pre_analysis.py生成）
{
  "symbol": "600519",
  "market": "A",
  "fetch_time": "2026-06-05T10:30:00",
  "sources": {
    "quote": {"price": 1500, "market_cap": 20000, "pe_ttm": 30},
    "financial": {"roe": 25, "revenue": 1000, "net_profit": 500},
    "stock_data": {},
    "events": []
  },
  "validation": {"quote_sources": 3, "conflicts": 0}
}

// step0_macro.json（agent在Step 0.5生成）
{
  "macro_snapshot": {
    "cycle_stage": "复苏/过热/滞胀/衰退",
    "kondratieff_wave": "回升/繁荣/衰退/萧条",
    "risk_level": "低/中/高/极高",
    "key_risks": ["风险1", "风险2"],
    "industry_positioning": "建议关注/谨慎/回避的行业方向",
    "asset_allocation_hint": "股票/债券/商品/现金偏好"
  }
}

// step1_quality.json（pre_analysis.py生成基础版，agent需深化）
{
  "step": 1,
  "note": "基础评分仅供参考，需 agent 进一步分析确认",
  "scores": {
    "1.1_商业模式": 18,
    "1.1_note": "⚠️待agent确认: 基于营收/利润数据推断，需四问检验法+特许经营权判断",
    "1.2_护城河": 20,
    "1.2_note": "⚠️待agent确认: 基于ROE>20推断，需护城河类型/宽度/趋势评估",
    "1.3_管理层": 15,
    "1.3_note": "⚠️待agent确认: 默认15分，需荒岛两问+三重测试+web search补充",
    "1.4_成长性": 16,
    "1.4_note": "⚠️待agent确认: 基于营收增速推断，需PEG+增长质量判断"
  },
  "total": 69,
  "max": 100,
  "data_gaps": ["管理层数据需 web search 补充"]
}

// step2_financial.json（pre_analysis.py生成基础版，agent需深化）
{
  "step": 2,
  "scores": {
    "2.1_盈利质量": 20,
    "2.2_资产负债表": 18,
    "2.3_现金流": 19,
    "2.4_财务趋势": 17
  },
  "total": 74,
  "max": 100,
  "data_gaps": []
}

// step3_industry.json
{"position_score": 20, "bargaining_score": 18, "risk_score": 16, "trend_score": 19, "total": 73}

// step4_valuation.json
{"intrinsic_value": 1500, "margin_of_safety": 35, "valuation_trap_score": 25, "total": 82}

// step5_reverse.json
{"bias_score": -12, "reverse_check_score": 10, "market_mood_score": 5, "esg_score": 0, "total": 3}

// step6_technical.json
{"ma_signal": "🟢", "macd_signal": "⚪", "rsi_signal": "🟢", "boll_signal": "🟢🟢", "summary": "良好"}

// step7_conclusion.json
{"weighted_score": 78, "conclusion": "好标的", "risk_alerts": [], "position_advice": {}}
```

## 恢复逻辑

```
1. 读取 checkpoint.json
2. 如果 pre_analysis=true：
   - agent 从 Step 0.5 继续（宏观环境评估）
   - Step 1-2 的评分作为基础参考，agent 需进行定性分析并调整
3. 如果 pre_analysis=false：
   - agent 从 last_step+1 继续
   - 已有step文件作为中间结果
4. Step 0.5 恢复：如果 step0_macro.json 存在且 last_step >= 0，Step 0.5 可跳过
5. 如果任何step文件格式错误 → 忽略该文件，从对应步骤重新执行
6. 报告生成后，检查点文件保留7天后自动清理
```

## pre_analysis.py 输出对齐

pre_analysis.py 生成的step1_quality.json和step2_financial.json是**简化量化评分**，与SKILL.md的Step子步骤对应关系：

| pre_analysis.py 输出 | 对应 SKILL.md 子步骤 | agent 需深化 |
|---------------------|---------------------|-------------|
| 1.1_商业模式（基于营收/利润数据） | 1.1 商业模式可理解性 | 四问检验法 + 特许经营权判断 |
| 1.2_护城河（基于ROE） | 1.2 长期竞争优势/护城河 | 护城河类型/宽度/趋势评估 |
| 1.3_管理层（默认15分） | 1.3 管理层质量 | 荒岛两问 + 三重测试 + web search |
| 1.4_成长性（基于营收增速） | 1.4 成长性评估 | PEG + 增长质量判断 |
