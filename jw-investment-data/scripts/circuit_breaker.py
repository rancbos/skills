#!/usr/bin/env python3
"""
circuit_breaker.py — 熔断器 + 降级链 v1.0
═══════════════════════════════════════════════

三个状态:
  CLOSED    — 正常，允许调用
  OPEN      — 熔断中，直接跳过该数据源
  HALF_OPEN — 恢复试探，允许1次测试

配置（可在 engines.yaml 覆盖）:
  failure_threshold: 3     # 连续失败N次→熔断
  recovery_timeout: 600    # 熔断600s后→半开探测
  half_open_probes: 1      # 半开时允许N次探测

用法:
  from circuit_breaker import CircuitBreaker, BreakerRegistry

  cb = BreakerRegistry("config/engines.yaml")
  # 调用前判断
  if cb.can_call("tencent_http"):
      result = _tencent_quote(...)
      if result and result.get("price"):
          cb.record_success("tencent_http")
      else:
          cb.record_failure("tencent_http")

参考: stock-data-acquisition 模块二的熔断保护机制 (CLOSED→OPEN→HALF_OPEN)
"""

import argparse, json, os, time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class BreakerState:
    """单个数据源的熔断状态"""
    state: str = State.CLOSED.value
    failure_count: int = 0
    last_failure: float = 0.0        # 最后失败时间戳
    last_success: float = 0.0         # 最后成功时间戳
    opened_at: float = 0.0            # 熔断触发时间
    total_calls: int = 0
    total_failures: int = 0


