# OpenCode Provider Authentication Reference

## auth.json Format

Location: `~/.local/share/opencode/auth.json`

**Correct format** (provider name → API key string):
```json
{
  "openrouter": "sk-or-v1-xxxxxxxxxxxx",
  "anthropic": "sk-ant-xxxxxxxxxxxx"
}
```

**Wrong formats** (do NOT use):
```json
{ "openrouter": { "apiKey": "xxx" } }   ← nested object, ignored
{ "openrouter": { "api_key": "xxx" } }  ← snake_case, ignored
```

**Verification**: `opencode debug config` shows resolved config. If `"provider": { "openrouter": {} }` is empty, the auth.json format is wrong.

## API Key Format by Provider

| Provider | Key Format | Example |
|----------|-----------|---------|
| OpenRouter | `sk-or-v1-...` | `sk-or-v1-abc123...` |
| Anthropic | `sk-ant-api03-...` | `sk-ant-api03-abc123...` |
| OpenAI | `sk-...` | `sk-abc123...` |
| SiliconFlow | varies | `sk-...` |
| OpenCode Zen | `oc-...` | `oc-abc123...` |

**⚠️ Key format mismatch**: If the key doesn't match the expected prefix, authentication will fail with "Missing Authentication header". Always validate key prefix before configuring.

## Environment Variables

| Provider | Env Var |
|----------|---------|
| OpenRouter | `OPENROUTER_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| SiliconFlow | `SILICONFLOW_API_KEY` |
| Google | `GOOGLE_GENERATIVE_AI_APIKEY` |

**Note**: env vars are shown separately from auth.json credentials in `opencode providers list`.

## Built-in vs External Models

| Model | Auth Required |
|-------|---------------|
| `opencode/mimo-v2.5-free` | No (built-in) |
| `opencode/mimo-v2-free` | No (built-in) |
| `openrouter/xiaomi/mimo-v2.5-pro` | Yes (OpenRouter key) |
| `openrouter/xiaomi/mimo-v2-pro` | Yes (OpenRouter key) |

## Troubleshooting

### "Missing Authentication header"
1. Check key prefix matches provider
2. Check auth.json format (must be flat string, not nested object)
3. Try env var: `OPENROUTER_API_KEY=sk-or-... opencode run 'test'`
4. Verify: `opencode debug config` should show non-empty provider section

### "0 credentials" in providers list
- auth.json format is wrong (nested object instead of string)
- Correct: `{ "openrouter": "sk-or-..." }` not `{ "openrouter": { "apiKey": "..." } }`

### /connect command in TUI
- Interactive TUI command, not available via CLI
- Use `opencode providers login -p openrouter -m api-key` for CLI (requires PTY)
- Alternative: write auth.json directly (see format above)
