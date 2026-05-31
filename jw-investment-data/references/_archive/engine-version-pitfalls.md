# 引擎版本陷阱与修复 (Engine Version Pitfalls)

> 本文档记录 `fetch_market_data.py` 各依赖库的版本兼容性问题及已验证的修复方案。
> 每次 `pip install --upgrade` 后参考本文档排查。

---

## 1. AkShare ≥1.18.0：全部旧接口被移除

**现象**：
```python
import akshare as ak
ak.stock_zh_a_spot_em()  # AttributeError: module 'akshare' has no attribute 'stock_zh_a_spot_em'
ak.stock_zh_a_hist()     # 同上
ak.stock_hk_spot_em()    # 同上
# 所有 stock_* 函数全部消失，dir(ak) 返回空列表
```

**根因**：AkShare 从 1.18.x 起重构了模块结构，旧版顶级函数全部改为子模块懒加载，但测试发现即使通过 `from akshare.stock import ...` 也无法导入（`unknown location` 错误）。

**阿里云镜像可用版本范围**：仅 1.16.72 ~ 1.18.63，全部属于新版。

**处理方案**：
- 本 Skill 的 v1.2 脚本已放弃 AkShare，改用 **腾讯 HTTP + Baostock + yfinance** 三引擎
- 如将来需要恢复 AkShare，需先确认新版 API 文档后重写所有接口调用

---

## 2. yfinance 1.4.0：`proxy=` 参数被移除

**现象**：
```python
import yfinance as yf
tk = yf.Ticker("0700.HK", proxy="http://127.0.0.1:7890")
# TypeError: Ticker.__init__() got an unexpected keyword argument 'proxy'
```

**验证**：
```python
import inspect, yfinance
print(list(inspect.signature(yfinance.Ticker).parameters.keys()))
# 输出: ['ticker', 'session']  — 没有 proxy
```

**修复方案**：改用 `session` 注入代理：
```python
import requests, yfinance as yf

session = requests.Session()
session.proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
tk = yf.Ticker("0700.HK", session=session)
```

本脚本中对应函数：`fetch_market_data.py` → `_yf_ticker()`

---

## 3. 腾讯 HTTP 接口 (qt.gtimg.cn)：GBK 编码

**现象**：
```python
r = subprocess.run(["curl", "-sS", qt_url], capture_output=True, text=True)
# UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb9
```

**根因**：腾讯服务器返回 GBK 编码的 HTTP 响应，但 `subprocess.run(text=True)` 默认用 UTF-8 解码。

**修复方案**：
```python
r = subprocess.run(["timeout", "8", "curl", "-sS", "-m", "5", url], capture_output=True)
# 不设 text=True，手动解码
raw_bytes = r.stdout
raw = raw_bytes.decode("gbk", errors="replace")
```

---

## 4. 东方财富 push2.eastmoney.com：IP 层拦截

**现象**：
```
urllib3.exceptions.ProtocolError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**诊断步骤**：
```bash
# TCP 三次握手成功
timeout 3 bash -c "echo x >/dev/tcp/push2.eastmoney.com/80" && echo OK  # → OK

# DNS 解析正常
nslookup push2.eastmoney.com  # → 61.129.129.196

# HTTP 请求被拒
curl -v http://push2.eastmoney.com/  # → Empty reply from server
```

**根因**：东方财富在应用层检测来源 IP，若命中黑名单则直接关闭连接（RemoteDisconnected），而非返回 HTTP 错误码。**TCP 层完全正常，是应用层的主动踢出。**

**影响范围**：所有依赖东方财富数据的 Python 库 — AkShare、efinance。

**解决方案**：
1. 配置代理（见 SKILL.md 代理章节）
2. 降级使用腾讯 HTTP + Baostock（不需要东方财富数据）
3. 使用 `mcp_ddg_mcp_fetch_content` 通过 DDG 代理抓取雪球数据

---

## 5. Yahoo Finance：限流机制

**现象**：
```
YFRateLimitError: Too Many Requests. Rate limited. Try after a while.
```

**特点**：
- 出现在同 IP 短时间内多次请求后
- 冷却时间通常 5-15 分钟
- 代理可彻底解决

**修复**：同 #2，用 session 注入代理后 yfinance 请求走代理 IP 出网。

---

## 6. pip 安装超时

**现象**：`pip install akshare` 等超时 120s+

**修复**：使用阿里云镜像
```bash
pip install akshare efinance baostock yfinance -i https://mirrors.aliyun.com/pypi/simple/
```
