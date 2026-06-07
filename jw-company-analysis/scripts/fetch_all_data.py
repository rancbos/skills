#!/usr/bin/env python3
"""
统一数据获取入口 v1.0
一次调用获取全部数据（行情+财务+技术+宏观），输出标准化JSON

用法：
  python3 fetch_all_data.py --symbol 000792 --market A
  python3 fetch_all_data.py --symbol 000792 --market A --output /path/to/output.json
  python3 fetch_all_data.py --symbol 000792 --market A --skip macro,technical

输出：JSON文件，包含以下字段：
  - quote: 行情数据（单源，异常时自动多源验证）
  - financial: 财务数据（comprehensive优先，fallback到financial）
  - technical: 技术指标（RSI/MACD/均线/布林带）
  - macro: 宏观环境（经济周期/利率/通胀/流动性）
  - metadata: 元数据（获取时间/数据源/降级标记）
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 超时配置（秒）
TIMEOUT_QUOTE = 25
TIMEOUT_FINANCIAL = 120
TIMEOUT_TECHNICAL = 15
TIMEOUT_MACRO = 30

# 脚本路径
SCRIPTS_DIR = Path(__file__).parent
JW_INVESTMENT_DATA = Path.home() / ".hermes/skills/rancbos-skills/jw-investment-data/scripts"
TRACK_BOLL_SCRIPT = SCRIPTS_DIR / "7track_boll.py"


def run_script(cmd, timeout=60, label=""):
    """运行脚本，返回 (success, output, error)"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            # 尝试解析JSON
            try:
                # 过滤掉非JSON行（如警告）
                lines = result.stdout.strip().split('\n')
                json_lines = [l for l in lines if l.strip().startswith('{') or l.strip().startswith('[')]
                if json_lines:
                    return True, json.loads('\n'.join(json_lines)), ""
                else:
                    return True, result.stdout, ""
            except json.JSONDecodeError:
                return True, result.stdout, ""
        else:
            return False, "", result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def fetch_quote(symbol, market):
    """获取行情数据（单源，异常时多源验证）"""
    print(f"[1/5] 获取行情数据...")
    
    # 主源：jw-data quote
    cmd = f"timeout {TIMEOUT_QUOTE} {JW_INVESTMENT_DATA}/jw-data quote {symbol}"
    success, output, error = run_script(cmd, TIMEOUT_QUOTE, "quote")
    
    if success:
        return {
            "data": output,
            "source": "jw-data",
            "tier": "🟢🟢🟢🟢",
            "degraded": False
        }
    
    # Fallback：fetch_market_data.py --category quote
    print(f"  [⚠️降级] jw-data quote 失败，尝试 fetch_market_data.py...")
    cmd = f"timeout {TIMEOUT_QUOTE} python3 {JW_INVESTMENT_DATA}/fetch_market_data.py --category quote --symbol {symbol} --market {market}"
    success, output, error = run_script(cmd, TIMEOUT_QUOTE, "quote_fallback")
    
    if success:
        return {
            "data": output,
            "source": "fetch_market_data.py",
            "tier": "🟢🟢🟢",
            "degraded": True,
            "degraded_reason": "jw-data quote 失败"
        }
    
    return {
        "data": None,
        "source": None,
        "tier": "🔴",
        "degraded": True,
        "degraded_reason": f"所有行情源失败: {error}"
    }


def fetch_financial(symbol, market):
    """获取财务数据（comprehensive优先，fallback到financial）"""
    print(f"[2/5] 获取财务数据...")
    
    # 主源：comprehensive（43列，60-120秒）
    cmd = f"timeout {TIMEOUT_FINANCIAL} python3 {JW_INVESTMENT_DATA}/fetch_market_data.py --category comprehensive --symbol {symbol} --market {market} 2>/dev/null"
    success, output, error = run_script(cmd, TIMEOUT_FINANCIAL, "comprehensive")
    
    if success:
        return {
            "data": output,
            "source": "comprehensive",
            "tier": "🟢🟢🟢🟢",
            "degraded": False
        }
    
    # Fallback：financial
    print(f"  [⚠️降级] comprehensive 失败，尝试 financial...")
    cmd = f"timeout {TIMEOUT_FINANCIAL} python3 {JW_INVESTMENT_DATA}/fetch_market_data.py --category financial --symbol {symbol} --market {market}"
    success, output, error = run_script(cmd, TIMEOUT_FINANCIAL, "financial")
    
    if success:
        return {
            "data": output,
            "source": "financial",
            "tier": "🟢🟢🟢",
            "degraded": True,
            "degraded_reason": "comprehensive 失败"
        }
    
    return {
        "data": None,
        "source": None,
        "tier": "🔴",
        "degraded": True,
        "degraded_reason": f"所有财务源失败: {error}"
    }


