# HTTP 直连回退 API（network-restricted 环境专用）

> 当 `fetch_market_data.py` 中所有 Python 引擎（AkShare/efinance/Baostock/yfinance）因网络限制全部失败时，使用本文件中的 HTTP 直连接口 + 网页抓取回退。

## 核心原则

Python 库需要直连特定域名（eastmoney.com、sina.com.cn、yahoofinance 等），这些域名可能在受限网络中被阻断。但代理的网络工具（search、web_fetch）走不同的出口，通常**不受同一限制**。因此：

```
Python 引擎全部失败 → 不回退到搜索 + HTTP 直连 + 网页抓取
```

## A股行情回退路径（已验证可行）

### 源1：雪球网页（web_fetch）

```
URL: https://xueqiu.com/S/SH600519
方法: mcp_ddg_mcp_fetch_content 或 mcp_tavily_tavily_extract
解析: 页面源码中包含价格数据，搜索 "¥" 或 "已收盘" 附近的数字
```

### 源2：腾讯证券 HTTP API（纯数据，无 JS 渲染）

```
URL: http://qt.gtimg.cn/q=sh600519
格式: v_sh600519="1~贵州茅台~600519~1303.00~..."
```

**字段解析（按 `~` 分割，索引从 0 开始）：**
```
[1]  = 名称     → 贵州茅台
[2]  = 代码     → 600519
[3]  = 最新价   → 1303.00       ← 核心字段
[4]  = 昨收     → 1273.38
[5]  = 今开     → 1268.02
[6]  = 成交量   → 82728
[30] = 涨跌额   → 29.62
[31] = 涨跌幅   → 2.33
[32] = 最高     → 1319.00
[33] = 最低     → 1250.10
[38] = PE(TTM)  → 19.73          ← 注意：字段索引 38，非直观位置
[43] = 总市值   → 16317.08       ← 单位：亿元
[44] = 流通市值 → 16317.08
[46] = PB       → 6.02
```

**代码前缀规则：**
- 上证（60xxxx）：`sh` — `http://qt.gtimg.cn/q=sh600519`
- 深证（00xxxx/30xxxx）：`sz` — `http://qt.gtimg.cn/q=sz000001`

### 源3：新浪财经 HTTP API

```
URL: http://hq.sinajs.cn/list=sh600519
格式: var hq_str_sh600519="贵州茅台,1303.00,1273.38,..."
字段: 名称, 今开, 昨收, 最新价, 最高, 最低, ...
```

注意：新浪 API 的字段顺序与腾讯不同，取数时必须对照。其中索引 3 是"最新价"。

### 港股代码

```
腾讯: http://qt.gtimg.cn/q=hk00700
新浪: http://hq.sinajs.cn/list=hk00700
```

## 实际案例：贵州茅台（600519）2026-05-27

```
Python 引擎结果: ❌ 全部失败（AkShare/efinance/Baostock）
回退路径:
  1. 雪球 web_fetch  → ¥1,303.00 ✅
  2. 腾讯 qt.gtimg.cn → ¥1,303.00 ✅
  3. 新浪（搜索片段）→ ¥1,273.38（仅前日收盘，今日不可用）

校验结论: ⚠️ 仅双源（雪球+腾讯），新浪仅能验证昨收
```

## 回退路径决策树

```
1. 尝试 fetch_market_data.py
   ├── 全部引擎成功 → 正常三源校验 ✅ 输出
   └── 全部引擎失败 →
       │
       2. 尝试 HTTP 直连接口
          ├── Tencent qt.gtimg.cn  → 源 A
          ├── Sina hq.sinajs.cn   → 源 B
          └── 至少 1 个成功 →
              │
              3. web_fetch 第三方财经网站
                 ├── 雪球 xueqiu.com/S/SHxxxxxx → 源 C
                 ├── 东方财富（通常 JS 渲染不可用）
                 └── 新浪财经网页版 → 源 C
              │
              4. 三源交叉比对
                 ├── 3 源一致 → ✅ 输出
                 ├── 2 源一致 → ⚠️ 输出 + 标注仅双源
                 └── 仅 1 源 → ❌ 输出 + 标注无法验证
```

## 已知局限

- 腾讯/Sina HTTP API 仅提供**实时行情**（当前价、涨跌幅、PE、市值），不提供 K 线历史和财务数据
- 网页抓取新浪/东方财富通常返回 JS 模板占位符（`@now@`、`@change@`），不可解析
- 港股/美股的 HTTP API 回退路径待验证
- HTTP API 无官方文档，字段索引可能随版本变动
