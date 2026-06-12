# Step 1 JSON Schema

## 结构化分析输出格式

Step 1 输出必须是有效 JSON，包含以下字段：

```json
{
  "source_summary": "一句话概括",
  "entities": [
    {
      "name": "xxx",
      "type": "concept",
      "relevance": "high",
      "confidence": "EXTRACTED",
      "evidence": "原文摘录或推理依据"
    }
  ],
  "topics": [
    {
      "name": "xxx",
      "importance": "high"
    }
  ],
  "connections": [
    {
      "from": "A",
      "to": "B",
      "type": "因果",
      "confidence": "INFERRED",
      "evidence": "推理依据"
    }
  ],
  "contradictions": [
    {
      "claim_a": "...",
      "claim_b": "...",
      "context": "..."
    }
  ],
  "new_vs_existing": {
    "new_entities": [],
    "updates": []
  }
}
```

## 置信度赋值规则

- **EXTRACTED**：信息直接出现在原文里，字面可以找到。**必须在 `evidence` 字段提供原文摘录**（建议 ≤50 字）
- **INFERRED**：信息是从多处原文推断出来的，原文没有直接说。**必须在 `evidence` 字段说明推理依据**
- **AMBIGUOUS**：原文说法不清楚，或者有歧义。`evidence` 可选
- **UNVERIFIED**：信息来自模型的背景知识，原文没有证据。`evidence` 可选

## 验证步骤

Step 1 完成后，必须执行验证：

```bash
# 1. 创建临时目录
mkdir -p {wiki_root}/.wiki-tmp

# 2. 写入 JSON
echo '<JSON内容>' > {wiki_root}/.wiki-tmp/step1-latest.json

# 3. 验证
bash ${SKILL_DIR}/scripts/validate-step1.sh {wiki_root}/.wiki-tmp/step1-latest.json

# 4. 清理
rm {wiki_root}/.wiki-tmp/step1-latest.json
```

如果脚本返回非 0，自动回退到单步 ingest（不进行 Step 2）。