def fetch_technical(symbol, market):
    """获取技术指标（RSI/MACD/均线/布林带）"""
    print(f"[3/5] 获取技术指标...")
    
    result = {}
    
    # 技术指标
    cmd = f"timeout {TIMEOUT_TECHNICAL} {JW_INVESTMENT_DATA}/jw-data indicators {symbol}"
    success, output, error = run_script(cmd, TIMEOUT_TECHNICAL, "indicators")
    if success:
        result["indicators"] = {
            "data": output,
            "source": "jw-data indicators",
            "tier": "🟢🟢🟢"
        }
    
    # 七轨布林线
    cmd = f"timeout {TIMEOUT_TECHNICAL} python3 {TRACK_BOLL_SCRIPT} --symbol {symbol} --market {market} --json"
    success, output, error = run_script(cmd, TIMEOUT_TECHNICAL, "boll")
    if success:
        result["boll"] = {
            "data": output,
            "source": "7track_boll.py",
            "tier": "🟢🟢🟢"
        }
    
    if result:
        return {
            "data": result,
            "source": "multiple",
            "tier": "🟢🟢🟢",
            "degraded": False
        }
    
    return {
        "data": None,
        "source": None,
        "tier": "🔴",
        "degraded": True,
        "degraded_reason": f"技术指标获取失败: {error}"
    }


def fetch_macro():
    """获取宏观环境数据"""
    print(f"[4/5] 获取宏观数据...")
    
    cmd = f"timeout {TIMEOUT_MACRO} {JW_INVESTMENT_DATA}/jw-data macro all"
    success, output, error = run_script(cmd, TIMEOUT_MACRO, "macro")
    
    if success:
        return {
            "data": output,
            "source": "jw-data macro",
            "tier": "🟢🟢",
            "degraded": False
        }
    
    return {
        "data": None,
        "source": None,
        "tier": "🟡",
        "degraded": True,
        "degraded_reason": f"宏观数据获取失败: {error}"
    }


def fetch_profile(symbol, market):
    """获取公司概况"""
    print(f"[5/5] 获取公司概况...")
    
    cmd = f"timeout 15 python3 {JW_INVESTMENT_DATA}/fetch_market_data.py --category profile --symbol {symbol} --market {market}"
    success, output, error = run_script(cmd, 15, "profile")
    
    if success:
        return {
            "data": output,
            "source": "fetch_market_data.py profile",
            "tier": "🟢🟢🟢",
            "degraded": False
        }
    
    return {
        "data": None,
        "source": None,
        "tier": "🟡",
        "degraded": True,
        "degraded_reason": f"公司概况获取失败: {error}"
    }


def main():
    parser = argparse.ArgumentParser(description="统一数据获取入口")
    parser.add_argument("--symbol", required=True, help="股票代码")
    parser.add_argument("--market", default="A", help="市场（A/HK/US）")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--skip", help="跳过的数据类型（逗号分隔：quote,financial,technical,macro,profile）")
    parser.add_argument("--parallel", action="store_true", help="并行获取（实验性）")
    
    args = parser.parse_args()
    
    skip_types = set(args.skip.split(",")) if args.skip else set()
    
    print(f"=" * 60)
    print(f"统一数据获取入口 v1.0")
    print(f"股票代码：{args.symbol}")
    print(f"市场：{args.market}")
    print(f"跳过：{skip_types if skip_types else '无'}")
    print(f"=" * 60)
    
    start_time = time.time()
    
    # 获取各项数据
    result = {
        "symbol": args.symbol,
        "market": args.market,
        "fetch_time": datetime.now().isoformat(),
        "data": {}
    }
    
    if "quote" not in skip_types:
        result["data"]["quote"] = fetch_quote(args.symbol, args.market)
    
    if "financial" not in skip_types:
        result["data"]["financial"] = fetch_financial(args.symbol, args.market)
    
    if "technical" not in skip_types:
        result["data"]["technical"] = fetch_technical(args.symbol, args.market)
    
    if "macro" not in skip_types:
        result["data"]["macro"] = fetch_macro()
    
    if "profile" not in skip_types:
        result["data"]["profile"] = fetch_profile(args.symbol, args.market)
    
    # 统计降级情况
    degraded_count = sum(1 for d in result["data"].values() if d.get("degraded", False))
    total_count = len(result["data"])
    
    result["metadata"] = {
        "total_sources": total_count,
        "degraded_sources": degraded_count,
        "success_rate": f"{(total_count - degraded_count) / total_count * 100:.0f}%",
        "elapsed_seconds": round(time.time() - start_time, 1)
    }
    
    # 输出
    output_path = args.output or f"/tmp/fetch_all_data_{args.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 数据获取完成")
    print(f"耗时：{result['metadata']['elapsed_seconds']}秒")
    print(f"成功率：{result['metadata']['success_rate']}")
    print(f"降级数：{degraded_count}/{total_count}")
    print(f"输出文件：{output_path}")
    print(f"{'=' * 60}")
    
    # 返回路径供下游使用
    print(output_path)


if __name__ == "__main__":
    main()
