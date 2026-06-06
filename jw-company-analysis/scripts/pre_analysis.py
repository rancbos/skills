#!/usr/bin/env python3
"""
jw-company-analysis: Step 0-2 预执行脚本
用途：预先获取数据并完成基础分析，生成检查点文件，减少 agent 执行时间
版本：v3.29.0（⚠️评分仅供参考，agent需补充：①industry_type判定②"求"框架评估③PEV/正常化PE等专用估值④管理层定性评估⑤逆向检查）

用法：
  python pre_analysis.py --symbol 600519 --market A
  python pre_analysis.py --symbol 0700.HK --market HK
  python pre_analysis.py --symbol AAPL --market US

输出：
  /root/data/.checkpoints/{symbol}_{date}/
  ├── step0_data.json       # 原始数据
  ├── step1_quality.json    # 企业质量基础评分
  ├── step2_financial.json  # 财务健康度基础评分
  └── checkpoint.json       # 完成状态
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path


def get_checkpoint_dir(symbol: str) -> Path:
    """获取检查点目录路径"""
    today = date.today().strftime("%Y%m%d")
    # 清理股票代码中的特殊字符用于目录名
    safe_symbol = symbol.replace(".", "_").replace("/", "_")
    checkpoint_dir = Path(f"/root/data/.checkpoints/{safe_symbol}_{today}")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir


def run_script(cmd: list[str], timeout: int = 60) -> dict | None:
    """运行外部脚本并返回 JSON 结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        else:
            print(f"  ⚠️ 脚本执行失败: {' '.join(cmd[:3])}...", file=sys.stderr)
            if result.stderr:
                print(f"    stderr: {result.stderr[:200]}", file=sys.stderr)
            return None
    except subprocess.TimeoutExpired:
        print(f"  ⏰ 脚本超时 ({timeout}s): {' '.join(cmd[:3])}...", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"  ❌ JSON 解析失败: {' '.join(cmd[:3])}...", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"  ❌ 脚本不存在: {cmd[0]}", file=sys.stderr)
        return None


def step0_fetch_data(symbol: str, market: str) -> dict:
    """Step 0: 数据获取"""
    print(f"\n{'='*60}")
    print(f"Step 0: 数据获取 - {symbol} ({market})")
    print(f"{'='*60}")

    data = {
        "symbol": symbol,
        "market": market,
        "fetch_time": datetime.now().isoformat(),
        "sources": {},
    }

    # 确定脚本路径
    scripts_dir = Path.home() / ".hermes" / "skills"

    if market == "A":
        # A股行情
        fetch_script = scripts_dir / "jw-investment-data" / "scripts" / "fetch_market_data.py"
        if fetch_script.exists():
            print("  📊 获取A股行情数据...")
            quote = run_script([
                "python", str(fetch_script),
                "--category", "quote",
                "--symbol", symbol,
                "--market", "A",
                "--format", "json",
            ])
            if quote:
                data["sources"]["quote"] = quote
                print(f"    ✅ 行情数据获取成功")

            # 财务数据
            print("  📈 获取财务数据...")
            financial = run_script([
                "python", str(fetch_script),
                "--category", "financial",
                "--symbol", symbol,
                "--market", "A",
                "--format", "json",
            ])
            if financial:
                data["sources"]["financial"] = financial
                print(f"    ✅ 财务数据获取成功")

            # K线数据
            print("  📉 获取K线数据...")
            kline = run_script([
                "python", str(fetch_script),
                "--category", "kline",
                "--symbol", symbol,
                "--market", "A",
                "--format", "json",
            ])
            if kline:
                data["sources"]["kline"] = kline
                print(f"    ✅ K线数据获取成功")
        else:
            print(f"  ⚠️ A股数据脚本不存在: {fetch_script}")

    elif market in ("HK", "US"):
        # 港美股
        fetch_script = scripts_dir / "jw-stock-value-analyzer" / "scripts" / "fetch_stock_data.py"
        if fetch_script.exists():
            print(f"  📊 获取{market}股行情数据...")
            stock_data = run_script([
                "python", str(fetch_script),
                "--symbol", symbol,
                "--market", market,
            ])
            if stock_data:
                data["sources"]["stock_data"] = stock_data
                print(f"    ✅ 行情数据获取成功")
        else:
            print(f"  ⚠️ 港美股数据脚本不存在: {fetch_script}")

    # 技术指标
    tech_script = scripts_dir / "jw-investment-data" / "scripts" / "technical_indicators.py"
    if tech_script.exists():
        print("  📐 获取技术指标...")
        tech = run_script([
            "python", str(tech_script),
            "--symbol", symbol,
            "--market", market,
        ])
        if tech:
            data["sources"]["technical"] = tech
            print(f"    ✅ 技术指标获取成功")

    # 数据完整性检查
    source_count = len(data["sources"])
    print(f"\n  📋 数据源获取: {source_count} 个")
    if source_count == 0:
        print("  ❌ 警告：未获取到任何数据源！")
    elif source_count < 2:
        print("  ⚠️ 警告：数据源不足，建议补充 web search 数据")

    return data


