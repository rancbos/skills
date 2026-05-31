---
name: hermes-external-memory-providers
description: "Install and configure third-party memory backends for Hermes Agent that require external infrastructure — npm packages, HTTP servers, MCP bridges, and Python client plugins. Covers the plugin lifecycle: discovery, deployment, configuration, and verification."
version: 1.0.0
author: Hermes Agent
tags:
  - hermes
  - memory
  - plugins
  - integration
trigger: user asks to install, configure, or replace a Hermes memory provider from an external source (GitHub, npm, Docker) — not a bundled plugin
platforms: [linux, macos]
---

# Installing External Memory Providers for Hermes Agent

Hermes Agent ships with several bundled memory providers (`holographic`, `hindsight`, `mem0`, `honcho`, etc.) under `plugins/memory/`. Third-party providers live in the same directory alongside bundled ones. Only one provider can be active at a time, selected via `memory.provider` in `config.yaml`.

## Architecture Overview

External memory backends for Hermes typically follow one of two patterns:

### Pattern A: Python Package (pip)
A pure-Python provider installable via `pip` that imports directly.
- Plugin goes in `~/.hermes/plugins/<name>/` (user-installed) or `plugins/memory/<name>/` (bundled)
- Standard `MemoryProvider` ABC with `register(ctx)` entry point
- Example: `mem0`, `honcho`

### Pattern B: Server + Client (most common for complex backends)
A standalone server (Node.js, Go, Rust) with a thin Python HTTP client plugin.
- **Python plugin** lives under `plugins/memory/<name>/` — implements `MemoryProvider` ABC, speaks HTTP to a local server
- **Server process** runs as a background daemon (Node.js, Docker, binary)
- **MCP server** (optional) bridges additional tools through the `mcp_servers` config
- Example: `agentmemory` (npm package + iii-engine)

## Step-by-Step Installation

### 1. Identify the Plugin Source

Scan the external repo for a Hermes integration:

```bash
# Look for integrations/hermes/ or plugin/ directories
# Check the GitHub repo tree for:
# - integrations/hermes/__init__.py   → Python plugin
# - integrations/hermes/plugin.yaml   → Plugin metadata
# - packages/mcp/                     → MCP server package
# - plugin/.mcp.json                  → MCP plugin config
```

### 2. Install Runtime Dependencies

For a Node.js-backed provider:

```bash
# Install the server package globally
npm install -g @provider/package @provider/mcp-package

# Verify binaries exist
ls $(npm root -g)/../bin/
```

The `--ignore-scripts` flag may be needed if optional native deps (onnxruntime, etc.) hang during compilation.

### 3. Deploy the Hermes Plugin

Create the plugin directory and copy the `__init__.py` from the external repo:

```bash
mkdir -p ~/.hermes/hermes-agent/plugins/memory/<provider-name>
```

The plugin file should:
- Import `from agent.memory_provider import MemoryProvider`
- Define a class implementing `MemoryProvider` ABC
- Define a `register(ctx)` function that calls `ctx.register_memory_provider(...)`

Create `plugin.yaml` with hook declarations:

```yaml
name: <provider-name>
version: <version>
description: "..."
author: "..."
homepage: "..."
hooks:
  - prefetch
  - sync_turn
  - on_session_end
  - on_pre_compress
  - on_memory_write
  - system_prompt_block
```

### 4. Update Hermes Configuration

Change the memory provider in `~/.hermes/config.yaml`:

```yaml
memory:
  provider: <provider-name>    # was: holographic
```

### 5. Configure MCP Server (optional)

For providers that expose MCP tools, add a `mcp_servers` entry:

```yaml
mcp_servers:
  <provider-name>:
    command: /path/to/mcp-binary
    env:
      KEY: value
    timeout: 120
    connect_timeout: 60
```

The MCP server makes the provider's tools available globally in every Hermes conversation. Install the `mcp` Python package first:

```bash
pip install mcp
```

### 6. Start the Backend Server

Most external providers need a long-running daemon:

```bash
# Start the provider's HTTP server in background
/path/to/provider-server 2>&1 &

# Verify it's running
curl http://localhost:<port>/health
```

If the provider relies on a separate engine binary (e.g., iii-engine for agentmemory), that binary must also be functional. A segfault or missing binary blocks the whole service.

### 7. Restart and Verify

```bash
# Restart Hermes to pick up new config
# Check that the new provider loads:
hermes memory status
```

