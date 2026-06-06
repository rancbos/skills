#!/usr/bin/env python3
"""
output_contract.py — 标准化输出契约 v1.0
═════════════════════════════════════════════

统一所有脚本的输出格式，参照 cn-stock 的契约模式:
  {ok: bool, source: str, data: <payload>, error: {code, message, retryable}, ts: int}

扩展字段（jw-investment-data 专用）:
  - verification: 校验结果
  - meta: 元信息（延迟、引擎状态、熔断状态）

用法:
  from output_contract import envelope_ok, envelope_error

  # 成功
  result = envelope_ok(source="tencent_http", data={"price": 31.38})
  # → {"ok": true, "source": "tencent_http", "data": {...}, "ts": 1716800000}

  # 错误
  result = envelope_error(code=4, message="引擎无数据", source="akshare")
  # → {"ok": false, "source": "akshare", "error": {"code": 4, "message": "...", "retryable": true}, "ts": ...}

参考:
  - cn-stock SKILL.md: {ok, source, data, error, ts} 契约
  - daisy-financial-research: exit code 0/1/4/5 体系
  - stock-data-acquisition: 熔断状态记录
"""

import time
from typing import Any, Dict, Optional


# ═══════════════════════════════ 退出码 ═════════════════════
EXIT_CODES = {
    0: ("ok", "成功"),
    1: ("runtime_error", "运行时错误"),
    2: ("config_error", "配置/认证错误"),
    3: ("validation_error", "校验失败"),
    4: ("no_data", "无数据（所有引擎空）"),
    5: ("dependency_missing", "依赖缺失"),
}


def _now_ts() -> int:
    return int(time.time())


def envelope_ok(source: str, data: Any, meta: Dict = None) -> Dict:
    """构建成功信封

    Args:
        source: 数据来源标识 (e.g. "tencent_http", "baostock")
        data: 有效载荷
        meta: 可选元信息（延迟、引擎状态等）
    """
    envelope = {
        "ok": True,
        "source": source,
        "data": data,
        "ts": _now_ts(),
    }
    if meta:
        envelope["meta"] = meta
    return envelope


def envelope_error(
    code: int,
    message: str,
    source: str = "",
    retryable: bool = False,
    meta: Dict = None,
) -> Dict:
    """构建错误信封

    Args:
        code: 退出码 (0-5)
        message: 错误描述
        source: 出错的引擎名
        retryable: 是否可重试
        meta: 可选元信息
    """
    error_block = {
        "code": code,
        "message": message,
        "retryable": retryable,
    }

    if code in EXIT_CODES:
        error_block["type"] = EXIT_CODES[code][0]

    envelope = {
        "ok": False,
        "source": source or "unknown",
        "error": error_block,
        "ts": _now_ts(),
    }
    if meta:
        envelope["meta"] = meta
    return envelope


def combined_envelope(
    verification: Dict,
    results: Dict,
    errors: list,
    meta_overrides: Dict = None,
) -> Dict:
    """构建组合信封 — 用于多引擎查询的输出

    Args:
        verification: verify() 返回的校验结果
        results: 各引擎结果 {engine_name: {...}}
        errors: 错误列表 ["engine: reason", ...]
        meta_overrides: 额外元信息
    """
    meta = {
        "latency_ms": meta_overrides.pop("latency_ms", 0) if meta_overrides else 0,
        "engines_queried": len(results) + len(errors),
        "engines_success": len(results),
        "verification": verification,
    }
    if meta_overrides:
        meta.update(meta_overrides)

    return {
        "ok": verification.get("confidence", "low") != "low",
        "source": ",".join(results.keys()) if results else "none",
        "data": {
            "results": results,
            "errors": errors,
        },
        "verification": verification,
        "meta": meta,
        "ts": _now_ts(),
    }


# ═══════════════════════════════ 自描述 ═════════════════════
def schema_json() -> Dict:
    """返回本模块的自描述"""
    return {
        "name": "output_contract",
        "version": "1.0.0",
        "envelope_format": {
            "success": {"ok": True, "source": "str", "data": "<any>", "ts": "int"},
            "error": {"ok": False, "source": "str", "error": {"code": "int", "message": "str", "retryable": "bool"}, "ts": "int"},
        },
        "exit_codes": EXIT_CODES,
    }


# ── 独立测试入口 ────────────────────────────────────────────
if __name__ == "__main__":
    import json

    print("=== 成功信封 ===")
    print(json.dumps(envelope_ok("tencent_http", {"price": 31.38}), ensure_ascii=False, indent=2))

    print("\n=== 错误信封 ===")
    print(json.dumps(envelope_error(4, "所有引擎无数据", source="akshare", retryable=True), ensure_ascii=False, indent=2))

    print("\n=== 组合信封 ===")
    v = {"status": "✅ 3源一致(2独立)", "confidence": "high", "adopted_value": 31.38}
    e = ["baidu: 需 pip install adata"]
    print(json.dumps(combined_envelope(v, {"tencent": {"price": 31.38}}, e, {"latency_ms": 234}), ensure_ascii=False, indent=2))
