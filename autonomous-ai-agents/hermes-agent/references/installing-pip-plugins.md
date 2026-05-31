# Installing pip-distributed Hermes plugins

Some Hermes plugins are distributed as Python packages on PyPI (e.g. `rtk-hermes`, `hermes-memory-store`). These are NOT installed via `hermes plugins install` — that CLI only works for built-in/bundled plugins shipped with Hermes itself.

## Installation steps

### 1. Find Hermes' Python executable

```bash
# Standard source install
HERMES_PY="$HOME/.hermes/hermes-agent/venv/bin/python"

# If using a symlinked shim, resolve the real path:
HERMES_BIN="$(command -v hermes)"
HERMES_REAL="$(python3 -c 'import os; print(os.path.realpath(sys.argv[1]))' "$HERMES_BIN")"
HERMES_PY="$(dirname "$HERMES_REAL")/python"
```

**Must be the venv Python**, not the system Python. Installing into a random venv won't make the plugin visible to Hermes.

### 2. pip install into Hermes' venv

```bash
"$HERMES_PY" -m pip install --upgrade <package-name>
```

If pip is missing from the venv (Hermes strips it from bundled installs for size), use `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
~/.local/bin/uv pip install --python "$HERMES_PY" --upgrade <package-name>
```

### 3. Enable in config.yaml

Add the plugin's entry point name to `plugins.enabled`:

```yaml
plugins:
  enabled:
    - rtk-rewrite     # example: entry point for rtk-hermes
```

**Do not rely on `hermes plugins enable <name>`.** That CLI command may not recognize pip-only entry points even when the plugin is correctly installed. Editing `plugins.enabled` directly in `~/.hermes/config.yaml` is the reliable path.

### 4. Restart Hermes

Plugins are discovered at startup. Start a new session (`/reset`) or restart the gateway process.

## Common pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Installed into wrong Python | Use Hermes' venv Python, not system Python |
| `No module named pip` | Bundled venv stripped pip | Use `uv pip install --python ...` |
| Plugin loaded but hook doesn't fire | Entry point name wrong in config | Check the plugin's `pyproject.toml` for the correct entry point name under `[project.entry-points."hermes_agent.plugins"]` |
| `hermes plugins install URL` fails | URL-based plugin install only works for Hermes-distributed plugins | Install via pip into venv + manual config edit |
| "This environment is externally managed" | Using system pip instead of venv pip | Point pip/uv at Hermes' venv Python, never use `--break-system-packages` |

## Verification

```bash
# Check plugin module loads
"$HERMES_PY" -c "import <plugin_module>; print('OK')"

# Check config entry
grep -A2 'enabled' ~/.hermes/config.yaml
```
