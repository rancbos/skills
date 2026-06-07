# 脚本调用速查表

> **用途**：SKILL.md 中引用的脚本命令速查表，按需加载。

## A股脚本调用

```bash
# 公司概况
timeout 15 ~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/fetch_market_data.py --category profile --symbol {代码} --market A

# 基础行情（多源验证）
timeout 25 ~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/jw-data quote {代码}

# ⭐综合财务画像（adata 43列+预告/快报+营运+股本+概念，60-120秒）
timeout 180 ~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/fetch_market_data.py --category comprehensive --symbol {代码} --market A 2>/dev/null

# 宏观环境
~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/jw-data macro all

# 5年多维财务（可选补充）
timeout 180 ~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/fetch_market_data.py --category financial --symbol {代码} --market A

# 技术指标
~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/jw-data indicators {代码}

# ⭐七轨布林线
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/7track_boll.py --symbol {代码} --market A --json

# K线图
~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/jw-data chart {代码}

# 资金流向
timeout 30 ~/.hermes/skills/rancbos-skills/jw-investment-data/scripts/fetch_market_data.py --category capital_flow --symbol {代码} --market A
```

## 港美股脚本调用

```bash
python ~/.hermes/skills/rancbos-skills/jw-stock-value-analyzer/scripts/fetch_stock_data.py --symbol {代码} --market {HK/US}
```

## 图表自动生成脚本

```bash
# 关键财务指标仪表盘
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/generate_charts.py --type financial --data '{"revenue": 100, "profit": 20, "margin": 25, "roe": 15}'

# 估值区间图
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/generate_charts.py --type valuation --data '{"conservative": 23.5, "neutral": 33.2, "optimistic": 42.4, "current": 29.45}'

# 技术信号综合评估
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/generate_charts.py --type technical --data '{"boll_position": 31.43, "rsi": 27.44, "macd": "bearish", "ma": "bearish"}'

# 一致预期分布图
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/generate_charts.py --type consensus --data '{"buy": 8, "hold": 2, "sell": 0, "target_prices": [35, 40, 43, 45, 48]}'

# 周期定位仪表盘
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/generate_charts.py --type cycle --data '{"cycle": "复苏", "interest_rate": "宽松", "inflation": "温和", "liquidity": "充裕"}'
```

## 统一数据获取入口

```bash
# 一次获取全部数据（行情+财务+技术+宏观）
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/fetch_all_data.py --symbol {代码} --market A

# 跳过某些数据类型
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/fetch_all_data.py --symbol {代码} --market A --skip macro,technical

# 指定输出路径
python3 ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/fetch_all_data.py --symbol {代码} --market A --output /path/to/output.json
```

## baostock 财务数据字段名

baostock 的财务数据字段名与预期不同，正确字段名如下：
- 利润表：`gpMargin`（毛利率）、`npMargin`（净利率）、`roeAvg`（ROE）、`netProfit`（净利润）、`epsTTM`（EPS）、`MBRevenue`（营收）
- 成长能力：`YOYNI`（净利润同比增长率）、`YOYPNI`（扣非净利润同比增长率）、`YOYEquity`（净资产同比增长率）、`YOYAsset`（总资产同比增长率）
- 资产负债：`liabilityToAsset`（资产负债率）、`currentRatio`（流动比率）、`quickRatio`（速动比率）

