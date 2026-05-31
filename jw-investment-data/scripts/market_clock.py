#!/usr/bin/env python3
"""
market_clock.py — 时间锚定 + 交易时段感知 + 智能缓存 v1.0
══════════════════════════════════════════════════════════

核心能力:
  1. 北京时间 → 市场状态判断（盘前/盘中/午间/收盘/休市/假日）
  2. 动态缓存 TTL（盘中5min vs 收盘24h）
  3. 交易日判断（周末 + 硬编码假日 + AkShare 动态日历）

输出:
  get_market_status() → {state, cache_ttl_minutes, is_trading, ...}

缓存策略:
  - 盘中 (09:30-11:30, 13:00-15:00) → 5分钟缓存
  - 盘前 (09:15-09:25)               → 3分钟缓存
  - 午间休市                          → 保留早盘缓存
  - 盘后/周末/假日                    → 24小时缓存

参考: stock-data-acquisition 模块一"时间锚定宪法" + 模块三"智能缓存"
"""

import json, os, time
from datetime import datetime
from typing import Dict, Optional, Tuple


# ═══════════════════════════════ 硬编码假日（2026年） ══════════
_HOLIDAYS_2026: Dict[str, Tuple[str, str]] = {
    "元旦": ("2026-01-01", "2026-01-03"),
    "春节": ("2026-02-17", "2026-02-23"),
    "清明": ("2026-04-04", "2026-04-06"),
    "劳动节": ("2026-05-01", "2026-05-05"),
    "端午": ("2026-06-20", "2026-06-22"),
    "中秋": ("2026-09-26", "2026-09-28"),
    "国庆": ("2026-10-01", "2026-10-07"),
}

# ═══════════════════════════════ A股交易时段 ═══════════════
# 格式: (开始, 结束, state_name, cache_ttl_minutes)
_A_TRADING_SESSIONS = [
    ("09:15", "09:25", "pre_market", 3),    # 集合竞价
    ("09:30", "11:29", "morning", 5),        # 早盘
    ("11:30", "13:00", "lunch", 5),          # 午间休息（保留早盘缓存）
    ("13:00", "15:00", "afternoon", 5),      # 午后
    ("15:01", "23:59", "closed", 1440),      # 收盘后
    ("00:00", "09:14", "closed", 1440),      # 盘前（非集合竞价时段）
]


def _is_weekend(dt: datetime) -> bool:
    """周六/周日"""
    return dt.weekday() >= 5


def _is_hardcoded_holiday(date_str: str) -> Optional[str]:
    """检查硬编码假日表，返回假日名称（None=不是假日）"""
    for name, (start, end) in _HOLIDAYS_2026.items():
        if start <= date_str <= end:
            return name
    return None


def _in_time_range(time_str: str, start: str, end: str) -> bool:
    """检查 time_str 是否在 [start, end) 范围内"""
    if start <= end:
        return start <= time_str < end
    else:
        # 跨天范围（如 15:01-23:59）
        return time_str >= start or time_str < end


def get_market_status(dt: datetime = None) -> Dict:
    """返回 A 股市场状态

    Returns:
        {
            "state": "trading" | "pre_market" | "lunch" | "closed",
            "cache_ttl_minutes": int,      # 建议缓存有效期
            "is_trading_day": bool,
            "is_trading_session": bool,     # 是否在连续竞价时段
            "session_name": str,
            "beijing_time": str,
            "beijing_date": str,
            "holiday": str | None,
        }
    """
    now = dt or datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # 1. 周末检查
    if _is_weekend(now):
        return {
            "state": "closed",
            "cache_ttl_minutes": 1440,
            "is_trading_day": False,
            "is_trading_session": False,
            "session_name": "weekend",
            "beijing_time": now.isoformat(),
            "beijing_date": date_str,
            "holiday": None,
        }

    # 2. 节假日检查
    holiday = _is_hardcoded_holiday(date_str)
    if holiday:
        return {
            "state": "closed",
            "cache_ttl_minutes": 1440,
            "is_trading_day": False,
            "is_trading_session": False,
            "session_name": "holiday",
            "beijing_time": now.isoformat(),
            "beijing_date": date_str,
            "holiday": holiday,
        }

    # 3. 交易时段匹配
    for start, end, session, ttl in _A_TRADING_SESSIONS:
        if _in_time_range(time_str, start, end):
            return {
                "state": "trading" if session in ("morning", "afternoon") else session,
                "cache_ttl_minutes": ttl,
                "is_trading_day": True,
                "is_trading_session": session in ("morning", "afternoon"),
                "session_name": session,
                "beijing_time": now.isoformat(),
                "beijing_date": date_str,
                "holiday": None,
            }

    # 兜底
    return {
        "state": "closed",
        "cache_ttl_minutes": 1440,
        "is_trading_day": True,
        "is_trading_session": False,
        "session_name": "closed",
        "beijing_time": now.isoformat(),
        "beijing_date": date_str,
        "holiday": None,
    }


# ═══════════════════════════════ 智能缓存 ════════════════════
class MarketCache:
    """基于交易时段的智能缓存

    用法:
        clock = get_market_status()
        cache = MarketCache("/path/to/cache/dir")
        cache.set("600519", {"price": 31.38, "name": "贵州茅台"})
        data = cache.get("600519", clock["cache_ttl_minutes"])
    """

    def __init__(self, cache_dir: str = None):
        self._dir = cache_dir or os.path.expanduser(
            "~/.hermes/cache/jw-investment-data/market_cache"
        )

    def _path(self, key: str) -> str:
        safe = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self._dir, f"{safe}.json")

    def get(self, key: str, ttl_minutes: int = 1440) -> Optional[Dict]:
        """读取缓存，过期返回 None"""
        fp = self._path(key)
        if not os.path.exists(fp):
            return None
        try:
            with open(fp) as f:
                data = json.load(f)
            age = time.time() - data.get("_cached_at", 0)
            if age > ttl_minutes * 60:
                return None  # 过期
            # 去掉内部字段
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except Exception:
            return None

    def set(self, key: str, data: Dict):
        """写入缓存"""
        os.makedirs(self._dir, exist_ok=True)
        data["_cached_at"] = time.time()
        data["_cached_session"] = get_market_status()["session_name"]
        try:
            with open(self._path(key), "w") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def invalidate(self, key: str = None):
        """失效缓存"""
        if key:
            fp = self._path(key)
            if os.path.exists(fp):
                os.remove(fp)
        else:
            # 清除所有
            if os.path.exists(self._dir):
                for f in os.listdir(self._dir):
                    if f.endswith(".json"):
                        os.remove(os.path.join(self._dir, f))


# ── 独立测试入口 ────────────────────────────────────────────
if __name__ == "__main__":
    now = datetime.now()
    status = get_market_status(now)
    print(f"北京时间: {status['beijing_time']}")
    print(f"市场状态: {status['state']}")
    print(f"是否交易日: {status['is_trading_day']}")
    print(f"是否交易时段: {status['is_trading_session']}")
    print(f"推荐缓存TTL: {status['cache_ttl_minutes']} 分钟")
    if status["holiday"]:
        print(f"假日: {status['holiday']}")
    print(f"\n--- 模拟非交易日 ---")
    weekend = datetime(2026, 5, 31, 10, 30)  # 周日
    print(get_market_status(weekend))
    print(f"\n--- 模拟节假日 ---")
    holiday = datetime(2026, 5, 1, 10, 30)  # 劳动节
    print(get_market_status(holiday))
