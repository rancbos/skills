#!/usr/bin/env python3
"""
检查点管理器 v1.0
支持断点续传、Step重跑、检查点验证

用法：
  python3 checkpoint_manager.py --symbol 000792 --action status
  python3 checkpoint_manager.py --symbol 000792 --action save --step 2
  python3 checkpoint_manager.py --symbol 000792 --action load
  python3 checkpoint_manager.py --symbol 000792 --action restart --step 3
  python3 checkpoint_manager.py --symbol 000792 --action skip --step 5
  python3 checkpoint_manager.py --symbol 000792 --action validate
  python3 checkpoint_manager.py --symbol 000792 --action repair
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


# 检查点目录
CHECKPOINT_DIR = Path.home() / "data/.checkpoints"
FALLBACK_DIR = Path.home() / "data/.checkpoints"


def get_checkpoint_dir(symbol: str, date: str = None) -> Path:
    """获取检查点目录"""
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    checkpoint_dir = CHECKPOINT_DIR / f"{symbol}_{date}"
    
    # 尝试创建目录，失败则使用fallback
    try:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        checkpoint_dir = FALLBACK_DIR / f"{symbol}_{date}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    return checkpoint_dir


def get_checkpoint_path(symbol: str, date: str = None) -> Path:
    """获取检查点文件路径"""
    return get_checkpoint_dir(symbol, date) / "checkpoint.json"


def load_checkpoint(symbol: str, date: str = None) -> Dict:
    """加载检查点"""
    path = get_checkpoint_path(symbol, date)
    
    if not path.exists():
        return {
            "status": "no_checkpoint",
            "last_step": -1,
            "completed_steps": [],
            "output_files": {}
        }
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"警告：检查点文件损坏 - {e}", file=sys.stderr)
        return {
            "status": "corrupted",
            "last_step": -1,
            "completed_steps": [],
            "output_files": {}
        }


def save_checkpoint(symbol: str, step: int, output_file: str = None, date: str = None) -> Dict:
    """保存检查点"""
    checkpoint = load_checkpoint(symbol, date)
    
    # 更新检查点
    checkpoint["status"] = "in_progress"
    checkpoint["last_step"] = step
    checkpoint["last_step_time"] = datetime.now().isoformat()
    
    if step not in checkpoint["completed_steps"]:
        checkpoint["completed_steps"].append(step)
        checkpoint["completed_steps"].sort()
    
    if output_file:
        checkpoint["output_files"][f"step{step}"] = output_file
    
    # 检查是否所有Step完成
    required_steps = [0, 0.5, 0.6, 1, 2, 3, 4, 5, 6, 7, 8]
    if all(s in checkpoint["completed_steps"] for s in required_steps):
        checkpoint["status"] = "completed"
        checkpoint["completed_time"] = datetime.now().isoformat()
    
    # 保存
    path = get_checkpoint_path(symbol, date)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    return checkpoint


def restart_from_step(symbol: str, step: int, date: str = None) -> Dict:
    """从指定Step重新开始"""
    checkpoint = load_checkpoint(symbol, date)
    
    # 清除该Step及之后的所有完成记录
    checkpoint["completed_steps"] = [s for s in checkpoint["completed_steps"] if s < step]
    checkpoint["last_step"] = step - 1
    checkpoint["status"] = "in_progress"
    
    # 清除该Step及之后的输出文件
    keys_to_remove = [k for k in checkpoint["output_files"].keys() if int(k.replace("step", "")) >= step]
    for key in keys_to_remove:
        del checkpoint["output_files"][key]
    
    # 保存
    path = get_checkpoint_path(symbol, date)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    return checkpoint


def skip_step(symbol: str, step: int, date: str = None) -> Dict:
    """跳过指定Step"""
    checkpoint = load_checkpoint(symbol, date)
    
    # 标记Step为已完成（跳过）
    if step not in checkpoint["completed_steps"]:
        checkpoint["completed_steps"].append(step)
        checkpoint["completed_steps"].sort()
    
    checkpoint["last_step"] = max(checkpoint["completed_steps"])
    checkpoint["skipped_steps"] = checkpoint.get("skipped_steps", [])
    if step not in checkpoint["skipped_steps"]:
        checkpoint["skipped_steps"].append(step)
        checkpoint["skipped_steps"].sort()
    
    # 保存
    path = get_checkpoint_path(symbol, date)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    return checkpoint


def validate_checkpoint(symbol: str, date: str = None) -> Dict:
    """验证检查点完整性"""
    checkpoint = load_checkpoint(symbol, date)
    
    issues = []
    warnings = []
    
    # 检查状态
    if checkpoint["status"] == "no_checkpoint":
        issues.append("检查点不存在")
    elif checkpoint["status"] == "corrupted":
        issues.append("检查点文件损坏")
    
    # 检查输出文件是否存在
    for step_key, file_path in checkpoint.get("output_files", {}).items():
        if not os.path.exists(file_path):
            issues.append(f"{step_key} 输出文件不存在: {file_path}")
    
    # 检查Step连续性
    completed = sorted(checkpoint.get("completed_steps", []))
    if completed:
        expected = list(range(0, max(completed) + 1))
        missing = [s for s in expected if s not in completed]
        if missing:
            warnings.append(f"Step不连续，缺失: {missing}")
    
    # 检查依赖关系
    step_deps = {
        0.5: [0],
        0.6: [0],
        1: [0, 0.5, 0.6],
        2: [0, 1],
        3: [0, 1, 2],
        4: [0, 1, 2, 3, 0.6],
        5: [1, 2, 3, 4],
        6: [0, 4, 5],
        7: [1, 2, 3, 4, 5, 6],
        8: [7]
    }
    
    for step, deps in step_deps.items():
        if step in completed:
            missing_deps = [d for d in deps if d not in completed]
            if missing_deps:
                issues.append(f"Step {step} 依赖未满足: {missing_deps}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "checkpoint": checkpoint
    }


def repair_checkpoint(symbol: str, date: str = None) -> Dict:
    """修复检查点"""
    validation = validate_checkpoint(symbol, date)
    
    if validation["valid"]:
        return {"repaired": False, "message": "检查点无需修复"}
    
    checkpoint = validation["checkpoint"]
    repairs = []
    
    # 修复缺失的Step依赖
    step_deps = {
        0.5: [0],
        0.6: [0],
        1: [0, 0.5, 0.6],
        2: [0, 1],
        3: [0, 1, 2],
        4: [0, 1, 2, 3, 0.6],
        5: [1, 2, 3, 4],
        6: [0, 4, 5],
        7: [1, 2, 3, 4, 5, 6],
        8: [7]
    }
    
    completed = set(checkpoint.get("completed_steps", []))
    
    for step, deps in step_deps.items():
        if step in completed:
            missing_deps = [d for d in deps if d not in completed]
            if missing_deps:
                # 移除依赖未满足的Step
                completed.remove(step)
                repairs.append(f"移除Step {step}（依赖未满足: {missing_deps}）")
    
    checkpoint["completed_steps"] = sorted(list(completed))
    checkpoint["last_step"] = max(completed) if completed else -1
    
    # 保存修复后的检查点
    path = get_checkpoint_path(symbol, date)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    return {
        "repaired": True,
        "repairs": repairs,
        "checkpoint": checkpoint
    }


def print_status(checkpoint: Dict):
    """打印检查点状态"""
    print("=" * 60)
    print(f"检查点状态")
    print("=" * 60)
    print(f"状态：{checkpoint['status']}")
    print(f"最后完成Step：{checkpoint['last_step']}")
    print(f"完成时间：{checkpoint.get('last_step_time', 'N/A')}")
    
    if checkpoint.get("completed_steps"):
        print(f"已完成Step：{', '.join(map(str, checkpoint['completed_steps']))}")
    
    if checkpoint.get("skipped_steps"):
        print(f"跳过Step：{', '.join(map(str, checkpoint['skipped_steps']))}")
    
    if checkpoint.get("output_files"):
        print(f"\n输出文件：")
        for step, path in checkpoint["output_files"].items():
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"  {step}: {exists} {path}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="检查点管理器")
    parser.add_argument("--symbol", required=True, help="股票代码")
    parser.add_argument("--date", help="日期（YYYYMMDD），默认今天")
    parser.add_argument("--action", required=True,
                       choices=["status", "save", "load", "restart", "skip", "validate", "repair"],
                       help="操作类型")
    parser.add_argument("--step", type=float, help="Step编号")
    parser.add_argument("--output", help="输出文件路径（save操作）")
    
    args = parser.parse_args()
    
    if args.action == "status":
        checkpoint = load_checkpoint(args.symbol, args.date)
        print_status(checkpoint)
    
    elif args.action == "save":
        if args.step is None:
            print("错误：save操作需要指定--step", file=sys.stderr)
            sys.exit(1)
        checkpoint = save_checkpoint(args.symbol, args.step, args.output, args.date)
        print(f"✅ 检查点已保存：Step {args.step}")
        print_status(checkpoint)
    
    elif args.action == "load":
        checkpoint = load_checkpoint(args.symbol, args.date)
        print(json.dumps(checkpoint, ensure_ascii=False, indent=2))
    
    elif args.action == "restart":
        if args.step is None:
            print("错误：restart操作需要指定--step", file=sys.stderr)
            sys.exit(1)
        checkpoint = restart_from_step(args.symbol, args.step, args.date)
        print(f"✅ 已从Step {args.step}重新开始")
        print_status(checkpoint)
    
    elif args.action == "skip":
        if args.step is None:
            print("错误：skip操作需要指定--step", file=sys.stderr)
            sys.exit(1)
        checkpoint = skip_step(args.symbol, args.step, args.date)
        print(f"✅ 已跳过Step {args.step}")
        print_status(checkpoint)
    
    elif args.action == "validate":
        result = validate_checkpoint(args.symbol, args.date)
        print("=" * 60)
        print("检查点验证结果")
        print("=" * 60)
        print(f"有效性：{'✅ 有效' if result['valid'] else '❌ 无效'}")
        
        if result["issues"]:
            print(f"\n问题：")
            for issue in result["issues"]:
                print(f"  ❌ {issue}")
        
        if result["warnings"]:
            print(f"\n警告：")
            for warning in result["warnings"]:
                print(f"  ⚠️ {warning}")
        
        print("=" * 60)
    
    elif args.action == "repair":
        result = repair_checkpoint(args.symbol, args.date)
        if result["repaired"]:
            print("✅ 检查点已修复")
            for repair in result["repairs"]:
                print(f"  - {repair}")
            print_status(result["checkpoint"])
        else:
            print("✅ 检查点无需修复")


if __name__ == "__main__":
    main()

