# Step 依赖关系图（v3.61.7 新增）

> **原则**：每个Step的输入/输出必须明确，依赖关系必须显式声明

## 一、Step 依赖关系总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Step 依赖关系图                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 0: 数据准备                                               │
│    │                                                            │
│    ├──→ Step 0.5: 公司背景                                      │
│    │      │                                                     │
│    │      └──→ Step 0.6: 宏观环境                               │
│    │             │                                              │
│    ▼             ▼                                              │
│  Step 1: 商业模式与企业质量 (35%)                                │
│    │                                                            │
│    ├──→ Step 2: 财务健康度 (20%)                                │
│    │      │                                                     │
│    │      └──→ Step 3: 产业链与价值链 (10%)                     │
│    │             │                                              │
│    ▼             ▼                                              │
│  Step 4: 估值与安全边际 (25%)                                    │
│    │                                                            │
│    ├──→ Step 5: 逆向检查 (安全阀)                               │
│    │      │                                                     │
│    │      └──→ Step 6: 技术面 (建仓时机)                        │
│    │             │                                              │
│    ▼             ▼                                              │
│  Step 7: 综合评分与投资结论                                      │
│    │                                                            │
│    └──→ Step 8: 交卷前自检 (强制后置)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 二、Step 依赖关系详细表

| Step | 名称 | 必须前置Step | 可选前置Step | 输出 | 下游依赖 |
|------|------|-------------|-------------|------|---------|
| Step 0 | 数据准备 | — | — | step0_data.json | Step 0.5, 0.6, 1, 2, 3, 4 |
| Step 0.5 | 公司背景 | Step 0 | — | company_background | Step 1, 7 |
| Step 0.6 | 宏观环境 | Step 0 | — | macro_context | Step 1, 4, 7 |
| Step 1 | 商业模式与企业质量 | Step 0, 0.5, 0.6 | — | step1_quality.json | Step 2, 3, 4, 5, 7 |
| Step 2 | 财务健康度 | Step 0, 1 | — | step2_financial.json | Step 3, 4, 5, 7 |
| Step 3 | 产业链与价值链 | Step 0, 1, 2 | — | step3_industry.json | Step 4, 5, 7 |
| Step 4 | 估值与安全边际 | Step 0, 1, 2, 3, 0.6 | — | step4_valuation.json | Step 5, 6, 7 |
| Step 5 | 逆向检查 | Step 1, 2, 3, 4 | — | step5_reverse.json | Step 6, 7 |
| Step 6 | 技术面 | Step 0, 4, 5 | — | step6_technical.json | Step 7 |
| Step 7 | 综合评分 | Step 1, 2, 3, 4, 5, 6 | — | step7_conclusion.json | Step 8 |
| Step 8 | 交卷前自检 | Step 7 | — | final_report.md | — |

## 三、Step 输入/输出规范

### Step 0: 数据准备
**输入**：股票代码、市场类型
**输出**：step0_data.json
```json
{
  "symbol": "000792",
  "market": "A",
  "industry_type": "周期-资源",
  "quote": {...},
  "financial": {...},
  "technical": {...},
  "macro": {...},
  "profile": {...}
}
```

### Step 0.5: 公司背景
**输入**：step0_data.json
**输出**：company_background
```json
{
  "basic_info": {...},
  "equity_structure": {...},
  "development_history": [...],
  "recent_events": [...]
}
```

### Step 0.6: 宏观环境
**输入**：step0_data.json
**输出**：macro_context
```json
{
  "cycle_stage": "复苏",
  "interest_rate": "宽松",
  "inflation": "温和",
  "liquidity": "充裕",
  "industry_impact": "利好"
}
```

### Step 1: 商业模式与企业质量
**输入**：step0_data.json, company_background, macro_context
**输出**：step1_quality.json
```json
{
  "business_model": {
    "score": 22,
    "four_questions": {...},
    "canvas": {...},
    "three_demands": "三求"
  },
  "moat": {
    "score": 20,
    "type": ["品牌", "成本优势"],
    "width": "宽",
    "trend": "稳定"
  },
  "management": {
    "score": 18,
    "capital_allocation": {...},
    "operation": {...},
    "integrity": {...}
  },
  "growth": {
    "score": 16,
    "drivers": [...],
    "quality": {...},
    "traps": [...]
  },
  "total": 76
}
```

