# iTick 接口速查（备选，不必须安装）

> 官网: https://itick.io
> 特点：永久免费套餐，REST + WebSocket，A股/港股/美股实时行情 + 15年历史K线

## 注册

1. 访问 https://itick.io 注册账号
2. 获取免费 API Key
3. 免费套餐限制：基本满足个人量化需求

## 安装

```bash
pip install requests  # 仅需标准库，无专用 SDK
```

## REST API 用法

```python
import requests

API_KEY = "your_api_key_here"
headers = {"Authorization": f"Bearer {API_KEY}"}

# ── A股实时行情 ──
resp = requests.get(
    "https://api.itick.org/stock/tick",
    params={"region": "CN", "code": "600519"},
    headers=headers
)
data = resp.json()

# ── A股日K线 ──
resp = requests.get(
    "https://api.itick.org/stock/kline",
    params={
        "region": "CN",
        "code": "600519",
        "kType": 1,        # 1=日, 2=周, 3=月
        "limit": 100
    },
    headers=headers
)
data = resp.json()

# ── 港股 ──
resp = requests.get(
    "https://api.itick.org/stock/tick",
    params={"region": "HK", "code": "00700"},
    headers=headers
)

# ── 美股 ──
resp = requests.get(
    "https://api.itick.org/stock/tick",
    params={"region": "US", "code": "AAPL"},
    headers=headers
)
```

## WebSocket 实时推送

```python
import websocket
import json

ws = websocket.WebSocketApp(
    "wss://api.itick.org/iws",
    on_message=lambda ws, msg: print(json.loads(msg)),
)

# 鉴权
ws.send(json.dumps({"type": "auth", "token": API_KEY}))

# 订阅实时行情
ws.send(json.dumps({
    "type": "subscribe",
    "channel": "stock.tick",
    "symbols": ["CN.600519"]
}))

ws.run_forever()
```

## 优势

1. REST + WebSocket 双协议，实时性强
2. 免费用量对个人量化足够
3. A/港/美 三市场统一接口，JSON 格式标准化
4. 15 年历史 K 线

## 常见坑

1. 需要注册获取 API Key（非零门槛）
2. 免费套餐有调用频率限制
3. WebSocket 连接需保持心跳