## Common Pitfalls

- **Not on PyPI.** Many third-party memory solutions are npm/Go/Docker projects, not Python packages. `pip install` will timeout or fail. Install via the project's native package manager.
- **Plugin discovery path.** Bundled providers (`plugins/memory/<name>/`) take precedence over user-installed ones (`$HERMES_HOME/plugins/<name>/`). If you're replacing a bundled plugin, put the new one in the same directory.
- **Network latency.** GitHub release downloads (especially large binaries like iii-engine at ~20MB) can be extremely slow from some regions. Use a longer timeout or a mirror/CDN.
- **Protected config file.** `~/.hermes/config.yaml` is protected from `write_file`/`patch`. Use `sed` or `terminal` to edit it.
- **Plugin hooks mismatch.** If the plugin declares hooks (in `plugin.yaml`) that the `__init__.py` doesn't implement, Hermes logs warnings but doesn't crash. Verify the hook names match exactly.
- **iii-engine segfault.** The agentmemory provider depends on iii-engine, which is a Rust binary downloaded at startup. An existing but broken binary (version mismatch, corrupted download) causes SIGSEGV. Fix: delete the broken binary and retry the `agentmemory doctor` process, or download the correct release manually.
- **Standalone MCP fallback.** When the full server (with iii-engine) can't start, many providers offer a standalone MCP mode using local SQLite. Look for `STANDALONE_MCP=1` or similar env flags. This gives partial functionality (tools work, server features like consolidation are disabled).
- **Restart required.** Plugin and MCP server config changes take effect on Hermes restart or `/reset`. Running config is snapshotted at initialization.

## Verification Checklist

After installation:

- [ ] Plugin directory exists with `__init__.py` and `plugin.yaml`
- [ ] `memory.provider` in config.yaml matches the plugin's `name` property
- [ ] Server daemon is running and responding on its port
- [ ] `hermes memory status` shows the provider as available
- [ ] MCP server connects (if configured): check startup logs for "connected"
- [ ] New session can call provider's tools (memory_recall, memory_save, etc.)

## Backup & Migration

External memory providers store data in external processes, not in Hermes's own state. When replacing devices, data must be backed up separately.

### Data Storage Pattern

Most server-based providers (agentmemory, mem0 with server, etc.) store data in files outside the plugin directory. Identify them by inspecting:

```bash
# Common locations
/root/data/                    # iii-engine data (agentmemory)
~/.mem0/                       # mem0 local storage
$XDG_DATA_HOME/<provider>/     # XDG-compliant locations
```