def step1_quality_basic(data: dict) -> dict:
    """Step 1: 企业质量基础评分（简化版，供 agent 参考）"""
    print(f"\n{'='*60}")
    print("Step 1: 企业质量基础评分（简化版）")
    print(f"{'='*60}")

    result = {
        "step": 1,
        "note": "基础评分仅供参考，需 agent 进一步分析确认",
        "scores": {},
        "notes": {},
        "data_gaps": [],
    }

    # 从数据中提取关键指标
    quote = data.get("sources", {}).get("quote", {})
    financial = data.get("sources", {}).get("financial", {})
    stock_data = data.get("sources", {}).get("stock_data", {})

    # 统一数据格式
    metrics = {}
    if quote:
        metrics.update({
            "market_cap": quote.get("market_cap") or quote.get("总市值"),
            "pe_ttm": quote.get("pe_ttm") or quote.get("PE-TTM"),
            "price": quote.get("price") or quote.get("最新价"),
        })
    if financial:
        metrics.update({
            "roe": financial.get("roe") or financial.get("ROE"),
            "revenue": financial.get("revenue") or financial.get("营业收入"),
            "net_profit": financial.get("net_profit") or financial.get("净利润"),
            "gross_margin": financial.get("gross_margin") or financial.get("毛利率"),
            "net_margin": financial.get("net_margin") or financial.get("净利率"),
            "revenue_growth": financial.get("revenue_growth") or financial.get("营收增速"),
            "profit_growth": financial.get("profit_growth") or financial.get("净利润增速"),
        })
    if stock_data:
        metrics.update({
            "market_cap": stock_data.get("market_cap"),
            "pe_ttm": stock_data.get("pe_ttm") or stock_data.get("trailingPE"),
            "price": stock_data.get("price") or stock_data.get("regularMarketPrice"),
            "roe": stock_data.get("roe") or stock_data.get("returnOnEquity"),
        })

    # 1.1 商业模式可理解性（简化判断）
    score_11 = 15  # 默认中等，需 agent 确认
    if metrics.get("revenue") and metrics.get("net_profit"):
        score_11 = 18  # 有基本数据，初步可理解
    result["scores"]["1.1_商业模式"] = score_11
    result["notes"]["1.1_商业模式"] = "⚠️待agent确认: 四问检验法+特许经营权判断"

    # 1.2 护城河（简化判断）
    score_12 = 12  # 默认中等
    roe = metrics.get("roe")
    if roe and isinstance(roe, (int, float)):
        if roe > 20:
            score_12 = 20
        elif roe > 15:
            score_12 = 17
        elif roe > 10:
            score_12 = 14
    result["scores"]["1.2_护城河"] = score_12
    result["notes"]["1.2_护城河"] = "⚠️待agent确认: 护城河类型+宽度+趋势评估"

    # 1.3 管理层（需 agent 深入分析）
    result["scores"]["1.3_管理层"] = 15
    result["notes"]["1.3_管理层"] = "⚠️待agent确认: 需web搜索管理层言论+荒岛两问+三重测试"
    result["data_gaps"].append("管理层数据需 web search 补充")

    # 1.4 成长性
    score_14 = 12
    rev_growth = metrics.get("revenue_growth")
    if rev_growth and isinstance(rev_growth, (int, float)):
        if rev_growth > 20:
            score_14 = 20
        elif rev_growth > 10:
            score_14 = 16
        elif rev_growth > 0:
            score_14 = 13
        else:
            score_14 = 8
    result["scores"]["1.4_成长性"] = score_14
    result["notes"]["1.4_成长性"] = "⚠️待agent确认: PEG+增长质量+困境反转判断"

    total = sum(result["scores"].values())
    result["total"] = total
    result["max"] = 100

    print(f"  1.1 商业模式: {result['scores']['1.1_商业模式']}/25")
    print(f"  1.2 护城河:   {result['scores']['1.2_护城河']}/25")
    print(f"  1.3 管理层:   {result['scores']['1.3_管理层']}/25 (需深入分析)")
    print(f"  1.4 成长性:   {result['scores']['1.4_成长性']}/25")
    print(f"  合计: {total}/100")
    if result["data_gaps"]:
        print(f"  ⚠️ 数据缺口: {', '.join(result['data_gaps'])}")

    return result


