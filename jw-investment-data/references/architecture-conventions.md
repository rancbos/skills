# jw-investment-data 架构约定

> v3.5.0 确立的架构模式。所有后续脚本开发遵循这些约定。

## 1. 脚本分层

```
用户入口层    jw-data (shell wrapper)
    ↓
业务脚本层    fetch_macro.py / fetch_market_data.py / technical_indicators.py
    ↓
展示层        format_macro.py / format_market.py  (Markdown渲染)
    ↓
基础设施层    circuit_breaker.py / market_clock.py / output_contract.py / health_check.py
```

**规则**：
- 展示层脚本只做格式化，不采集数据
- 业务脚本只做采集+调度，不做格式化
- 基础设施层无 `--schema` / `--version`（纯库模块，通过 import 使用）

## 2. 脚本标准化清单

每个**用户可调用的业务脚本**必须满足：

| 要求 | 检查方式 |
|:---|:---|
| `__version__ = "x.y.z"` | `python script.py --version` |
| `--schema` 输出 JSON 自描述 | `python script.py --schema` |
| `--force` 跳过缓存 | `python script.py --force` |
| `--format json|markdown` | 标准信封 + 人读可切换 |
| 标准信封 `{ok, source, data, error, ts}` | 使用 `output_contract.py` |

## 3. 配置外置原则

- TTL / 阈值 / 优先级 → `config/engines.yaml`
- 密钥 / token → 环境变量或 `.env`（永不写入 yaml）
- 硬编码常量仅作为 fallback 默认值

## 4. 错误处理

- API 失败不静默吞 → 聚合到 `_errors` 列表
- Markdown 输出末尾显式列表
- JSON 输出 `meta.errors` 字段

## 5. 统一入口 `jw-data`

```
jw-data macro <sub>     → fetch_macro.py --category <sub>
jw-data quote <sym>     → fetch_market_data.py --category quote --symbol <sym>
jw-data kline <sym> [d] → fetch_market_data.py --category kline ...
jw-data indicators <sym>→ technical_indicators.py ...
jw-data chart <sym>     → draw_kline.py ...
jw-data health          → health_check.py
jw-data schema          → 自描述
```

## 6. 缓存管理

- 目录：`~/.hermes/cache/jw-investment-data/macro/`
- TTL 源：`config/engines.yaml` → `macro.cache.*_ttl_days`
- 回退：脚本内置 hardcoded fallback
- `--force`：跳过缓存 + 重置熔断器

## 7. 版本号管理

- 所有业务脚本 `__version__` 跟随 skill 主版本号
- 基础设施脚本独立版本（`circuit_breaker v1.0.0`, `health_check v1.0.0`）
- SKILL.md 标题含版本号，更新日志按版本组织