Important: the "file" may actually be a **directory** containing `.bin` or other file types (e.g., agentmemory's `state_store.db` is a kv-store directory with `.bin` files inside).

### What to Back Up

| Component | Example Path | Strategy |
|-----------|-------------|----------|
| Memory data | `/root/data/state_store.db/` | `cp -r` (it's a directory) |
| Provider config | `~/.agentmemory/.env` | copy |
| Server binary | `~/.local/bin/iii` | re-download on target |
| Python plugin | `plugins/memory/<name>/__init__.py` | copy |
| Hermes config delta | `memory.provider` + `mcp_servers` in config.yaml | note the lines |

### What NOT to Back Up

- **npm packages** — reinstall on target with `npm install -g`
- **Hermes itself** — reinstall separately
- **PID files, temp files, caches** — irrelevant on target

### Automated Backup Script

For agentmemory specifically, a backup script lives at `~/.agentmemory/backup-agentmemory.sh`. Pattern for other providers:

```bash
#!/bin/bash
BACKUP_DIR="${1:-$HOME/memory-backup-$(date +%Y%m%d)}"
mkdir -p "$BACKUP_DIR/data" "$BACKUP_DIR/config" "$BACKUP_DIR/plugin"

# Stop the server first
pkill -f "<provider-process>" 2>/dev/null; sleep 2

# Backup data
cp -r /root/data/state_store.db "$BACKUP_DIR/data/" 2>/dev/null

# Backup config
cp ~/.agentmemory/.env "$BACKUP_DIR/config/"

# Back up plugin
cp ~/.hermes/hermes-agent/plugins/memory/<name>/*.py "$BACKUP_DIR/plugin/"
```

### Restore Procedure

On the target device:
1. Install npm/Go/Rust dependencies (same versions)
2. Stop any running instance
3. Copy data into `/root/data/` (or equivalent)
4. Restore config files
5. Restore plugin files
6. Start the server
7. Restart Hermes

Full walkthrough for agentmemory in `references/backup-migration.md`.

## Embedding Configuration for Chinese

Many external memory providers default to **BM25 bag-of-words** indexing, which treats Chinese text as character-level tokens — no word segmentation, no semantic similarity. For adequate Chinese search, configure an embedding provider.

### Quick Setup (SiliconFlow)

```env
OPENAI_API_KEY=sk-xxx                          # SiliconFlow API key
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # Chinese-specific, 1024-dim
```

### Chinese Search Behaviour

| Provider | Default Search | Good For | Bad At |
|----------|---------------|----------|--------|
| BM25-only | Character-level keyword | Precise name/ID queries | Semantic / near-synonym search |
| + bge-large-zh-v1.5 | Hybrid BM25 + vector | 口语化查询 (`住哪里` → 地址), 近义搜索 (`沟通工具` → 微信飞书) | Cross-language (EN→ZH), highly abstract queries |
| + bge-m3 (multilingual) | Hybrid BM25 + vector | All of above + cross-language | — |

### Important: Old data has no vectors

Memories saved **before** embedding was configured are BM25-only. They won't appear in semantic search results. Re-save them or use the provider's backfill mechanism if available.

### Pitfall: Chinese-only model blocks cross-language

`bge-large-zh-v1.5` is a Chinese-only embedding model. English queries like `where does the user live` return empty results against Chinese memories. Use `BAAI/bge-m3` (multilingual) if you need English ↔ Chinese search.

*Detailed evaluation data in `references/chinese-embedding-tips.md`.*

## Adding Embedding Support to Memory Plugins

When a user requests a specific embedding model (e.g. `BAAI/bge-large-zh-v1.5`) for better semantic search, you need to modify the memory provider plugin to support sentence-transformers. This is a common extension pattern for any memory backend.

### Architecture

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

### Implementation Pattern

**1. Add Embedder class** — thread-safe singleton with lazy loading:
```python
class Embedder:
    def __init__(self, model_name=None):
        self.model_name = model_name
        self._model = None
        if model_name: self._load_model()

    def _load_model(self):
        # Global cache + threading lock — loads model once per name
        # normalize_embeddings=True so cosine sim = dot product
        # Never raise — log warnings, return None on failure
```

**2. Extend SQLite schema** — add `embedding_vector BLOB` column via `ALTER TABLE` migration.

**3. Store embeddings on write** — in `_compute_hrr_vector()`, also encode and store embedding.

**4. Add retrieval helpers** — `get_all_embedding_vectors()`, `compute_all_embeddings()` for backfill.

**5. Integrate into search pipeline** — add embedding cosine similarity alongside FTS/Jaccard/HRR signals:
```python
relevance = (fts_weight * fts_score
             + jaccard_weight * jaccard
             + hrr_weight * hrr_sim
             + embedding_weight * emb_sim)
```

**6. Wire config** — `embedding_model` and `embedding_weight` in provider config, force weight=0 if model unavailable.

### Key Pitfalls

- **PyTorch is large (~400MB CPU-only).** Install with `--index-url https://download.pytorch.org/whl/cpu` for CPU-only torch.
- **Graceful fallback is mandatory.** If sentence-transformers missing, plugin must work exactly as before with embedding_weight=0.
- **Thread safety.** Use global cache with lock — Hermes may initialize plugin multiple times across sessions.
- **Backfill on initialize.** Call `compute_all_embeddings()` in `initialize()` to backfill existing facts.
- **Chinese text.** Default HRR tokenization is whitespace-based (useless for CJK). BGE family (`BAAI/bge-large-zh-v1.5`) is purpose-built for Chinese.
- **`trust_remote_code=True`** needed for BGE models (they use custom code).

### Detailed Walkthrough

See `references/holographic-embedding-integration.md` for complete code diffs and the exact modifications applied to the holographic plugin.

## Related

- `native-mcp` skill — MCP server configuration reference
- `references/agentmemory-setup.md` — concrete agentmemory installation walkthrough
- `references/chinese-embedding-tips.md` — Chinese search quality evaluation and multilingual model recommendations
- `references/backup-migration.md` — data backup, restore, and cross-device migration procedures
- `references/holographic-embedding-integration.md` — full embedding integration walkthrough with code diffs