def step2_financial_basic(data: dict) -> dict:
    """Step 2: 财务健康度基础评分（简化版）"""
    print(f"\n{'='*60}")
    print("Step 2: 财务健康度基础评分（简化版）")
    print(f"{'='*60}")

    result = {
        "step": 2,
        "note": "基础评分仅供参考，需 agent 进一步分析确认",
        "scores": {},
        "notes": {},
        "data_gaps": [],
        "key_metrics": {},
    }

    # 提取财务数据
    financial = data.get("sources", {}).get("financial", {})
    stock_data = data.get("sources", {}).get("stock_data", {})

    metrics = {}
    if financial:
        metrics.update(financial)
    if stock_data:
        metrics.update({
            "roe": stock_data.get("roe") or stock_data.get("returnOnEquity"),
            "pe_ttm": stock_data.get("pe_ttm") or stock_data.get("trailingPE"),
        })

    # 2.1 盈利质量
    score_21 = 12
    roe = metrics.get("roe")
    if roe and isinstance(roe, (int, float)):
        if roe > 20:
            score_21 = 20
        elif roe > 15:
            score_21 = 17
        elif roe > 10:
            score_21 = 14
    result["scores"]["2.1_盈利质量"] = score_21
    result["data_gaps"].append("经营现金流/净利润、应收账款增速需财报数据")

    # 2.2 资产负债表
    score_22 = 12
    debt_ratio = metrics.get("debt_ratio") or metrics.get("资产负债率")
    if debt_ratio and isinstance(debt_ratio, (int, float)):
        if debt_ratio < 30:
            score_22 = 20
        elif debt_ratio < 50:
            score_22 = 16
        elif debt_ratio < 70:
            score_22 = 12
        else:
            score_22 = 8
    result["scores"]["2.2_资产负债表"] = score_22
    result["key_metrics"]["资产负债率"] = debt_ratio

    # 2.3 现金流
    score_23 = 10
    result["scores"]["2.3_现金流"] = score_23
    result["data_gaps"].append("经营现金流、FCF 需财报数据")

    # 2.4 财务趋势
    score_24 = 10
    rev_growth = metrics.get("revenue_growth") or metrics.get("营收增速")
    if rev_growth and isinstance(rev_growth, (int, float)):
        if rev_growth > 15:
            score_24 = 18
        elif rev_growth > 5:
            score_24 = 14
        elif rev_growth > 0:
            score_24 = 11
    result["scores"]["2.4_财务趋势"] = score_24

    total = sum(result["scores"].values())
    result["total"] = total
    result["max"] = 100

    print(f"  2.1 盈利质量:   {result['scores']['2.1_盈利质量']}/25")
    print(f"  2.2 资产负债表: {result['scores']['2.2_资产负债表']}/25")
    print(f"  2.3 现金流:     {result['scores']['2.3_现金流']}/25")
    print(f"  2.4 财务趋势:   {result['scores']['2.4_财务趋势']}/25")
    print(f"  合计: {total}/100")
    if result["data_gaps"]:
        print(f"  ⚠️ 数据缺口: {', '.join(result['data_gaps'])}")

    return result


