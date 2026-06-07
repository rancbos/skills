1|#!/usr/bin/env python3
2|"""
3|jw-company-analysis: Step 0-2 预执行脚本
4|用途：预先获取数据并完成基础分析，生成检查点文件，减少 agent 执行时间
5|版本：v3.60.7（⚠️评分仅供参考，agent需补充：①industry_type判定②"求"框架评估③PEV/正常化PE等专用估值④管理层定性评估⑤逆向检查）
6|
7|用法：
8|  python pre_analysis.py --symbol 600519 --market A
9|  python pre_analysis.py --symbol 0700.HK --market HK
10|  python pre_analysis.py --symbol AAPL --market US
11|
12|输出：
13|  /root/data/.checkpoints/{symbol}_{date}/
14|  ├── step0_data.json       # 原始数据
15|  ├── step1_quality.json    # 企业质量基础评分
16|  ├── step2_financial.json  # 财务健康度基础评分
17|  └── checkpoint.json       # 完成状态
18|"""
19|
20|import argparse
21|import json
22|import os
23|import subprocess
24|import sys
25|from datetime import datetime, date
26|from pathlib import Path
27|
28|
29|def get_checkpoint_dir(symbol: str) -> Path:
30|    """获取检查点目录路径"""
31|    today = date.today().strftime("%Y%m%d")
32|    # 清理股票代码中的特殊字符用于目录名
33|    safe_symbol = symbol.replace(".", "_").replace("/", "_")
34|    checkpoint_dir = Path(f"/root/data/.checkpoints/{safe_symbol}_{today}")
35|    checkpoint_dir.mkdir(parents=True, exist_ok=True)
36|    return checkpoint_dir
37|
38|
39|def run_script(cmd: list[str], timeout: int = 60) -> dict | None:
40|    """运行外部脚本并返回 JSON 结果"""
41|    try:
42|        result = subprocess.run(
43|            cmd,
44|            capture_output=True,
45|            text=True,
46|            timeout=timeout,
47|        )
48|        if result.returncode == 0 and result.stdout.strip():
49|            return json.loads(result.stdout)
50|        else:
51|            print(f"  ⚠️ 脚本执行失败: {' '.join(cmd[:3])}...", file=sys.stderr)
52|            if result.stderr:
53|                print(f"    stderr: {result.stderr[:200]}", file=sys.stderr)
54|            return None
55|    except subprocess.TimeoutExpired:
56|        print(f"  ⏰ 脚本超时 ({timeout}s): {' '.join(cmd[:3])}...", file=sys.stderr)
57|        return None
58|    except json.JSONDecodeError:
59|        print(f"  ❌ JSON 解析失败: {' '.join(cmd[:3])}...", file=sys.stderr)
60|        return None
61|    except FileNotFoundError:
62|        print(f"  ❌ 脚本不存在: {cmd[0]}", file=sys.stderr)
63|        return None
64|
65|
66|def step0_fetch_data(symbol: str, market: str) -> dict:
67|    """Step 0: 数据获取"""
68|    print(f"\n{'='*60}")
69|    print(f"Step 0: 数据获取 - {symbol} ({market})")
70|    print(f"{'='*60}")
71|
72|    data = {
73|        "symbol": symbol,
74|        "market": market,
75|        "fetch_time": datetime.now().isoformat(),
76|        "sources": {},
77|    }
78|
79|    # 确定脚本路径
80|    scripts_dir = Path.home() / ".hermes" / "skills" / "rancbos-skills"
81|
82|    if market == "A":
83|        # A股行情
84|        fetch_script = scripts_dir / "jw-investment-data" / "scripts" / "fetch_market_data.py"
85|        if fetch_script.exists():
86|            print("  📊 获取A股行情数据...")
87|            quote = run_script([
88|                "python", str(fetch_script),
89|                "--category", "quote",
90|                "--symbol", symbol,
91|                "--market", "A",
92|                "--format", "json",
93|            ])
94|            if quote:
95|                data["sources"]["quote"] = quote
96|                print(f"    ✅ 行情数据获取成功")
97|
98|            # 财务数据
99|            print("  📈 获取财务数据...")
100|            financial = run_script([
101|                "python", str(fetch_script),
102|                "--category", "financial",
103|                "--symbol", symbol,
104|                "--market", "A",
105|                "--format", "json",
106|            ])
107|            if financial:
108|                data["sources"]["financial"] = financial
109|                print(f"    ✅ 财务数据获取成功")
110|
111|            # K线数据
112|            print("  📉 获取K线数据...")
113|            kline = run_script([
114|                "python", str(fetch_script),
115|                "--category", "kline",
116|                "--symbol", symbol,
117|                "--market", "A",
118|                "--format", "json",
119|            ])
120|            if kline:
121|                data["sources"]["kline"] = kline
122|                print(f"    ✅ K线数据获取成功")
123|        else:
124|            print(f"  ⚠️ A股数据脚本不存在: {fetch_script}")
125|
126|    elif market in ("HK", "US"):
127|        # 港美股
128|        fetch_script = scripts_dir / "jw-stock-value-analyzer" / "scripts" / "fetch_stock_data.py"
129|        if fetch_script.exists():
130|            print(f"  📊 获取{market}股行情数据...")
131|            stock_data = run_script([
132|                "python", str(fetch_script),
133|                "--symbol", symbol,
134|                "--market", market,
135|            ])
136|            if stock_data:
137|                data["sources"]["stock_data"] = stock_data
138|                print(f"    ✅ 行情数据获取成功")
139|        else:
140|            print(f"  ⚠️ 港美股数据脚本不存在: {fetch_script}")
141|
142|    # 技术指标
143|    tech_script = scripts_dir / "jw-investment-data" / "scripts" / "technical_indicators.py"
144|    if tech_script.exists():
145|        print("  📐 获取技术指标...")
146|        tech = run_script([
147|            "python", str(tech_script),
148|            "--symbol", symbol,
149|            "--market", market,
150|        ])
151|        if tech:
152|            data["sources"]["technical"] = tech
153|            print(f"    ✅ 技术指标获取成功")
154|
155|    # 数据完整性检查
156|    source_count = len(data["sources"])
157|    print(f"\n  📋 数据源获取: {source_count} 个")
158|    if source_count == 0:
159|        print("  ❌ 警告：未获取到任何数据源！")
160|    elif source_count < 2:
161|        print("  ⚠️ 警告：数据源不足，建议补充 web search 数据")
162|
163|    return data
164|
165|
166|def step1_quality_basic(data: dict) -> dict:
167|    """Step 1: 企业质量基础评分（简化版，供 agent 参考）"""
168|    print(f"\n{'='*60}")
169|    print("Step 1: 企业质量基础评分（简化版）")
170|    print(f"{'='*60}")
171|
172|    result = {
173|        "step": 1,
174|        "note": "基础评分仅供参考，需 agent 进一步分析确认",
175|        "scores": {},
176|        "notes": {},
177|        "data_gaps": [],
178|    }
179|
180|    # 从数据中提取关键指标
181|    quote = data.get("sources", {}).get("quote", {})
182|    financial = data.get("sources", {}).get("financial", {})
183|    stock_data = data.get("sources", {}).get("stock_data", {})
184|
185|    # 统一数据格式
186|    metrics = {}
187|    if quote:
188|        metrics.update({
189|            "market_cap": quote.get("market_cap") or quote.get("总市值"),
190|            "pe_ttm": quote.get("pe_ttm") or quote.get("PE-TTM"),
191|            "price": quote.get("price") or quote.get("最新价"),
192|        })
193|    if financial:
194|        metrics.update({
195|            "roe": financial.get("roe") or financial.get("ROE"),
196|            "revenue": financial.get("revenue") or financial.get("营业收入"),
197|            "net_profit": financial.get("net_profit") or financial.get("净利润"),
198|            "gross_margin": financial.get("gross_margin") or financial.get("毛利率"),
199|            "net_margin": financial.get("net_margin") or financial.get("净利率"),
200|            "revenue_growth": financial.get("revenue_growth") or financial.get("营收增速"),
201|            "profit_growth": financial.get("profit_growth") or financial.get("净利润增速"),
202|        })
203|    if stock_data:
204|        metrics.update({
205|            "market_cap": stock_data.get("market_cap"),
206|            "pe_ttm": stock_data.get("pe_ttm") or stock_data.get("trailingPE"),
207|            "price": stock_data.get("price") or stock_data.get("regularMarketPrice"),
208|            "roe": stock_data.get("roe") or stock_data.get("returnOnEquity"),
209|        })
210|
211|    # 1.1 商业模式可理解性（简化判断）
212|    score_11 = 15  # 默认中等，需 agent 确认
213|    if metrics.get("revenue") and metrics.get("net_profit"):
214|        score_11 = 18  # 有基本数据，初步可理解
215|    result["scores"]["1.1_商业模式"] = score_11
216|    result["notes"]["1.1_商业模式"] = "⚠️待agent确认: 四问检验法+特许经营权判断"
217|
218|    # 1.2 护城河（简化判断）
219|    score_12 = 12  # 默认中等
220|    roe = metrics.get("roe")
221|    if roe and isinstance(roe, (int, float)):
222|        if roe > 20:
223|            score_12 = 20
224|        elif roe > 15:
225|            score_12 = 17
226|        elif roe > 10:
227|            score_12 = 14
228|    result["scores"]["1.2_护城河"] = score_12
229|    result["notes"]["1.2_护城河"] = "⚠️待agent确认: 护城河类型+宽度+趋势评估"
230|
231|    # 1.3 管理层（需 agent 深入分析）
232|    result["scores"]["1.3_管理层"] = 15
233|    result["notes"]["1.3_管理层"] = "⚠️待agent确认: 需web搜索管理层言论+荒岛两问+三重测试"
234|    result["data_gaps"].append("管理层数据需 web search 补充")
235|
236|    # 1.4 成长性
237|    score_14 = 12
238|    rev_growth = metrics.get("revenue_growth")
239|    if rev_growth and isinstance(rev_growth, (int, float)):
240|        if rev_growth > 20:
241|            score_14 = 20
242|        elif rev_growth > 10:
243|            score_14 = 16
244|        elif rev_growth > 0:
245|            score_14 = 13
246|        else:
247|            score_14 = 8
248|    result["scores"]["1.4_成长性"] = score_14
249|    result["notes"]["1.4_成长性"] = "⚠️待agent确认: PEG+增长质量+困境反转判断"
250|
251|    total = sum(result["scores"].values())
252|    result["total"] = total
253|    result["max"] = 100
254|
255|    print(f"  1.1 商业模式: {result['scores']['1.1_商业模式']}/25")
256|    print(f"  1.2 护城河:   {result['scores']['1.2_护城河']}/25")
257|    print(f"  1.3 管理层:   {result['scores']['1.3_管理层']}/25 (需深入分析)")
258|    print(f"  1.4 成长性:   {result['scores']['1.4_成长性']}/25")
259|    print(f"  合计: {total}/100")
260|    if result["data_gaps"]:
261|        print(f"  ⚠️ 数据缺口: {', '.join(result['data_gaps'])}")
262|
263|    return result
264|
265|
266|def step2_financial_basic(data: dict) -> dict:
267|    """Step 2: 财务健康度基础评分（简化版）"""
268|    print(f"\n{'='*60}")
269|    print("Step 2: 财务健康度基础评分（简化版）")
270|    print(f"{'='*60}")
271|
272|    result = {
273|        "step": 2,
274|        "note": "基础评分仅供参考，需 agent 进一步分析确认",
275|        "scores": {},
276|        "notes": {},
277|        "data_gaps": [],
278|        "key_metrics": {},
279|    }
280|
281|    # 提取财务数据
282|    financial = data.get("sources", {}).get("financial", {})
283|    stock_data = data.get("sources", {}).get("stock_data", {})
284|
285|    metrics = {}
286|    if financial:
287|        metrics.update(financial)
288|    if stock_data:
289|        metrics.update({
290|            "roe": stock_data.get("roe") or stock_data.get("returnOnEquity"),
291|            "pe_ttm": stock_data.get("pe_ttm") or stock_data.get("trailingPE"),
292|        })
293|
294|    # 2.1 盈利质量
295|    score_21 = 12
296|    roe = metrics.get("roe")
297|    if roe and isinstance(roe, (int, float)):
298|        if roe > 20:
299|            score_21 = 20
300|        elif roe > 15:
301|            score_21 = 17
302|        elif roe > 10:
303|            score_21 = 14
304|    result["scores"]["2.1_盈利质量"] = score_21
305|    result["data_gaps"].append("经营现金流/净利润、应收账款增速需财报数据")
306|
307|    # 2.2 资产负债表
308|    score_22 = 12
309|    debt_ratio = metrics.get("debt_ratio") or metrics.get("资产负债率")
310|    if debt_ratio and isinstance(debt_ratio, (int, float)):
311|        if debt_ratio < 30:
312|            score_22 = 20
313|        elif debt_ratio < 50:
314|            score_22 = 16
315|        elif debt_ratio < 70:
316|            score_22 = 12
317|        else:
318|            score_22 = 8
319|    result["scores"]["2.2_资产负债表"] = score_22
320|    result["key_metrics"]["资产负债率"] = debt_ratio
321|
322|    # 2.3 现金流
323|    score_23 = 10
324|    result["scores"]["2.3_现金流"] = score_23
325|    result["data_gaps"].append("经营现金流、FCF 需财报数据")
326|
327|    # 2.4 财务趋势
328|    score_24 = 10
329|    rev_growth = metrics.get("revenue_growth") or metrics.get("营收增速")
330|    if rev_growth and isinstance(rev_growth, (int, float)):
331|        if rev_growth > 15:
332|            score_24 = 18
333|        elif rev_growth > 5:
334|            score_24 = 14
335|        elif rev_growth > 0:
336|            score_24 = 11
337|    result["scores"]["2.4_财务趋势"] = score_24
338|
339|    total = sum(result["scores"].values())
340|    result["total"] = total
341|    result["max"] = 100
342|
343|    print(f"  2.1 盈利质量:   {result['scores']['2.1_盈利质量']}/25")
344|    print(f"  2.2 资产负债表: {result['scores']['2.2_资产负债表']}/25")
345|    print(f"  2.3 现金流:     {result['scores']['2.3_现金流']}/25")
346|    print(f"  2.4 财务趋势:   {result['scores']['2.4_财务趋势']}/25")
347|    print(f"  合计: {total}/100")
348|    if result["data_gaps"]:
349|        print(f"  ⚠️ 数据缺口: {', '.join(result['data_gaps'])}")
350|
351|    return result
352|
353|
354|def save_checkpoint(checkpoint_dir: Path, step: int, data: dict):
355|    """保存检查点"""
356|    filename = f"step{step}_{'data' if step == 0 else 'quality' if step == 1 else 'financial'}.json"
357|    filepath = checkpoint_dir / filename
358|    with open(filepath, "w", encoding="utf-8") as f:
359|        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
360|    print(f"  💾 检查点已保存: {filepath}")
361|
362|    # 更新 checkpoint.json
363|    checkpoint_meta = {
364|        "last_step": step,
365|        "timestamp": datetime.now().isoformat(),
366|        "files": [f.name for f in checkpoint_dir.glob("step*.json")],
367|    }
368|    meta_path = checkpoint_dir / "checkpoint.json"
369|    with open(meta_path, "w", encoding="utf-8") as f:
370|        json.dump(checkpoint_meta, f, ensure_ascii=False, indent=2)
371|
372|
373|def check_existing_checkpoint(checkpoint_dir: Path) -> int:
374|    """检查已有检查点，返回最后完成的步骤"""
375|    meta_path = checkpoint_dir / "checkpoint.json"
376|    if meta_path.exists():
377|        with open(meta_path, "r", encoding="utf-8") as f:
378|            meta = json.load(f)
379|        last_step = meta.get("last_step", -1)
380|        print(f"  📂 发现已有检查点，最后完成步骤: Step {last_step}")
381|        return last_step
382|    return -1
383|
384|
385|def main():
386|    parser = argparse.ArgumentParser(
387|        description="jw-company-analysis Step 0-2 预执行脚本",
388|        formatter_class=argparse.RawDescriptionHelpFormatter,
389|        epilog="""
390|示例:
391|  python pre_analysis.py --symbol 600519 --market A
392|  python pre_analysis.py --symbol 0700.HK --market HK
393|  python pre_analysis.py --symbol AAPL --market US
394|  python pre_analysis.py --symbol 600519 --market A --force  # 忽略已有检查点
395|        """,
396|    )
397|    parser.add_argument("--symbol", required=True, help="股票代码")
398|    parser.add_argument("--market", required=True, choices=["A", "HK", "US"], help="市场")
399|    parser.add_argument("--force", action="store_true", help="强制重新执行，忽略已有检查点")
400|    args = parser.parse_args()
401|
402|    print(f"\n{'#'*60}")
403|    print(f"# jw-company-analysis 预执行 v3.29.0")
404|    print(f"# 股票: {args.symbol} | 市场: {args.market}")
405|    print(f"{'#'*60}")
406|
407|    checkpoint_dir = get_checkpoint_dir(args.symbol)
408|
409|    # 检查已有检查点
410|    if not args.force:
411|        last_step = check_existing_checkpoint(checkpoint_dir)
412|        if last_step >= 2:
413|            print("  ✅ Step 0-2 已完成，使用 --force 强制重新执行")
414|            # 读取并输出已有结果
415|            for step in range(3):
416|                filename = f"step{step}_{'data' if step == 0 else 'quality' if step == 1 else 'financial'}.json"
417|                filepath = checkpoint_dir / filename
418|                if filepath.exists():
419|                    with open(filepath, "r", encoding="utf-8") as f:
420|                        result = json.load(f)
421|                    print(f"\n  Step {step} 结果已加载: {filepath}")
422|            return
423|
424|    # Step 0: 数据获取
425|    start_step = max(0, check_existing_checkpoint(checkpoint_dir) + 1) if not args.force else 0
426|
427|    if start_step <= 0:
428|        data = step0_fetch_data(args.symbol, args.market)
429|        save_checkpoint(checkpoint_dir, 0, data)
430|    else:
431|        # 加载已有数据
432|        data_path = checkpoint_dir / "step0_data.json"
433|        with open(data_path, "r", encoding="utf-8") as f:
434|            data = json.load(f)
435|
436|    # Step 1: 企业质量基础评分
437|    if start_step <= 1:
438|        quality = step1_quality_basic(data)
439|        save_checkpoint(checkpoint_dir, 1, quality)
440|    else:
441|        print("  ⏭️ Step 1 已完成，跳过")
442|
443|    # Step 2: 财务健康度基础评分
444|    if start_step <= 2:
445|        financial = step2_financial_basic(data)
446|        save_checkpoint(checkpoint_dir, 2, financial)
447|
448|    print(f"\n{'='*60}")
449|    print("✅ 预执行完成！")
450|    print(f"检查点目录: {checkpoint_dir}")
451|    print(f"{'='*60}")
452|    print("\n下一步：agent 可从 Step 3 继续执行，或基于检查点数据深化 Step 0-2 分析。")
453|
454|
455|if __name__ == "__main__":
456|    main()
457|