# SiliconFlow Embeddings API Reference

## API Endpoint

```
POST https://api.siliconflow.cn/v1/embeddings
Authorization: Bearer <api_key>
Content-Type: application/json
```

## Request Body

```json
{
  "model": "BAAI/bge-large-zh-v1.5",
  "input": "<text> or [<text1>, <text2>, ...]",
  "encoding_format": "float"
}
```

## Response

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.xxx, -0.xxx, ...]
    }
  ],
  "model": "BAAI/bge-large-zh-v1.5",
  "usage": {
    "prompt_tokens": N,
    "total_tokens": N
  }
}
```

## Supported Models

- `BAAI/bge-large-zh-v1.5` — 1024 dimensions, Chinese-optimized
- `BAAI/bge-large-en-v1.5` — 1024 dimensions, English-optimized
- `BAAI/bge-base-zh-v1.5` — 768 dimensions, lighter Chinese
- `text-embedding-3-small` — 512/1536 dims, OpenAI-compatible
- `text-embedding-3-large` — 256/1024/3072 dims, higher quality

## Pricing

SiliconFlow charges per token. BGE-large-zh-v1.5 is typically very affordable for memory-store scale usage (a few facts per session).

## Key Points

- Batched inputs (`["text1", "text2", ...]`) are more efficient than single calls
- BGE models output L2-normalized vectors — cosine similarity = dot product
- Rate limits: check https://siliconflow.cn for current limits
- Key stored in `SILICONFLOW_API_KEY` in Hermes `.env` file