### Step 2: 财务健康度
**输入**：step0_data.json, step1_quality.json
**输出**：step2_financial.json
```json
{
  "profit_quality": {
    "score": 20,
    "ocf_to_profit": 1.2,
    "cash_quality": "优"
  },
  "balance_sheet": {
    "score": 18,
    "debt_ratio": 15.85,
    "current_ratio": 2.5
  },
  "profitability": {
    "score": 16,
    "gross_margin": 68.72,
    "roe": 15.2,
    "roic": 12.5
  },
  "risk_analysis": {
    "score": 15,
    "risk_items": [...]
  },
  "total": 69
}
```

### Step 3: 产业链与价值链
**输入**：step0_data.json, step1_quality.json, step2_financial.json
**输出**：step3_industry.json
```json
{
  "industry_chain": {
    "upstream": {...},
    "midstream": {...},
    "downstream": {...},
    "company_position": "中游"
  },
  "value_chain": {
    "activities": [...],
    "cost_structure": {...},
    "profit_contribution": {...}
  },
  "five_forces": {
    "supplier_power": "中",
    "buyer_power": "高",
    "new_entrants": "低",
    "substitutes": "中",
    "rivalry": "高"
  },
  "total": 75
}
```

### Step 4: 估值与安全边际
**输入**：step0_data.json, step1_quality.json, step2_financial.json, step3_industry.json, macro_context
**输出**：step4_valuation.json
```json
{
  "method_selection": {
    "primary": "正常化PE",
    "secondary": "PB+产能市值比",
    "reason": "周期-资源行业"
  },
  "valuation_range": {
    "conservative": 23.5,
    "neutral": 33.2,
    "optimistic": 42.4,
    "current": 29.45
  },
  "safety_margin": {
    "margin": 11.3,
    "level": "偏低"
  },
  "traps": {
    "triggered": 0,
    "items": []
  },
  "total": 69
}
```

### Step 5: 逆向检查
**输入**：step1_quality.json, step2_financial.json, step3_industry.json, step4_valuation.json
**输出**：step5_reverse.json
```json
{
  "kill_thesis": [
    "碳酸锂价格持续低迷",
    "钾肥需求下降"
  ],
  "audit_opinion": "标准无保留",
  "pledge_ratio": 5.2,
  "red_flags": [],
  "adjustment": -2
}
```

### Step 6: 技术面
**输入**：step0_data.json, step4_valuation.json, step5_reverse.json
**输出**：step6_technical.json
```json
{
  "boll_position": 31.43,
  "rsi": 27.44,
  "macd": "bearish",
  "ma": "bearish",
  "signal_strength": "中",
  "suggestion": "小仓位试探"
}
```

### Step 7: 综合评分
**输入**：step1_quality.json, step2_financial.json, step3_industry.json, step4_valuation.json, step5_reverse.json, step6_technical.json
**输出**：step7_conclusion.json
```json
{
  "quality_score": 76,
  "financial_score": 69,
  "industry_score": 75,
  "valuation_score": 69,
  "reverse_adjustment": -2,
  "total_score": 71,
  "rating": "🟢好标的",
  "thesis": "...",
  "suggestion": "..."
}
```

### Step 8: 交卷前自检
**输入**：step7_conclusion.json, final_report.md
**输出**：final_report.md（已验证）
```json
{
  "data_verification": "✅",
  "conclusion_verification": "✅",
  "arithmetic_verification": "✅",
  "stress_test": "✅"
}
```

## 四、依赖关系检查规则

**执行前检查**：
1. 检查所有必须前置Step的输出文件是否存在
2. 检查输出文件格式是否正确
3. 检查关键字段是否完整

**检查失败处理**：
- 缺失前置Step → 自动执行缺失Step
- 格式错误 → 尝试修复或重新执行
- 字段缺失 → 标记降级，继续执行

## 五、断点续传支持

**检查点机制**：
- 每个Step完成后写入检查点
- 检查点包含：Step编号、完成时间、输出文件路径
- 支持从任意Step继续执行

**检查点格式**：
```json
{
  "status": "in_progress",
  "last_step": 2,
  "last_step_time": "2026-06-08T10:30:00",
  "completed_steps": [0, 0.5, 0.6, 1, 2],
  "output_files": {
    "step0": "/path/to/step0_data.json",
    "step1": "/path/to/step1_quality.json",
    "step2": "/path/to/step2_financial.json"
  }
}
```

