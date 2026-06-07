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
- **pdf 提取 fallback**：当 jw-investment-data 脚本不可用时，可用 `pdftotext` 从本地研报/年报 PDF 提取结构化数据作为主数据源（非 web search），信源等级 🟢🟢（券商研报）或 🟢🟢🟢（年报）。
- **baostock 不支持 ma/kdj 指标**：`jw-data indicators` 使用 baostock 后端，ma 和 kdj 会报 `未知指标` 错误。解决：用 baostock 手动计算 MA5/10/20/60 和 KDJ（K/D/J）。代码模式：`df['MA5'] = df['close'].rolling(5).mean()`，KDJ 用 RSV→EMA 计算。详见 `references/technical-analysis-guide.md`。
- **fetch_all_data.py 超时**：统一数据获取入口脚本默认超时60秒，comprehensive 财务数据需要120秒。解决：直接使用各脚本分别获取（jw-data quote + fetch_market_data.py --category comprehensive + 7track_boll.py），或修改 fetch_all_data.py 超时常量。
- **akshare 网络连接失败**：akshare 库在某些网络环境下会 RemoteDisconnected。解决：优先使用 baostock + jw-data 组合，akshare 作为最后 fallback。
- **模板多次插入后结构混乱**：反复向 SKILL.md 和模板插入内容后，`head/tail` 拼接可能导致重复章节或错位。解决：每次大改后用 `grep -n "^##\|^###" file` 检查章节结构，确认无重复。
- **SKILL.md 多行插入**：向 SKILL.md 插入多行内容（含引号/特殊字符）时，`sed -i` 经常因引号不匹配而失败。安全模式：①`head -n $LINE file > /tmp/part1.md` ②`cat content.md >> /tmp/part1.md` ③`tail -n +$((LINE+1)) file >> /tmp/part1.md` ④`cp /tmp/part1.md file`。用 `patch` 工具做精确替换也可以。

