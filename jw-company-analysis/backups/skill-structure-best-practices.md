# Skill 结构最佳实践

> **来源**：skill-review 审查 jw-company-analysis 后总结的经验教训。

## 结构合规性

### 目录标准布局
```
skill-name/
├── SKILL.md           # 主文件，≤500行
├── references/        # 按需加载的详细文档
├── scripts/           # 可执行脚本
├── templates/         # 模板文件
├── tests/             # 测试文件
└── backups/           # 历史版本（可选）
```

### 清理规则
- **不要**保留 `.bak` 文件 — 用 `backups/` 目录代替
- **不要**保留 `__pycache__/` — 加入 `.gitignore`
- **不要**保留未引用的 references — 移到 `backups/references-archive/`
- **不要**保留 `README.md`（除非 skill 本身就是关于 README）

## Token 效率

### SKILL.md 精简原则
- **≤500行硬限制**，接近400行时预警
- **只放 Claude 不知道的东西** — 不解释 markdown 语法、JSON 格式等
- **执行细节提取到 references** — 脚本命令、超时常量、Pitfall 列表
- **用 imperative form** — "执行 X" 而不是 "You should execute X"
- **Progressive loading** — 按需加载 references，不要一次性全部加载

### 提取到 references 的内容
- 脚本调用速查表 → `references/script-commands.md`
- 超时常量配置 → `references/timeout-config.md`
- Pitfall 列表 → `references/pitfalls.md`
- 字段名参考 → `references/baostock-fields.md`

## 工作流设计

### Checklist 格式
```markdown
## 执行清单 ⚠️ REQUIRED

- [ ] Step 0: 数据准备 ⚠️ REQUIRED
- [ ] Step 1: 分析
- [ ] Step 2: 输出 ⚠️ REQUIRED
```

### 关键标记
- ⚠️ REQUIRED — 不能跳过的步骤
- ⛔ BLOCKING — 前置条件，未满足则阻断

## 描述质量

### 触发关键词
- 至少 5 个触发短语
- 覆盖自然语言查询（问句形式）
- 包含中英文变体

### 示例
```
触发：'分析XX公司'、'深度分析XX'、'这家公司值不值得持有'、
'XX股票分析'、'XX股票怎么样'、'这家公司值得买吗'、
'价值投资分析'、'帮我看看XX'、'长期持有分析'。
```

## 审查评分标准

| 维度 | 权重 | 满分 |
|------|------|------|
| 结构合规性 | 20% | 10 |
| 描述质量 | 20% | 10 |
| 工作流设计 | 20% | 10 |
| Token效率 | 20% | 10 |
| 反模式检测 | 20% | 10 |

**目标**：总体评分 ≥ 8.0/10
