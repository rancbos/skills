#!/usr/bin/env python3
"""
横纵分析法中间产物保存/加载脚本。

用于保存研究过程中的中间结果，支持断点续做。

使用方法：
  # 快捷模式：生成模板文件（推荐）
  python save_checkpoint.py --quick "研究对象名"
  
  # 从文件保存中间产物
  python save_checkpoint.py --stage research --object "研究对象名" --data-file data.json
  
  # 从命令行保存中间产物
  python save_checkpoint.py --stage research --object "研究对象名" --data '{"sources": [...]}'
  
  # 加载中间产物
  python save_checkpoint.py --stage research --object "研究对象名" --load
  
  # 列出所有保存的检查点
  python save_checkpoint.py --list

阶段说明：
  - research (别名: info, search): 信息收集阶段
  - vertical (别名: history, time): 纵向分析阶段
  - horizontal (别名: compete, compare): 横向分析阶段
  - insight (别名: cross, merge): 横纵交汇阶段
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


# 检查点保存目录
CHECKPOINT_DIR = Path.home() / ".hermes" / "checkpoints" / "hv-analysis"

# 阶段别名映射
STAGE_ALIASES = {
    "info": "research",
    "search": "research",
    "history": "vertical",
    "time": "vertical",
    "compete": "horizontal",
    "compare": "horizontal",
    "cross": "insight",
    "merge": "insight",
}

# 各阶段模板
STAGE_TEMPLATES = {
    "research": {
        "sources": [],
        "key_facts": [],
        "timeline": [],
        "competitors": [],
        "notes": ""
    },
    "vertical": {
        "origin": "",
        "milestones": [],
        "decisions": [],
        "phases": [],
        "challenges": []
    },
    "horizontal": {
        "competitors": [],
        "comparison_matrix": {},
        "user_feedback": {},
        "market_position": "",
        "trends": []
    },
    "insight": {
        "historical_influence": "",
        "competitor_origins": "",
        "advantage_roots": [],
        "disadvantage_roots": [],
        "scenarios": {
            "most_likely": "",
            "most_dangerous": "",
            "most_optimistic": ""
        }
    }
}


def ensure_dir():
    """确保检查点目录存在。"""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def get_checkpoint_path(object_name: str, stage: str) -> Path:
    """获取检查点文件路径。"""
    # 清理对象名作为文件名
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in object_name)
    return CHECKPOINT_DIR / f"{safe_name}_{stage}.json"


def resolve_stage(stage_input: str) -> str:
    """解析阶段名称（支持别名）。"""
    if stage_input in STAGE_ALIASES:
        return STAGE_ALIASES[stage_input]
    if stage_input in ["research", "vertical", "horizontal", "insight"]:
        return stage_input
    return stage_input  # 返回原值，让后续验证处理


def save_checkpoint(object_name: str, stage: str, data: dict) -> str:
    """保存检查点。"""
    ensure_dir()
    
    checkpoint = {
        "object": object_name,
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }
    
    path = get_checkpoint_path(object_name, stage)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    return str(path)


def load_checkpoint(object_name: str, stage: str) -> dict | None:
    """加载检查点。"""
    path = get_checkpoint_path(object_name, stage)
    
    if not path.exists():
        print(f"❌ 检查点不存在: {path}")
        return None
    
    with open(path, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)
    
    return checkpoint


def list_checkpoints() -> list:
    """列出所有检查点。"""
    ensure_dir()
    
    checkpoints = []
    for path in sorted(CHECKPOINT_DIR.glob("*.json")):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                checkpoints.append({
                    "file": path.name,
                    "object": data.get("object", "未知"),
                    "stage": data.get("stage", "未知"),
                    "timestamp": data.get("timestamp", "未知"),
                })
        except Exception as e:
            checkpoints.append({
                "file": path.name,
                "object": "解析失败",
                "stage": "错误",
                "timestamp": str(e),
            })
    
    return checkpoints


def quick_start(object_name: str) -> None:
    """快捷模式：为所有阶段生成模板文件。"""
    ensure_dir()
    
    print(f"🚀 为「{object_name}」生成所有阶段模板...\n")
    
    created_files = []
    for stage, template in STAGE_TEMPLATES.items():
        path = get_checkpoint_path(object_name, stage)
        if path.exists():
            print(f"  ⏭️  {stage} 已存在，跳过")
        else:
            save_checkpoint(object_name, stage, template)
            created_files.append(str(path))
            print(f"  ✅ {stage}: {path}")
    
    print(f"\n📁 模板目录: {CHECKPOINT_DIR}")
    print(f"📝 共创建 {len(created_files)} 个模板文件")
    print("\n下一步：编辑这些 JSON 文件填充数据，然后运行：")
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in object_name)
    print(f"  python save_checkpoint.py --stage research --object \"{object_name}\" --data-file {CHECKPOINT_DIR / f'{safe_name}_research.json'}")


def main():
    parser = argparse.ArgumentParser(description='横纵分析法中间产物管理')
    parser.add_argument('--quick', help='快捷模式：为指定对象生成所有阶段模板')
    parser.add_argument('--stage', help='阶段 (research/vertical/horizontal/insight 或别名 info/history/compete/cross)')
    parser.add_argument('--object', help='研究对象名称')
    parser.add_argument('--data', help='要保存的JSON数据（字符串）')
    parser.add_argument('--data-file', help='要保存的JSON数据（文件路径）')
    parser.add_argument('--load', action='store_true', help='加载检查点')
    parser.add_argument('--list', action='store_true', help='列出所有检查点')
    
    args = parser.parse_args()
    
    # 快捷模式
    if args.quick:
        quick_start(args.quick)
        return
    
    # 列出检查点
    if args.list:
        checkpoints = list_checkpoints()
        if not checkpoints:
            print("📭 暂无保存的检查点")
        else:
            print(f"📋 共 {len(checkpoints)} 个检查点:\n")
            for cp in checkpoints:
                print(f"  • {cp['object']} [{cp['stage']}] - {cp['timestamp']}")
                print(f"    文件: {cp['file']}")
        return
    
    # 需要 object 和 stage
    if not args.object or not args.stage:
        print("❌ 需要指定 --object 和 --stage")
        print("💡 快捷模式：python save_checkpoint.py --quick \"研究对象名\"")
        parser.print_help()
        sys.exit(1)
    
    # 解析阶段名称
    stage = resolve_stage(args.stage)
    if stage not in ["research", "vertical", "horizontal", "insight"]:
        print(f"❌ 无效的阶段名称: {args.stage}")
        print("有效阶段: research, vertical, horizontal, insight")
        print("别名: info, search, history, time, compete, compare, cross, merge")
        sys.exit(1)
    
    # 加载检查点
    if args.load:
        checkpoint = load_checkpoint(args.object, stage)
        if checkpoint:
            print(f"✅ 加载检查点: {args.object} [{stage}]")
            print(f"   保存时间: {checkpoint['timestamp']}")
            print(f"\n📦 数据:\n{json.dumps(checkpoint['data'], ensure_ascii=False, indent=2)}")
        return
    
    # 保存检查点
    if args.data_file:
        # 从文件读取
        try:
            with open(args.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"❌ 文件不存在: {args.data_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {e}")
            sys.exit(1)
    elif args.data:
        # 从命令行读取
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {e}")
            sys.exit(1)
    else:
        print("❌ 需要指定 --data 或 --data-file 来保存数据")
        print("💡 快捷模式：python save_checkpoint.py --quick \"研究对象名\"")
        parser.print_help()
        sys.exit(1)
    
    path = save_checkpoint(args.object, stage, data)
    print(f"✅ 检查点已保存: {path}")


if __name__ == '__main__':
    main()
