# agentmemory MCP + Plugin Integration Reference

## Overview

[agentmemory](https://github.com/rohitg00/agentmemory) is a persistent cross-session memory system powered by the iii-engine runtime. It integrates with Hermes Agent via two parallel paths:

## Path 1: MCP Stdio Server

Provides `memory_recall`, `memory_save`, `memory_search` tools via the `@agentmemory/mcp` npm package.

### Configuration (`~/.hermes/config.yaml`)

```yaml
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

### Env Vars Explained

| Variable | Purpose |
|----------|---------|
| `STANDALONE_MCP=1` | Run MCP shim without needing full iii-engine worker. Falls back to InMemoryKV if the HTTP backend is unreachable. |
| `STANDALONE_PERSIST_PATH` | SQLite-backed persistence path for standalone mode. |
| `AGENTMEMORY_URL` | Backend REST API URL. MCP shim proxies to this when available. |

### Fallback Behaviour

- If the backend (port 3111) is reachable → tools proxy to full agentmemory server
- If unreachable → tools use local `InMemoryKV` (subset of features, limited tool set)

## Path 2: Python MemoryProvider Plugin

Provides deep agent lifecycle hooks. Installed as a Hermes memory plugin.

### Location

`~/.hermes/hermes-agent/plugins/memory/agentmemory/`

### Files

- `__init__.py` — `AgentMemoryProvider` class with HTTP client to `http://localhost:3111/agentmemory/*`
- `plugin.yaml` — declares hooks: `prefetch`, `sync_turn`, `on_session_end`, `on_pre_compress`, `on_memory_write`, `system_prompt_block`

### Hooks Implemented

| Hook | Purpose |
|------|---------|
| `system_prompt_block` | Injects relevant past memories into the system prompt |
| `prefetch` | Searches memory for context related to incoming user message |
| `sync_turn` | Logs user/assistant turn as an observation |
| `on_session_end` | Notifies agentmemory to close the session |
| `on_pre_compress` | Injects context before context window compaction |
| `on_memory_write` | Mirrors built-in Hermes memory tool writes to agentmemory |

### Registration

```python
def register(ctx):
    ctx.register_memory_provider(AgentMemoryProvider())
```

## Backend: agentmemory Server

The REST API backend that both paths depend on for full functionality.

### Architecture

```
agentmemory CLI (Node.js)
    │
    ├── spawns iii-engine (child process, port 49134 WebSocket)
    │
    └── connects via iii-sdk → registers 50+ functions + REST triggers
                                    │
                                    └── port 3111 HTTP API (/agentmemory/*)
```

### Installation

```bash
npm install -g @agentmemory/agentmemory @agentmemory/mcp
```

The iii-engine binary is auto-downloaded on first `agentmemory` run.

### Starting

```bash
agentmemory  # starts both iii-engine + worker, serves on port 3111
```

### Configuration

`~/.agentmemory/.env`:

```ini
AGENTMEMORY_HOST=0.0.0.0
AGENTMEMORY_PORT=3111
AGENTMEMORY_INJECT_CONTEXT=true
AGENTMEMORY_AUTO_COMPRESS=true
AGENTMEMORY_SLOTS=memory
AGENTMEMORY_TOOLS=all
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agentmemory/session/start` | POST | Begin a new session |
| `/agentmemory/session/end` | POST | End a session |
| `/agentmemory/remember` | POST | Save a memory |
| `/agentmemory/search` | POST | BM25 keyword search |
| `/agentmemory/smart-search` | POST | Hybrid semantic + keyword search |
| `/agentmemory/context` | POST | Get context for current session |
| `/agentmemory/observe` | POST | Log an observation |
| `/healthz` | GET | Health check |
| `/agentmemory/status` | GET | Server status |

### LLM Provider

Without an API key, agentmemory runs in **noop/BM25-only** mode — observations are indexed via synthetic compression, hybrid search works, but LLM-backed features (summarisation, reflection, consolidation, knowledge graph extraction) are disabled. Set one of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or `MINIMAX_API_KEY` in `~/.agentmemory/.env` to enable full features.

## Verification Commands

```bash
# Check backend health
agentmemory status

# Test memory operations
curl -X POST http://localhost:3111/agentmemory/remember \
  -H 'Content-Type: application/json' \
  -d '{"content":"test","type":"fact"}'

curl -X POST http://localhost:3111/agentmemory/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","limit":5}'
```

## Systemd Service

```ini
[Unit]
Description=agentmemory - Persistent memory for AI coding agents
After=network.target

[Service]
Type=simple
EnvironmentFile=/root/.agentmemory/.env
ExecStart=/root/.hermes/node/bin/agentmemory
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```