def save_checkpoint(checkpoint_dir: Path, step: int, data: dict):
    """保存检查点"""
    filename = f"step{step}_{'data' if step == 0 else 'quality' if step == 1 else 'financial'}.json"
    filepath = checkpoint_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"  💾 检查点已保存: {filepath}")

    # 更新 checkpoint.json
    checkpoint_meta = {
        "last_step": step,
        "timestamp": datetime.now().isoformat(),
        "files": [f.name for f in checkpoint_dir.glob("step*.json")],
    }
    meta_path = checkpoint_dir / "checkpoint.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint_meta, f, ensure_ascii=False, indent=2)


def check_existing_checkpoint(checkpoint_dir: Path) -> int:
    """检查已有检查点，返回最后完成的步骤"""
    meta_path = checkpoint_dir / "checkpoint.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        last_step = meta.get("last_step", -1)
        print(f"  📂 发现已有检查点，最后完成步骤: Step {last_step}")
        return last_step
    return -1


def main():
    parser = argparse.ArgumentParser(
        description="jw-company-analysis Step 0-2 预执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pre_analysis.py --symbol 600519 --market A
  python pre_analysis.py --symbol 0700.HK --market HK
  python pre_analysis.py --symbol AAPL --market US
  python pre_analysis.py --symbol 600519 --market A --force  # 忽略已有检查点
        """,
    )
    parser.add_argument("--symbol", required=True, help="股票代码")
    parser.add_argument("--market", required=True, choices=["A", "HK", "US"], help="市场")
    parser.add_argument("--force", action="store_true", help="强制重新执行，忽略已有检查点")
    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print(f"# jw-company-analysis 预执行 v3.29.0")
    print(f"# 股票: {args.symbol} | 市场: {args.market}")
    print(f"{'#'*60}")

    checkpoint_dir = get_checkpoint_dir(args.symbol)

    # 检查已有检查点
    if not args.force:
        last_step = check_existing_checkpoint(checkpoint_dir)
        if last_step >= 2:
            print("  ✅ Step 0-2 已完成，使用 --force 强制重新执行")
            # 读取并输出已有结果
            for step in range(3):
                filename = f"step{step}_{'data' if step == 0 else 'quality' if step == 1 else 'financial'}.json"
                filepath = checkpoint_dir / filename
                if filepath.exists():
                    with open(filepath, "r", encoding="utf-8") as f:
                        result = json.load(f)
                    print(f"\n  Step {step} 结果已加载: {filepath}")
            return

    # Step 0: 数据获取
    start_step = max(0, check_existing_checkpoint(checkpoint_dir) + 1) if not args.force else 0

    if start_step <= 0:
        data = step0_fetch_data(args.symbol, args.market)
        save_checkpoint(checkpoint_dir, 0, data)
    else:
        # 加载已有数据
        data_path = checkpoint_dir / "step0_data.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    # Step 1: 企业质量基础评分
    if start_step <= 1:
        quality = step1_quality_basic(data)
        save_checkpoint(checkpoint_dir, 1, quality)
    else:
        print("  ⏭️ Step 1 已完成，跳过")

    # Step 2: 财务健康度基础评分
    if start_step <= 2:
        financial = step2_financial_basic(data)
        save_checkpoint(checkpoint_dir, 2, financial)

    print(f"\n{'='*60}")
    print("✅ 预执行完成！")
    print(f"检查点目录: {checkpoint_dir}")
    print(f"{'='*60}")
    print("\n下一步：agent 可从 Step 3 继续执行，或基于检查点数据深化 Step 0-2 分析。")


if __name__ == "__main__":
    main()
