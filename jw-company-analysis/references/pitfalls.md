# Pitfall 列表

> **用途**：SKILL.md 中引用的 Pitfall 速查表，按需加载。

## 脚本执行 Pitfall

- **并行取数模式**：用 `delegate_task` 并行执行研报提取 + web search，可节省 50-70% 取数时间。示例：`delegate_task(tasks=[{goal: "从本地研报PDF提取关键数据", toolsets: ["terminal", "file"]}, {goal: "web search 最新经营数据", toolsets: ["search", "web"]}])`
- **报告输出路径 fallback**：`/root/data/` 权限不足时（Permission denied），fallback 到 `~/data/`。检查点目录同理。
- **行号前缀污染**：read_file 输出带行号前缀（`N|content`），如果在 execute_code 中处理后 write_file 会嵌入行号。用 terminal cat 读取或 patch 做精确替换。
- 用 `--category quote --symbol 600519 --market A --format json`，不用旧格式 `--code`
- comprehensive 失败时 fallback 到 `financial` + web search（Pitfall 7）
- 管道模式必须 `2>/dev/null`（py_mini_racer DeprecationWarning 破坏 JSON）
- 预执行脚本：`python ~/.hermes/skills/rancbos-skills/jw-company-analysis/scripts/pre_analysis.py --symbol {代码} --market A`
- **脚本路径**：所有 rancbos-skills 下的脚本在 `~/.hermes/skills/rancbos-skills/` 下（不是 `~/.hermes/skills/`）。首次执行前验证：`python3 <script> --help`，报错说明路径或依赖问题。
- **依赖安装**：首次执行需确认以下包已安装：`pip install akshare adata baostock efinance yfinance pandas matplotlib --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple`。七轨布林额外需要 numpy/matplotlib/pandas。缺少包会报 `No module named 'X'`。
- **CHECKPOINT_DIR 权限**：默认 `/root/data/` 可能不可写（Permission denied）。如 `mkdir -p` 失败，fallback 到 `~/data/.checkpoints/`。报告输出同理 fallback 到 `~/data/`。
- **⚠️ pre_analysis.py 权限修复（v3.63.4 已修补）**：`get_checkpoint_dir` 函数原来硬编码 `/root/data/.checkpoints/` 且无 fallback，会导致 PermissionError 崩溃。v3.63.4 已修补为优先尝试 `/root/data/`，失败则 fallback 到 `~/data/`。如果使用旧版本脚本，需手动 patch `get_checkpoint_dir` 函数添加 fallback 逻辑。
- **pdf 提取 fallback**：当 jw-investment-data 脚本不可用时，可用 `pdftotext` 从本地研报/年报 PDF 提取结构化数据作为主数据源（非 web search），信源等级 🟢🟢（券商研报）或 🟢🟢🟢（年报）。高效 grep 模式：①管理层信息 `grep -E "董事长|总经理|总裁|实际控制人|控股股东"` ②财务数据 `grep -A 3 -E "营业收入|净利润|总资产|净资产|现金流"` ③分红信息 `grep -E "分红|股息|利润分配"` ④股东结构 `grep -A 2 -E "前十大股东|持股比例|股东性质"` ⑤具体人物 `grep -B 10 "2025年.*至今.*董事长"` 定位当前管理层。
- **⚠️ pre_analysis.py 内部调用 `python` 而非 `python3`**：脚本内部的 subprocess 调用使用 `python`（不是 `python3`），在某些系统上会报 "脚本不存在: python"。脚本仍能部分执行（生成基本评分），但数据获取步骤会全部失败。**症状**：输出中出现多行 `❌ 脚本不存在: python`，step0_data.json 的 `sources` 为空 `{}`。**解决**：①忽略 pre_analysis.py 的数据获取结果 ②手动用 `fetch_market_data.py --category quote` + `--category comprehensive` 分别获取数据 ③或修复 pre_analysis.py 内部的 subprocess 调用为 `python3`。
- **⚠️ pre_analysis.py `validate_checkpoint` NameError**：脚本在 `main()` 末尾调用 `validate_checkpoint(checkpoint_dir)` 但该函数未定义。**症状**：输出 `NameError: name 'validate_checkpoint' is not defined. Did you mean: 'save_checkpoint'?`，pre_analysis.py 崩溃无 JSON 输出。**解决**：①忽略 pre_analysis.py ②直接用 `fetch_market_data.py --category quote/comprehensive/financial` 分别获取数据 ③手动组装 step0_data.json ④或修复 pre_analysis.py 将 `validate_checkpoint` 改为实际存在的函数名。此 bug 在 v3.29.0 存在。
- **⚠️ 子agent报告写作引入行号前缀**：用 `delegate_task` 委托子agent撰写分析报告时，子agent内部调用 `read_file` 会获取带行号前缀的输出（`N|content`），如果子agent随后用 `write_file` 写入时未清理，行号前缀会嵌入最终报告。**症状**：报告中出现 `1|1|1|## 标题` 等污染行。**解决**：①报告生成后立即运行 `grep -c "^[0-9]*|" file` 检查污染行数 ②如有污染，用 `sed -i 's/^[0-9]*|//' file` 批量清理 ③在委托任务的 context 中明确告知子agent "用 terminal cat 读取文件，不要用 read_file" 以预防此问题。
- **⚠️ 子agent报告评分格式错误**：子agent撰写报告时，Step 5 逆向检查可能使用 0-100 评分而非 skill 规定的 -50~+20 范围。**症状**：Step 5 显示 "70/100" 而非正确的 "-10/20"，导致逆向调整分计算错误。**解决**：报告生成后验证 Step 5 评分是否在 -50~+20 范围内，以及综合得分公式是否正确：`基础得分 = Step1×35% + Step2×20% + Step3×10% + Step4×25%`，`综合得分 = 基础得分 + Step5得分×10%`。
- **⚠️ comprehensive `ok: false` 不代表零数据**：当 `fetch_market_data.py --category comprehensive` 返回 `ok: false` 时，`data.results` 中可能仍有 `adata_finance` 等有效数据。`ok` 字段反映的是**所有数据源都成功**，而非"没有任何数据"。**解决**：①即使 `ok: false`，也要检查 `data.results` 中是否有目标数据 ②解析 JSON 后提取 `adata_finance`（核心财务）、`express`（业绩快报）、`operation`（营运指标）③忽略 `errors` 字段中的非关键源（tushare/xueqiu/yfinance 经常超时）。
- **⚠️ `web_search` 工具不存在**：SKILL.md 中多处引用 "web search" 作为数据源，但实际环境中 `web_search` 工具不可用。**替代方案**：①中文财经快讯用 `mcp_jin10_search_flash(keyword)` ②英文/通用搜索用 `browser_navigate` 访问搜索引擎 ③研报/公告数据用 `pdftotext` 从本地 PDF 提取。搜索流程应写成：`jin10快讯 → 本地PDF → 浏览器搜索` 的优先级链。
- **baostock 不支持 ma/kdj 指标**：`jw-data indicators` 使用 baostock 后端，ma 和 kdj 会报 `未知指标` 错误。解决：用 baostock 手动计算 MA5/10/20/60 和 KDJ（K/D/J）。代码模式：`df['MA5'] = df['close'].rolling(5).mean()`，KDJ 用 RSV→EMA 计算。详见 `references/technical-analysis-guide.md`。
- **fetch_all_data.py 超时**：统一数据获取入口脚本默认超时60秒，comprehensive 财务数据需要120秒。解决：直接使用各脚本分别获取（jw-data quote + fetch_market_data.py --category comprehensive + 7track_boll.py），或修改 fetch_all_data.py 超时常量。
- **⚠️ comprehensive 输出过大（200K+字符）**：`fetch_market_data.py --category comprehensive` 返回的 JSON 包含市场-wide 数据（龙虎榜全部股票、龙虎榜原因、龙虎榜金额等），单次输出可达 200K+ 字符，严重浪费 context 窗口。**解决**：①在 `execute_code` 中用 `json.loads` 解析后只提取目标股票相关字段：`adata_finance`（核心财务）、`express`（业绩快报）、`operation`（营运指标）、`shares`（股本变动）、`concept`（概念板块）②用管道过滤：`... 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); r=d['data']['results']; print(json.dumps({k:r[k] for k in ['adata_finance','express','operation'] if k in r},indent=2,ensure_ascii=False))"` ③`daily_movers`（龙虎榜）、`market_five`（五档行情）、`north_flow`（北向资金）数据量巨大且通常对个股分析无用，解析后直接丢弃 ④推荐在 `delegate_task` 中执行 comprehensive，让子 agent 过滤后只返回结构化摘要，避免污染父 agent 的 context 窗口。
- **并行取数最佳实践**：用 `delegate_task(tasks=[...])` 并行执行三个子任务效率最高：①研报PDF提取（terminal+file）②技术指标+布林线（terminal）③新闻搜索（search+web）。实测可在 ~60秒内完成全部取数（vs 串行 ~300秒）。子 agent 返回摘要而非原始数据，父 agent context 消耗可控。
- **akshare 网络连接失败**：akshare 库在某些网络环境下会 RemoteDisconnected。解决：优先使用 baostock + jw-data 组合，akshare 作为最后 fallback。
- **模板多次插入后结构混乱**：反复向 SKILL.md 和模板插入内容后，`head/tail` 拼接可能导致重复章节或错位。解决：每次大改后用 `grep -n "^##\|^###" file` 检查章节结构，确认无重复。
- **SKILL.md 多行插入**：向 SKILL.md 插入多行内容（含引号/特殊字符）时，`sed -i` 经常因引号不匹配而失败。安全模式：①`head -n $LINE file > /tmp/part1.md` ②`cat content.md >> /tmp/part1.md` ③`tail -n +$((LINE+1)) file >> /tmp/part1.md` ④`cp /tmp/part1.md file`。用 `patch` 工具做精确替换也可以。

