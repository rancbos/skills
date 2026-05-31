---
name: holographic-memory-embedding
description: "Add semantic embedding support (local sentence-transformers OR API-based via SiliconFlow) to Hermes holographic memory plugin. Dual mode: local BGE models or OpenAI-compatible embeddings API."
---

# Holographic Memory + Embedding Models

The `holographic` memory plugin supports optional **semantic embeddings** for Chinese/multilingual semantic search, in TWO modes:

1. **API mode** (recommended): Uses an OpenAI-compatible embeddings API (e.g. SiliconFlow). No local model download. Fast setup.
2. **Local mode**: Uses `sentence-transformers` with a local model (e.g. `BAAI/bge-large-zh-v1.5`). Works offline but needs ~1.3 GB download.

When `embedding_api_url` is set in config, API mode is used. Otherwise local mode is used.

## When to Use

- User needs Chinese-language memory search (HRR tokenizes by whitespace, which is poor for CJK text)
- User wants to configure a specific embedding model like `BAAI/bge-large-zh-v1.5`
- User's existing facts should get automatic embedding backfill on next session start
- pip install is slow / network-constrained → use API mode instead

## What Gets Modified

All files are under `plugins/memory/holographic/` in the Hermes source tree:

| File | Change |
|------|--------|
| `holographic.py` | Add `Embedder` class (local) + `ApiEmbedder` class (API) with thread-safe singleton, encode/batch-encode, cosine similarity, serialization |
| `store.py` | Add `embedding_vector BLOB` column to `facts` table, pass embedder to `MemoryStore`, add `compute_all_embeddings()` and `get_all_embedding_vectors()` |
| `retrieval.py` | Add `embedding_weight` to `FactRetriever.__init__`, mix embedding cosine sim into hybrid score |
| `__init__.py` | Add `embedding_model`, `embedding_weight`, `embedding_api_url` config keys; create `ApiEmbedder` or `Embedder` in `initialize()`; auto-backfill existing facts |
| `~/.hermes/config.yaml` | Set `plugins.hermes-memory-store.embedding_model`, `embedding_weight`, optionally `embedding_api_url` |

## Config Keys

Under `plugins.hermes-memory-store` in `~/.hermes/config.yaml`:

```yaml
plugins:
  hermes-memory-store:
    embedding_model: BAAI/bge-large-zh-v1.5   # or any HF sentence-transformers model
    embedding_weight: '0.5'                    # weight in hybrid search (auto-normalized)
    embedding_api_url: https://api.siliconflow.cn/v1/embeddings  # omit for local mode
```

Set via CLI:

**API mode** (requires `SILICONFLOW_API_KEY` in `.env`):
```bash
hermes config set plugins.hermes-memory-store.embedding_model "BAAI/bge-large-zh-v1.5"
hermes config set plugins.hermes-memory-store.embedding_weight "0.5"
hermes config set plugins.hermes-memory-store.embedding_api_url "https://api.siliconflow.cn/v1/embeddings"
```

**Local mode** (requires `pip install sentence-transformers`):
```bash
hermes config set plugins.hermes-memory-store.embedding_model "BAAI/bge-large-zh-v1.5"
hermes config set plugins.hermes-memory-store.embedding_weight "0.5"
# DON'T set embedding_api_url — leave it empty
```

## Installation (API Mode — Preferred)

No model download needed. Just ensure `numpy` is available in the Hermes venv.

```bash
# Activate Hermes venv
source ~/.hermes/hermes-agent/venv/bin/activate

# Numpy is required for vector operations
pip install numpy
```

If pip is slow (network issues), use system numpy instead:
```bash
apt install -y python3-numpy
SITE_PKG=$(python -c "import site; print(site.getsitepackages()[0])")
echo "/usr/lib/python3/dist-packages" > "$SITE_PKG/system-packages.pth"
```
Then set `embedding_api_url` and add `SILICONFLOW_API_KEY` to `~/.hermes/.env`.

## Installation (Local Mode)

```bash
# Activate Hermes venv
source ~/.hermes/hermes-agent/venv/bin/activate

# Install sentence-transformers (this also pulls torch — can be slow)
pip install sentence-transformers --find-links https://download.pytorch.org/whl/cpu
```

Use the cpu-only PyTorch index to avoid downloading gigabytes of CUDA toolkit packages.

## Architecture

### Embedder class (`holographic.py`)

- Thread-safe singleton: caches one `SentenceTransformer` model per model name
- `encode(text)` → normalized float32 numpy array
- `encode_batch(texts)` → list of arrays
- `cosine_similarity(a, b)` → float [0, 1]
- Falls back gracefully if sentence-transformers is not installed or model fails
- `vector_to_bytes(vec)` / `bytes_to_vector(data)` — serialization helpers

### ApiEmbedder class (`holographic.py`)

- Calls OpenAI-compatible embeddings API (SiliconFlow, OpenAI, etc.)
- `encode(text)` → float32 numpy array via HTTP POST
- `encode_batch(texts)` → batch-calls API (more efficient than multiple single calls)
- `cosine_similarity(a, b)` → float [0, 1] (dot product on normalized vectors)
- Same serialization interface as `Embedder` (`vector_to_bytes`, `bytes_to_vector`)
- Reads API key from config `embedding_api_key` or `.env` variable `SILICONFLOW_API_KEY`
- Lazy import of numpy (only inside methods) — module can load without numpy installed
- `from __future__ import annotations` used so type hints don't fail on missing numpy

