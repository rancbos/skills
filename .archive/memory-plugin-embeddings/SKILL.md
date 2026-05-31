---
name: memory-plugin-embeddings
description: "Add sentence-transformers / local embedding model support to Hermes memory provider plugins. Covers the Embedder class pattern, SQLite schema extension, hybrid retrieval integration, config wiring, and backfill logic."
version: 1.0.0
author: Hermes Agent
tags:
  - hermes
  - memory
  - embeddings
  - sentence-transformers
  - plugin-development
trigger: user asks to change/configure/add an embedding model for Hermes memory
platforms: [linux, macos]
---

# Memory Plugin Embedding Integration

When a user requests a specific embedding model (e.g. `BAAI/bge-large-zh-v1.5`)
for Hermes memory, you need to modify the memory provider plugin to support
sentence-transformers. This skill documents the general pattern, using the
holographic plugin as a concrete example.

## Architecture Overview

```
Embedder (sentence-transformers wrapper)
   ┃ encode(text) → float32 vector
   ┃
   ▼
MemoryStore (SQLite)           FactRetriever (search pipeline)
   ┣ embedding_vector BLOB       ┣ FTS5 keyword
   ┣ compute_all_embeddings()    ┣ Jaccard token overlap
   ┣ get_all_embedding_vectors() ┣ HRR phase similarity
   ┗ get_embedding_vector()      ┗ Embedding cosine similarity
```

## Step-by-Step Implementation

### 1. Add Embedder class to the core module

In the plugin's main logic file (e.g. `holographic.py`), add an `Embedder` class
that wraps sentence-transformers:

```python
_HAS_ST = False
try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except ImportError:
    SentenceTransformer = None

_EMBEDDER_LOCK = threading.Lock()
_EMBEDDER_CACHE: dict[str, SentenceTransformer | None] = {}

class Embedder:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name
        self._model = None
        self._dim = 0
        if model_name:
            self._load_model()

    def _load_model(self) -> None:
        """Lazy-load with thread-safe singleton caching."""
        if not _HAS_ST: return
        with _EMBEDDER_LOCK:
            if name in _EMBEDDER_CACHE:
                self._model = _EMBEDDER_CACHE[name]
                ...
```

**Key design rules:**
- Thread-safe singleton via `_EMBEDDER_CACHE` — loads model once per name
- `normalize_embeddings=True` on encode() so cosine sim = dot product
- Returns `np.float32` arrays
- Never raise — log warnings and return `None` on failure

### 2. Extend the SQLite schema

Add `embedding_vector BLOB` column to the facts table:

```sql
CREATE TABLE IF NOT EXISTS facts (
    ...
    hrr_vector      BLOB,
    embedding_vector BLOB
);
```

Add a migration in the `_init_db()` method:

```python
columns = {row[1] for row in conn.execute("PRAGMA table_info(facts)")}
if "embedding_vector" not in columns:
    conn.execute("ALTER TABLE facts ADD COLUMN embedding_vector BLOB")
```

### 3. Store embeddings on write

In the store's `__init__`, accept an `embedder` parameter. Modify the
vector-computation method to also store the embedding:

```python
def _compute_hrr_vector(self, fact_id, content):
    # ... existing HRR logic ...
    if self._embedder and self._embedder.available:
        emb = self._embedder.encode(content)
        if emb is not None:
            self._conn.execute(
                "UPDATE facts SET embedding_vector = ? WHERE fact_id = ?",
                (Embedder.vector_to_bytes(emb), fact_id),
            )
```

### 4. Add retrieval helpers

```python
def get_all_embedding_vectors(self, category=None, min_trust=0.0):
    """Load (fact_id, vector, trust_score) tuples for batch scoring."""

def get_embedding_vector(self, fact_id):
    """Single fact's embedding vector."""

def compute_all_embeddings(self) -> int:
    """Backfill all facts that lack an embedding vector."""
```

### 5. Integrate into search pipeline

In the retriever's `search()` method, add embedding similarity alongside
existing signals:

