# agentmemory Setup Walkthrough

Concrete installation record for [agentmemory](https://github.com/rohitg00/agentmemory) v0.9.21 as a Hermes Agent memory provider, Linux x86_64.

## Component Versions

| Component | Version | Source |
|-----------|---------|--------|
| @agentmemory/agentmemory | 0.9.21 | npm |
| @agentmemory/mcp | 0.9.21 | npm |
| iii-engine | 0.11.2 | GitHub release |
| Hermes plugin | 0.8.0 | integrations/hermes/ in repo |

## System Dependencies Pre-Check

- Node.js >= 20 (was v22.22.3)
- npm (was 10.9.8)
- Python 3.10+ with `mcp` package (`pip install mcp`)
- Linux x86_64

## Installation Sequence

### 1. npm Packages

```bash
npm install -g @agentmemory/agentmemory @agentmemory/mcp --ignore-scripts
```

The `--ignore-scripts` flag avoids hanging on optional native deps (onnxruntime-node). Binaries land at `$(npm root -g)/../bin/`:
- `agentmemory` — main CLI / server daemon
- `agentmemory-mcp` — stdio MCP bridge

### 2. Hermes Plugin

Plugin directory: `plugins/memory/agentmemory/` (bundled, takes precedence)

Two files:
- **`__init__.py`** — `AgentMemoryProvider` class, HTTP client to `http://localhost:3111/agentmemory/`. 384 lines, from repo at `integrations/hermes/__init__.py`.
- **`plugin.yaml`** — declares 6 hooks: `prefetch`, `sync_turn`, `on_session_end`, `on_pre_compress`, `on_memory_write`, `system_prompt_block`.

### 3. iii-Engine v0.11.2

agentmemory relies on the iii-engine binary for storage. The doctor (`agentmemory doctor --all`) tries to auto-install, but it may fail silently. Manual install:

```bash
# Download from GitHub Releases (~33MB)
curl -sL --connect-timeout 30 --max-time 300 \
  -o /tmp/iii.tar.gz \
  "https://github.com/iii-hq/iii/releases/download/iii/v0.11.2/iii-x86_64-unknown-linux-gnu.tar.gz"

# Extract
tar xzf /tmp/iii.tar.gz -C /tmp/
mv /tmp/iii /root/.local/bin/iii
chmod +x /root/.local/bin/iii

# Verify
/root/.local/bin/iii --version  # → 0.11.2
```

**Pitfall: segfault on startup.** If the binary is corrupted (partial download, version mismatch), iii-engine will crash with SIGSEGV and agentmemory logs "iii-engine did not become ready within 15s". Fix: delete the old binary and re-download. The musl variant (`-musl.tar.gz`) is statically linked and may avoid some glibc compatibility issues.

### 4. Configuration

Config directory: `~/.agentmemory/.env`

```env
AGENTMEMORY_HOST=0.0.0.0
AGENTMEMORY_PORT=3111
AGENTMEMORY_INJECT_CONTEXT=true
AGENTMEMORY_AUTO_COMPRESS=true
AGENTMEMORY_SLOTS=memory
AGENTMEMORY_TOOLS=all
```

### 5. Starting the Server

```bash
/root/.hermes/node/bin/agentmemory
```

This starts both the agentmemory worker (Node.js) and the iii-engine subprocess. Verify:

```bash
/root/.hermes/node/bin/agentmemory status
```

Expected output fields: `Health: ✓ healthy`, `Provider: ✓ llm` (or ✗ noop), `Embeddings: ✓ embeddings` (or bm25-only).

Ports used: 3111 (REST API), 3113 (viewer), 49134 (iii-engine WebSocket).

### 6. Hermes Config

Edit `~/.hermes/config.yaml`:

```yaml
memory:
  provider: agentmemory    # was: holographic

mcp_servers:
  agentmemory:
    command: /root/.hermes/node/bin/agentmemory-mcp
    env:
      STANDALONE_MCP: "1"
      STANDALONE_PERSIST_PATH: "/root/.agentmemory/local.db"
      AGENTMEMORY_URL: "http://localhost:3111"
    timeout: 120
    connect_timeout: 60
```

### 7. Systemd Service (optional)

Service file at `~/.agentmemory/agentmemory.service`:

```ini
[Unit]
Description=agentmemory - Persistent memory for AI coding agents
Documentation=https://github.com/rohitg00/agentmemory
After=network.target

[Service]
Type=simple
User=root
EnvironmentFile=/root/.agentmemory/.env
ExecStart=/root/.hermes/node/bin/agentmemory
WorkingDirectory=/root
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=agentmemory
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

Deploy: `cp ~/.agentmemory/agentmemory.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable agentmemory && systemctl start agentmemory`.

## Verification Commands

```bash
# API health
curl -s http://localhost:3111/agentmemory/status

# Save a memory
curl -s -X POST http://localhost:3111/agentmemory/remember \
  -H 'Content-Type: application/json' \
  -d '{"content":"test memory","type":"fact"}'

# Search
curl -s -X POST http://localhost:3111/agentmemory/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","limit":5}'

# Semantic search (requires embedding provider)
curl -s -X POST http://localhost:3111/agentmemory/smart-search \
  -H 'Content-Type: application/json' \
  -d '{"query":"住哪里","limit":5}'
```

## Known Issues

- **GitHub release downloads are slow** from some regions. Use `--max-time 600`, a proxy, or ghproxy.com.
- **iii-engine 0.11.2** is pinned by agentmemory v0.9.21. Newer iii versions (≥0.11.6) use a different sandbox model and are incompatible without a refactor.
- **Standalone MCP mode** (`STANDALONE_MCP=1`) uses an in-memory KV store backed by JSON, not the full iii-engine. Persistent across restarts via `STANDALONE_PERSIST_PATH`, but lacks consolidation, graph extraction, and other full-server features.
- **Embedding config is NOT hot-reloadable.** Must restart the agentmemory process after changing `.env`.