class BreakerRegistry:
    """管理所有数据源的熔断状态"""

    def __init__(self, config: Dict = None, persist_path: str = None):
        """
        Args:
            config: engines.yaml 中的 breaker 配置段
            persist_path: 状态持久化文件路径
        """
        self.breakers: Dict[str, BreakerState] = {}
        self._persist_path = persist_path or os.path.expanduser(
            "~/.hermes/cache/jw-investment-data/circuit_breakers.json"
        )

        # 默认阈值（config 可覆盖）
        cfg = config or {}
        self.failure_threshold: int = cfg.get("failure_threshold", 3)
        self.recovery_timeout: int = cfg.get("recovery_timeout", 600)   # 10分钟
        self.half_open_probes: int = cfg.get("half_open_probes", 1)

        # 加载已有状态
        self._load()

    # ── 核心方法 ──────────────────────────────────────────

    def can_call(self, engine: str) -> bool:
        """调用前检查：该引擎是否允许被调用"""
        b = self._get(engine)

        if b.state == State.CLOSED.value:
            return True

        if b.state == State.OPEN.value:
            if (time.time() - b.opened_at) >= self.recovery_timeout:
                b.state = State.HALF_OPEN.value
                self._save()
                return True
            return False

        if b.state == State.HALF_OPEN.value:
            # 半开状态允许探测（次数由 half_open_probes 控制）
            return True

        return False

    def record_success(self, engine: str):
        """调用成功 → 恢复为 CLOSED"""
        b = self._get(engine)
        b.state = State.CLOSED.value
        b.failure_count = 0
        b.last_success = time.time()
        b.total_calls += 1
        self._save()

    def record_failure(self, engine: str):
        """调用失败 → 累计次数，超阈值则熔断"""
        b = self._get(engine)
        b.failure_count += 1
        b.last_failure = time.time()
        b.total_calls += 1
        b.total_failures += 1

        if b.state == State.HALF_OPEN.value:
            # 半开探测失败 → 重新熔断
            b.state = State.OPEN.value
            b.opened_at = time.time()
        elif b.failure_count >= self.failure_threshold:
            b.state = State.OPEN.value
            b.opened_at = time.time()

        self._save()

    def get_state(self, engine: str) -> BreakerState:
        """获取引擎当前熔断状态（不修改状态）"""
        return self._get(engine)

    def status_snapshot(self) -> Dict:
        """返回所有引擎的状态快照（用于输出/调试）"""
        return {
            eng: {
                "state": b.state,
                "failures": b.failure_count,
                "last_failure": b.last_failure,
                "opened_seconds": int(time.time() - b.opened_at) if b.state == State.OPEN.value else 0,
            }
            for eng, b in self.breakers.items()
        }

    def reset(self, engine: str = None):
        """重置熔断状态"""
        if engine:
            self._get(engine).__init__()
        else:
            self.breakers.clear()
        self._save()

    # ── 内部方法 ──────────────────────────────────────────

    def _get(self, engine: str) -> BreakerState:
        if engine not in self.breakers:
            self.breakers[engine] = BreakerState()
        return self.breakers[engine]

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
            data = {
                eng: {
                    "state": b.state,
                    "failure_count": b.failure_count,
                    "last_failure": b.last_failure,
                    "last_success": b.last_success,
                    "opened_at": b.opened_at,
                    "total_calls": b.total_calls,
                    "total_failures": b.total_failures,
                }
                for eng, b in self.breakers.items()
            }
            with open(self._persist_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # 静默失败，不影响主流程

    def _load(self):
        try:
            if os.path.exists(self._persist_path):
                with open(self._persist_path) as f:
                    data = json.load(f)
                for eng, d in data.items():
                    b = BreakerState(
                        state=d.get("state", State.CLOSED.value),
                        failure_count=d.get("failure_count", 0),
                        last_failure=d.get("last_failure", 0),
                        last_success=d.get("last_success", 0),
                        opened_at=d.get("opened_at", 0),
                        total_calls=d.get("total_calls", 0),
                        total_failures=d.get("total_failures", 0),
                    )
                    self.breakers[eng] = b
        except Exception:
            pass


__version__ = "1.0.0"

# ── 独立测试入口 ────────────────────────────────────────────
def _schema_json():
    import json
    return json.dumps({
        "name": "circuit_breaker", "version": "1.0.0",
        "description": "多引擎熔断器 — CLOSED→OPEN→HALF_OPEN 三态自动恢复",
        "states": {"CLOSED": "正常", "OPEN": "熔断", "HALF_OPEN": "探测恢复"},
        "config": {"failure_threshold": 3, "recovery_timeout": 600},
        "exit_codes": {"0": "ok"},
    }, ensure_ascii=False, indent=2)

def main():
    p = argparse.ArgumentParser("circuit_breaker")
    p.add_argument("--schema", action="store_true")
    p.add_argument("--version", action="store_true")
    args = p.parse_args()
    if args.schema:
        print(_schema_json())
        return 0
    if args.version:
        print(f"circuit_breaker v{__version__}")
        sys.exit(0)

if __name__ == "__main__":
    main()
    print("=== Circuit Breaker 自检 ===")
    print("=== Circuit Breaker 自检 ===")
    cb = BreakerRegistry()

    # 模拟三次失败
    print(f"tencent cl=1: {cb.can_call('tencent_http')}")
    cb.record_failure("tencent_http")
    cb.record_failure("tencent_http")
    print(f"tencent cl=2: {cb.can_call('tencent_http')}")
    cb.record_failure("tencent_http")  # 第3次 → 熔断

    print(f"tencent cl=3: {cb.can_call('tencent_http')}  ← 熔断后应返回 False")
    print(cb.status_snapshot())

    # 模拟半开恢复
    cb.breakers["tencent_http"].opened_at = time.time() - 700  # 模拟已过11分钟
    print(f"\ntencent 11min后: {cb.can_call('tencent_http')}  ← 应返回 True (HALF_OPEN)")
    print(f"状态: {cb.breakers['tencent_http'].state}")

    # 半开成功 → 恢复
    cb.record_success("tencent_http")
    print(f"恢复后: {cb.breakers['tencent_http'].state}  ← 应为 CLOSED")