```python
emb_sim = 0.5  # neutral
if self.embedding_weight > 0 and self._embedder.available and fact.get("embedding_vector"):
    qvec = self._embedder.encode(query)
    fvec = Embedder.bytes_to_vector(fact["embedding_vector"])
    emb_sim = Embedder.cosine_similarity(qvec, fvec)

relevance = (fts_weight * fts_score
             + jaccard_weight * jaccard
             + hrr_weight * hrr_sim
             + embedding_weight * emb_sim)
```

### 6. Wire config through the provider

In the MemoryProvider's `initialize()`:

```python
embedding_model = self._config.get("embedding_model", "") or ""
embedding_weight = float(self._config.get("embedding_weight", 0.5))

if embedding_model:
    self._embedder = Embedder(model_name=embedding_model)
    if not self._embedder.available:
        embedding_weight = 0.0
else:
    embedding_weight = 0.0

self._store = MemoryStore(db_path=db_path, embedder=self._embedder)
backfilled = self._store.compute_all_embeddings()

self._retriever = FactRetriever(
    store=self._store,
    embedding_weight=embedding_weight,
)
```

## Config Schema

Add these to `get_config_schema()`:

```python
{"key": "embedding_model",
 "description": "Sentence-transformers model (e.g. BAAI/bge-large-zh-v1.5)",
 "default": ""},
{"key": "embedding_weight",
 "description": "Weight for embedding similarity in hybrid search",
 "default": "0.5"},
```

## Pitfalls

- **PyTorch is large (~400MB CPU-only).** The `sentence-transformers` pip
  dependency pulls `torch` which itself pulls CUDA toolkit packages if
  resolved from the default index. Install with `--index-url
  https://download.pytorch.org/whl/cpu` to get CPU-only torch, or accept
  the full CUDA download. Either way, it takes 5-15 minutes.

- **Graceful fallback is mandatory.** If sentence-transformers is not
  installed or the model can't load, the plugin must work exactly as before.
  The `embedding_weight` should be forced to 0.0 in that case.

- **Thread safety.** The Embedder class must use singletons (global cache
  with lock) because Hermes may initialize the plugin multiple times
  across sessions. Loading the same model twice wastes memory and time.

- **Numpy is required for HRR + embeddings.** If numpy is missing, HRR
  operations fail silently. Install numpy in the Hermes venv first:
  `pip install numpy`.

- **Backfill on initialize.** When the embedding model is first configured,
  existing facts won't have `embedding_vector`. Call `compute_all_embeddings()`
  in `initialize()` to backfill them on startup.

- **Chinese text handling.** The default HRR `encode_text()` tokenizes by
  splitting on whitespace, which is meaningless for CJK text. Adding
  sentence-transformers embeddings is essential for Chinese-language memory
  retrieval. The BGE family (`BAAI/bge-large-zh-v1.5`, `BAAI/bge-small-zh-v1.5`)
  is purpose-built for Chinese.

- **SELECT f.* includes the BLOB column.** When the retriever uses
  `SELECT f.*`, the `embedding_vector` BLOB is automatically included in
  results. No column-list change needed, but be aware that the BLOB adds
  ~1-4KB per row to the result set.

- **Restart required.** Plugin config changes take effect on the next
  session (`/reset` or new `hermes` invocation). Running config is
  snapshotted at initialization.

## Verification

After implementing:

```bash
# 1. Verify all modules import cleanly (even without sentence-transformers)
python -c "from plugins.memory.holographic import HolographicMemoryProvider"

# 2. Verify config loads
hermes config | grep -A2 embedding

# 3. Check memory status
hermes memory status

# 4. Start a new session and test
hermes
# → /reset to reload config if already in a session
# → Use fact_store(action='add', content='测试中文记忆', category='general')
# → Then fact_store(action='search', query='中文')
```

## Related

- `references/holographic-embedding-integration.md` — full code walkthrough,
  error transcripts, and concrete file diffs for the holographic plugin