### Initialization Logic (`__init__.py`)

```
if embedding_model is set:
  if embedding_api_url is set:
    try to read API key from config/.env
    if key found → create ApiEmbedder
    else → log warning, fall back to HRR-only (embedding_weight=0)
  else:
    try to create local Embedder (sentence-transformers)
    if fails → log warning, fall back to HRR-only
```

### Storage (`store.py`)

- New column `embedding_vector BLOB` stores the float32 numpy array as bytes
- When embedder is available, new facts get embedding computed on insert/update
- `compute_all_embeddings()` — called on `initialize()` to backfill facts that lack embeddings
- `get_all_embedding_vectors(category, min_trust)` — bulk-loads vectors for batch scoring
- `get_embedding_vector(fact_id)` — single fact embedding retrieval

### Retrieval (`retrieval.py`)

The hybrid search formula becomes:

```
score = FTS5_weight · fts_rank
      + Jaccard_weight · token_overlap
      + HRR_weight · phase_similarity
      + Embedding_weight · cosine_similarity(query_emb, fact_emb)

final = score · trust_score · temporal_decay
```

Weights are auto-normalized to sum to 1.0.

## Testing

### API Mode (recommended)

```python
source ~/.hermes/hermes-agent/venv/bin/activate
python -c "
from plugins.memory.holographic.holographic import ApiEmbedder
ae = ApiEmbedder(
    model_name='BAAI/bge-large-zh-v1.5',
    api_url='https://api.siliconflow.cn/v1/embeddings',
    api_key='YOUR_KEY'
)
print('available:', ae.available, 'dim:', ae.dim)
vec = ae.encode('测试中文语义向量')
print('encode OK, shape:', vec.shape, 'first 5:', vec[:5])

# Batch test
vecs = ae.encode_batch(['今天天气', '明天天气'])
print('batch encode OK:', len(vecs), 'vectors')

# Serialization roundtrip
data = ApiEmbedder.vector_to_bytes(vec)
restored = ApiEmbedder.bytes_to_vector(data)
import numpy as np
print('roundtrip OK:', np.allclose(vec, restored), f'({len(data)} bytes)')
"
```

### Local Mode

```python
source ~/.hermes/hermes-agent/venv/bin/activate
python -c "
from plugins.memory.holographic.holographic import Embedder, _HAS_ST
print('ST available:', _HAS_ST)
e = Embedder('BAAI/bge-large-zh-v1.5')
print('Model loaded:', e.available, 'dim:', e.dim)
vec = e.encode('你好世界')
print('Encode OK, shape:', vec.shape)
"
```

## Pitfalls

- **Git update risk**: If Hermes Agent is updated via `git pull`, the plugin code changes to `holographic.py` and `__init__.py` may be overwritten. A backup patch is saved at `~/.hermes/hermes-changes.patch`.
  
  **To restore after update:**
  ```bash
  cd ~/.hermes/hermes-agent
  git apply ~/.hermes/hermes-changes.patch
  ```
  
  **自动恢复（推荐）**：已安装 git post-merge 和 post-rewrite hook，以后 `git pull` 或 `git pull --rebase` 后会自动恢复补丁，无需手动操作。
  
  If the patch conflicts (upstream code changed), regenerate it:
  ```bash
  cd ~/.hermes/hermes-agent
  # Re-apply the changes manually, then:
  git diff plugins/memory/holographic/ > ~/.hermes/hermes-changes.patch
  ```

### API Mode
- **API key required**: Must set `SILICONFLOW_API_KEY` in `.env` or `embedding_api_key` in config. No key = fallback to HRR-only.
- **Network dependency**: Each encode() call hits the API. Slow network affects memory write/update latency.
- **Rate limits**: SiliconFlow may have rate limits. Batch encoding helps reduce calls.
- **Token costs**: Very cheap for typical usage, but not free.
- **Restart required**: Plugin config is read at session start. Run `/reset` or start a new `hermes` session after changing config.

### Local Mode
- **Slow install**: sentence-transformers pulls torch (and on Linux, the CUDA toolkit). Use `--find-links https://download.pytorch.org/whl/cpu` to get CPU-only torch. Network speed may make the install take 10-30 minutes.
- **Memory**: BGE-large is ~1.3 GB VRAM/RAM for inference. On low-memory machines, use `BAAI/bge-small-zh-v1.5` instead.
- **First load slow**: The model is downloaded from HuggingFace Hub on first use (~1.3 GB for BGE-large).
- **Restart required**: Same as API mode.

### Both Modes
- **Existing facts**: Are auto-backfilled with embeddings on first `initialize()` after config change. Can be slow for large stores.
- **numpy required**: All vector operations (including API mode) depend on numpy. If pip is slow, install via `apt install python3-numpy` + `.pth` pointer.

## References

| File | What It Covers |
|------|---------------|
| `references/siliconflow-api.md` | SiliconFlow API endpoint, request/response format, supported models, pricing |
