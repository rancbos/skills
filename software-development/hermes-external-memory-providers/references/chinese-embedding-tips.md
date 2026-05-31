# Chinese Search Quality with agentmemory

Evaluation conducted on agentmemory v0.9.21 with `BAAI/bge-large-zh-v1.5` via SiliconFlow API. Tests compare BM25-only mode vs. hybrid BM25+vector mode.

## Test Setup

5 Chinese memories saved before embedding was active (BM25-only), 3 saved after embedding was active (with vectors):

| Memory Content | Type | Has Vector? |
|---------------|------|:-----------:|
| 用户住在临沂市河东区，山东省 | user_pref | ✗ |
| 用户喜欢使用微信和飞书进行通信 | preference | ✗ |
| 项目使用Python Flask框架开发后端API | architecture | ✗ |
| 深度学习模型训练使用PyTorch框架，数据集存储在NAS上 | architecture | ✗ |
| 用户常用的编程语言是Python和TypeScript | fact | ✗ |
| 用户居住在山东省临沂市河东区 (new) | fact | ✓ |
| 用户通过微信和飞书与人沟通交流 (new) | fact | ✓ |
| 项目后端使用Python Flask框架开发Web API接口 (new) | architecture | ✓ |

## Search Results Matrix

### BM25-Only Mode

| Query | Result | Score | Correct? |
|-------|--------|:-----:|:--------:|
| `临沂` | 临沂地址 | 1.29 | ✅ |
| `PyTorch 训练` | PyTorch 条目 | 4.36 | ✅ |
| `Flask` | Flask 条目 | 0.02 | ✅ |
| `微信飞书` | 微信飞书 | 0.02 | ✅ |
| `住在哪里` | 临沂地址 (+ 误匹配 PyTorch) | 0.02 | ⚠️ noisy |
| `地址` | empty | 0 | ❌ |
| `消息聊天` | empty | 0 | ❌ |
| `where does user live` | empty | 0 | ❌ |
| `programming language` | empty | 0 | ❌ |

### Hybrid Mode (BM25 + bge-large-zh-v1.5 vectors)

| Query | Result | Correct? | Notes |
|-------|--------|:--------:|-------|
| `住哪里` | 临沂地址 | ✅ | Semantic match |
| `家在山东` | 临沂地址 (new+old) | ✅ | Semantic + keyword |
| `沟通工具` | 微信飞书 (new) | ✅ | Synonym match |
| `通信方式` | 微信飞书 (old, keyword-matched) | ✅ | Partial semantic |
| `地址` | empty | ❌ | Too abstract |
| `位置信息` | empty | ❌ | Too abstract |
| `where do you live` | empty | ❌ | Cross-language not supported |
| `machine learning` | empty | ❌ | Cross-language not supported |
| `backend framework` | empty | ❌ | Cross-language not supported |
| `Web框架` | Flask entries | ✅ | Keyword + partial semantic |

## Key Findings

### 1. Old (pre-embedding) memories lack vectors

Memories saved before embedding configuration are searchable only via BM25 keyword match. They **do not appear** in vector-based semantic results. The smart-search hybrid scoring shows `bm25Score=0.0` and `vectorScore=0.0` for these entries even when they're returned.

**Fix**: Re-save important memories after enabling the embedding provider, or use the provider's backfill mechanism if available.

### 2. bge-large-zh-v1.5 is Chinese-only

This model creates a **Chinese-centric** vector space. English queries (even semantically related ones) consistently return empty results because the embedding doesn't map English tokens into the Chinese embedding space. This is inherent to the model, not a configuration issue.

**For cross-language search**: Use `BAAI/bge-m3` (multilingual, supports 100+ languages) or `intfloat/multilingual-e5-large-instruct`.

### 3. Smart-search scores are opaque

In our tests, `combinedScore`, `bm25Score`, and `vectorScore` were all `0.000` for hybrid results. This appears to be a rendering/display issue in the response rather than actual zero scores — the retrieval order was correct even when scores were zero.

### 4. Abstract queries fail

Queries like `地址` (address) or `位置信息` (location info) did not match the address memory `临沂市河东区，山东省`. The embedding model requires reasonably specific semantic overlap. Expect failure for:
- Very short abstract queries (1-2 characters with broad meaning)
- Highly conceptual queries with no concrete terms in the target memory

### 5. No Chinese word segmentation visible

BM25 operates at the character level for Chinese text — `住在哪里` matches by individual characters `住`, `在`, `哪`, `里` rather than word-level tokens. This causes false positives (e.g., `用户家住在哪里在哪个省` matching the PyTorch entry due to overlapping characters).

## Recommended Embedding Providers

| Provider | URL | Recommended Model | Language |
|----------|-----|-------------------|----------|
| SiliconFlow | `https://api.siliconflow.cn/v1` | `BAAI/bge-large-zh-v1.5` | Chinese only |
| SiliconFlow | `https://api.siliconflow.cn/v1` | `BAAI/bge-m3` | Multilingual (100+ langs) |
| OpenAI | `https://api.openai.com/v1` | `text-embedding-3-small` | Multilingual |
| Voyage AI | `https://api.voyageai.com/v1` | `voyage-3-lite` | Multilingual |

## Testing Commands

```bash
# Quick functional test
curl -s -X POST http://localhost:3111/agentmemory/remember \
  -H 'Content-Type: application/json' \
  -d '{"content":"测试记忆条目","type":"fact"}'

# Semantic search
curl -s -X POST http://localhost:3111/agentmemory/smart-search \
  -H 'Content-Type: application/json' \
  -d '{"query":"住哪里","limit":5}'

# Check status (look for Embeddings field)
/root/.hermes/node/bin/agentmemory status
```
