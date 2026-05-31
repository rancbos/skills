# agentmemory Backup & Migration Guide

Complete procedure for backing up agentmemory data and restoring on a new device.

## Data Storage

agentmemory stores data via iii-engine in `/root/data/`:

| Path | Type | Content |
|------|------|---------|
| `/root/data/state_store.db/` | **Directory** (not a file) | All memories, observations, sessions, access logs — the core dataset |
| `/root/data/stream_store/` | Directory | Live stream data |

Note: `state_store.db` is a directory containing `.bin` files, NOT a single SQLite file. Always use `cp -r`.

## Full Backup Script

Pre-installed at `~/.agentmemory/backup-agentmemory.sh`:

```bash
# Backup to default location (~/agentmemory-backup-YYYYMMDD/)
bash ~/.agentmemory/backup-agentmemory.sh

# Backup to specific directory
bash ~/.agentmemory/backup-agentmemory.sh /path/to/backup
```

### Manual Backup

```bash
# 1. Stop services
pkill -f agentmemory 2>/dev/null; pkill -f iii 2>/dev/null; sleep 2

# 2. Data (core)
mkdir -p /tmp/backup/data /tmp/backup/config /tmp/backup/plugin
cp -r /root/data/state_store.db /tmp/backup/data/
cp -r /root/data/stream_store /tmp/backup/data/

# 3. Config
cp ~/.agentmemory/.env /tmp/backup/config/
cp ~/.agentmemory/preferences.json /tmp/backup/config/
cp ~/.agentmemory/agentmemory.service /tmp/backup/config/

# 4. Hermes plugin
cp ~/.hermes/hermes-agent/plugins/memory/agentmemory/__init__.py /tmp/backup/plugin/
cp ~/.hermes/hermes-agent/plugins/memory/agentmemory/plugin.yaml /tmp/backup/plugin/

# 5. Hermes config deltas
grep -A 1 "^memory:" ~/.hermes/config.yaml > /tmp/backup/config/hermes-memory-config.txt
grep -A 8 "^mcp_servers:" ~/.hermes/config.yaml > /tmp/backup/config/hermes-mcp-config.txt
```

## Restore on New Device

```bash
# 1. Install npm packages (same versions)
npm install -g @agentmemory/agentmemory @agentmemory/mcp

# 2. Stop any running services
pkill -f agentmemory 2>/dev/null; pkill -f iii 2>/dev/null; sleep 2

# 3. Restore data
rm -rf /root/data/state_store.db /root/data/stream_store 2>/dev/null
cp -r backup/data/state_store.db /root/data/
cp -r backup/data/stream_store /root/data/

# 4. Restore config
cp backup/config/.env ~/.agentmemory/
cp backup/config/preferences.json ~/.agentmemory/

# 5. Restore plugin
mkdir -p ~/.hermes/hermes-agent/plugins/memory/agentmemory/
cp backup/plugin/__init__.py ~/.hermes/hermes-agent/plugins/memory/agentmemory/
cp backup/plugin/plugin.yaml ~/.hermes/hermes-agent/plugins/memory/agentmemory/

# 6. Edit config.yaml (from backup/config/hermes-memory-config.txt + hermes-mcp-config.txt)
#    memory.provider: agentmemory
#    mcp_servers.agentmemory: ... (see backup)

# 7. Start server
/root/.hermes/node/bin/agentmemory &
sleep 10

# 8. Verify
/root/.hermes/node/bin/agentmemory status
# Should show previous Sessions/Observations/Memories count

# 9. Quick API test
curl -s http://localhost:3111/agentmemory/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","limit":3}'

# 10. Restart Hermes Agent
```

## Critical Rules

1. **Stop before backup.** iii-engine locks its data files while running. Backup with the server stopped.
2. **state_store.db is a directory.** Use `cp -r`, not `cp`.
3. **Same iii-engine version.** agentmemory v0.9.21 pins iii-engine v0.11.2. Newer versions use a different sandbox model.
4. **API keys are portable.** SiliconFlow keys in `.env` work on any device.
5. **Hermes config.yaml has to be edited manually.** The backup script extracts the relevant lines; paste them into the new device's config.
