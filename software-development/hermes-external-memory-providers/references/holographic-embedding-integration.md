# Holographic Plugin: BGE Embedding Integration Walkthrough

This document records the exact modification applied to extend the
Hermes holographic memory plugin with `BAAI/bge-large-zh-v1.5` embeddings.

## Files Modified

| File | Purpose |
|------|---------|
| `plugins/memory/holographic/holographic.py` | Added `Embedder` class + `threading` import |
| `plugins/memory/holographic/store.py` | Added `embedding_vector` column, embedder param, backfill |
| `plugins/memory/holographic/retrieval.py` | Added `embedding_weight` to hybrid search scoring |
| `plugins/memory/holographic/__init__.py` | Wired `embedding_model` config + `embedder` to store/retriever |
| `plugins/memory/holographic/plugin.yaml` | v0.2.0, declared `sentence-transformers` dep |
| `plugins/memory/holographic/README.md` | Updated docs with embedding section |
| `~/.hermes/config.yaml` | Set `embedding_model: BAAI/bge-large-zh-v1.5` |

## Embedder Class (holographic.py)

The key design:

```python
try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except ImportError:
    SentenceTransformer = None
    _HAS_ST = False

_EMBEDDER_LOCK = threading.Lock()
_EMBEDDER_CACHE = {}

class Embedder:
    def __init__(self, model_name=None):
        self.model_name = model_name
        self._model = None
        self._dim = 0
        if model_name:
            self._load_model()

    def _load_model(self):
        if not _HAS_ST:
            return  # silently fail — weight = 0 will disable embedding search
        with _EMBEDDER_LOCK:
            if name in _EMBEDDER_CACHE:
                self._model = _EMBEDDER_CACHE[name]
            else:
                try:
                    self._model = SentenceTransformer(name, trust_remote_code=True)
                    _EMBEDDER_CACHE[name] = self._model
                except:
                    _EMBEDDER_CACHE[name] = None

    def encode(self, text):
        if not self.available or not text:
            return None
        vec = self._model.encode(text, normalize_embeddings=True)
        return np.array(vec, dtype=np.float32)

    @staticmethod
    def cosine_similarity(a, b):
        return float(np.dot(a, b))  # normalized vectors → dot = cosine

    @staticmethod
    def vector_to_bytes(vec):
        return vec.tobytes()

    @staticmethod
    def bytes_to_vector(data):
        return np.frombuffer(data, dtype=np.float32).copy() if data else None
```

Key decisions:
- `normalize_embeddings=True` makes dot-product equivalent to cosine similarity
- `trust_remote_code=True` is needed for BGE models (they use custom code)
- Global cache prevents reloading model across `initialize()` calls
- All failures degrade gracefully (returns None, caller handles weight=0)

## Schema Migration (store.py)

The `_init_db()` method:

```python
columns = {row[1] for row in self._conn.execute("PRAGMA table_info(facts)").fetchall()}
if "embedding_vector" not in columns:
    self._conn.execute("ALTER TABLE facts ADD COLUMN embedding_vector BLOB")
```

This is safe for existing databases — adds the column without dropping data.

## Hybrid Search Scoring (retrieval.py)

The retriever now normalizes weights dynamically:

```python
if embedding_weight > 0.0:
    total = fts_weight + jaccard_weight + hrr_weight + embedding_weight
    fts_weight /= total
    jaccard_weight /= total
    hrr_weight /= total
    embedding_weight /= total
```

Then in each fact's scoring loop:

```python
emb_sim = 0.5  # neutral baseline
if (self.embedding_weight > 0.0
    and self._embedder
    and self._embedder.available
    and fact.get("embedding_vector")):
    qvec = self._embedder.encode(query)
    fvec = hrr_module.Embedder.bytes_to_vector(fact["embedding_vector"])
    if qvec is not None and fvec is not None and len(fvec) > 0:
        emb_sim = hrr_module.Embedder.cosine_similarity(qvec, fvec)

relevance = (self.fts_weight * fts_score
             + self.jaccard_weight * jaccard
             + self.hrr_weight * hrr_sim
             + self.embedding_weight * emb_sim)
```

## Backfill on Initialize

```python
self._store = MemoryStore(db_path=db_path, embedder=self._embedder)
if self._embedder and self._embedder.available:
    backfilled = self._store.compute_all_embeddings()
    if backfilled:
        logger.info("Backfilled %d existing facts with embedding vectors", backfilled)
```

## Install Note

The sentence-transformers package pulls PyTorch, which on Linux tries to
install ~1GB of CUDA toolkit packages. To avoid this, either:

```bash
# CPU-only (faster download)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers --no-deps
pip install transformers huggingface-hub tokenizers numpy

# Or accept the full CUDA install (takes 5-15 min):
pip install sentence-transformers
```
