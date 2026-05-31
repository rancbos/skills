# 服务器网络诊断报告

> 日期：2026-05-27
> 目的：排查 jw-investment-data 各数据引擎不可用原因

## 诊断结论

**根因**：东方财富（push2.eastmoney.com）对这台服务器的 IP 做了应用层拒绝——TCP 握手成功，但收到 HTTP 请求后立即断开连接。不是网络不通，是 IP 黑名单。

## 逐引擎诊断结果

### ✅ 可用

| 引擎 | 连接地址 | 延迟 | 备注 |
|------|---------|------|------|
| Baostock | 114.94.20.73:10030 | <2s | 直连成功，EOD 数据 |
| 腾讯证券 HTTP | qt.gtimg.cn:80 | <2s | curl 直连成功，返回纯 JSON |
| 雪球网页 | xueqiu.com:443 | <5s | 通过 MCP web_fetch 可获取 |
| DDG MCP | 代理通道 | <10s | 走 DuckDuckGo 代理 |
| Tavily MCP | 代理通道 | <10s | 走 Tavily 代理 |
| Jin10 MCP | 专有通道 | <2s | 已接入 |

### ⚠️ 部分可用

| 引擎 | 原因 |
|------|------|
| 新浪财经 HTTP (hq.sinajs.cn) | curl 偶有超时（~5s），不稳定 |

### ❌ 不可用

| 引擎 | 失败模式 | 原因 |
|------|---------|------|
| AkShare | RemoteDisconnected | 东方财富 push2 服务端拒连 |
| efinance | RemoteDisconnected | 同上（底层同为东方财富 push2） |
| yfinance | Too Many Requests | Yahoo API 限流 |
| 东方财富网页 | Empty reply | 同上— IP 被拒 |

## 解决方案

### 方案一：代理 IP（推荐，彻底解决）

```bash
# 环境变量法（全局）
export HTTP_PROXY=http://代理IP:端口
export HTTPS_PROXY=http://代理IP:端口

# akshare-proxy 专用包
pip install akshare-proxy -i https://mirrors.aliyun.com/pypi/simple/

# yfinance 原生支持
yf.Ticker("AAPL", proxy="http://代理IP:端口")
```

### 方案二：多通道降级（无需代理，当前可行）

```
查询请求
  ├── 第1层：Baostock（唯一可用的 Python 引擎）
  ├── 第2层：腾讯 HTTP（curl 直连纯 JSON）
  ├── 第3层：MCP web_fetch（通过 DDG/Tavily 代理访问雪球/东方财富网页）
  └── 第4层：搜索兜底（mcp_tavily_tavily_search）
```

## 网络环境参数

- DNS: systemd-resolved (127.0.0.53)
- 外网: Ping 百度 ✅ (7ms)
- TCP 连通性: 所有目标端口 ✅
- HTTP 连通性: 部分目标被应用层拒绝
- pip 镜像: 阿里云 ✅ (mirrors.aliyun.com)
