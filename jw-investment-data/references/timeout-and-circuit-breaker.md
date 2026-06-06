# 超时与熔断器机制

## 脚本超时设定

`fetch_market_data.py` 串行调用 8 个引擎，**无总超时**：

| 引擎 | 单引擎超时 | 实测耗时 |
|------|-----------|---------|
| tencent_http | timeout 8 + curl -m 5 + subprocess timeout=10 | ~0.3s |
| sina_https | 同上 | ~3s |
| baostock | subprocess timeout=10 | ~1s |
| akshare | requests.get timeout=8 | ~1s |
| baidu | timeout 8 + curl -m 5 + subprocess timeout=10 | ~2s |
| tushare | 同上 | ~2s |
| xueqiu | timeout 8 + curl -m 8 + subprocess timeout=10 | ~5s |
| yfinance | 带重试 retries=2 | ~10-30s |

**最坏情况**：8 × 10秒 = 80秒（首次调用，熔断器未触发时）

## 熔断器机制

- 每引擎独立追踪失败次数
- **3次连续失败 → OPEN（熔断）**，跳过该引擎
- **10分钟后自动 HALF_OPEN → 探测恢复**
- `--force` 可重置所有熔断器

熔断器状态查看：
```bash
cd ~/.hermes/skills/jw-investment-data/scripts
python3 circuit_breaker.py
```

## 已知问题

### 1. 首次调用超时

首次调用时所有引擎都会尝试（熔断器无历史），最坏80秒。

**解决方案**：外部调用必须用 `timeout 25` 包裹：
```bash
timeout 25 python3 fetch_market_data.py --category quote --symbol 600519 --force
```

### 2. technical_indicators.py VERSION 变量错误

**问题**：第246行使用 `VERSION` 而非 `__version__`，导致 Markdown 输出时 NameError。

**修复**：
```bash
sed -i 's/VERSION)/__version__)/g' ~/.hermes/skills/jw-investment-data/scripts/technical_indicators.py
```

### 3. xueqiu/yfinance 不可用

- xueqiu：需要 cookie 认证，无 cookie 时无数据
- yfinance：Yahoo Finance 限流，经常返回 "Too Many Requests"

这两个引擎失败不影响主流程，其他6个引擎足够。

## 降级策略

```
jw-investment-data 超时/报错
  → timeout 25 包裹（已内置到调用方 skill）
  → 超时后直接降级到 web search
  → 不要重试，浪费时间
```
