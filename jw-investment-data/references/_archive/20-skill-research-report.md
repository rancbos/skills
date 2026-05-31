# 20+ 投研数据 Skill 分析报告

> 2026-05-27，对 `/root/mydata/skills---/投研数据/` 下 20 个 skill 的系统性分析。
> v3.0 的熔断器、交易时钟、标准信封均源于此分析。

## 数据源全景

| 数据源 | 类型 | 认证 | 覆盖 | Skill 数 |
|--------|------|:--:|------|:--:|
| Baostock | Python库 | ❌ | A股 EOD | 3 |
| AkShare | Python库 | ❌ | 多市场 | 3 |
| Tushare Pro | HTTP API | ✅ | A/H/US | 3 |
| 聚宽 jqdatasdk | Python SDK | ✅ | A股 | 1 |
| 大虾皮 daxiapi | CLI | ✅ | A股 | 1 |
| 腾讯财经 | HTTP | ❌ | A/H 实时 | 2 |
| 新浪财经 | HTTP | ❌ | A/H 实时 + 五档 | 2 |
| Yahoo Finance | HTTP/Python | ❌(需代理) | 全球 | 2 |
| 通达信 TdxQuant | 本地客户端 | ❌ | 多市场 | 1 |
| sc-proxy | 透明代理 | ✅ 按次 | A股 | 1 |
| MCP (ClickHouse) | MCP协议 | ✅ JWT | 多市场 | 2 |
| WebSocket 实时 | WebSocket | ✅ Token | A/H 实时 | 1 |

## 调用方式模式

| 模式 | 代表 Skill | 优点 | 缺点 |
|------|-----------|------|------|
| Python import | baostock/tushare/jqdatasdk | 最直接 | 依赖库安装 |
| HTTP 裸调 | akshare-stock(腾讯) | 零依赖 | 需自处理错误 |
| MCP 协议 | stock-mcp-query | Agent 原生 | 需 MCP 服务 |
| 透明代理 | cn-stock(sc-proxy) | 调用方无感 | 依赖代理 |
| CLI 命令 | daxiapi | 语义化 | 需 npm/python |
| WebSocket | stock-rt-subscribe | 实时推送 | 需长连接 |

## 架构亮点（已落地到 v3.0）

| # | 模式 | 来源 | v3.0 落地 |
|---|------|------|----------|
| ① | 多源降级链 + 熔断器 | stock-data-acquisition | `circuit_breaker.py` |
| ② | 时间锚定 + 交易时段感知 | stock-data-acquisition | `market_clock.py` |
| ③ | 输出契约 `{ok, source, data, error, ts}` | cn-stock | `output_contract.py` |
| ④ | 自描述 `--schema` | daisy-financial | `fetch_market_data.py` |
| ⑤ | LRU 缓存 + 增量更新 | stock-backtest-simulator | `market_clock.py` MarketCache |
| ⑥ | 跨会话决策日志 | daisy dexter_memory_log | 远期 Phase 3 |

## 关键陷阱

| 陷阱 | 发现 | 解决 |
|------|------|------|
| BaoStock `rs.get_data()` 在 pandas 2.x 崩溃 | baostock SKILL.md | 改用 `while rs.next()` 手动迭代 |
| AkShare 首页仅200只，深市低价股漏检 | 实测 | 翻页兜底（最多20页） |
| 新浪 HTTP 超时，HTTPS 可用 | 实测 | 强制 HTTPS + Referer |
| 腾讯 GBK 编码，text=True 乱码 | 实测 | `decode('gbk', errors='replace')` |
| 雪球需先拿 cookie 再调 API | 实测 | 两步法，cookie 缓存30分钟 |
| yfinance 1.4 移除 `proxy=`，改用 `session=` | 实测 | `Ticker(symbol, session=proxied_session)` |

## 独特架构：cn-stock 透明代理模式

```
用户调用 → exports.py → sc-proxy(tushare插件) → api.tushare.pro
                ↑ fake token 被代理替换为真实 token
```

- **调用方无感**：只需传 fake token，代理替换后转发
- **按次计费**：透明代理层控制 billing，无需调用方管理额度
- **集中管理**：所有 Token 在代理层统一维护，零泄露风险
- **类比价值**：如果未来要对接多个付费 API，此模式比每脚本各管各的 Token 更安全可维护
