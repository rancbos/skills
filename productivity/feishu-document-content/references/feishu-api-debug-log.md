# Feishu Document API Debug Log

Record of API calls made during the 2026-05-25 session, mapping what worked and what didn't against Feishu Open API endpoints.

## Context

- Feishu app was missing `drive:file:upload` scope → Import API failed initially
- After scope was granted by admin, Import API worked immediately
- Block API (`POST /children`) worked for individual blocks but was impractical for full documents

## Endpoint Test Matrix

### Authentication

| Endpoint | Method | Result |
|----------|--------|--------|
| `open-apis/auth/v3/tenant_access_token/internal` | POST | ✅ Returns `tenant_access_token` with 3600s expiry |

### Document Operations

| Endpoint | Method | Result | Notes |
|----------|--------|--------|-------|
| `docx/v1/documents/{id}` | GET | ✅ | Returns document metadata, title, revision |
| `docx/v1/documents/{id}` | PATCH (update title) | ❌ invalid param | Title cannot be changed after creation |
| `docx/v1/documents/{id}/blocks/{block_id}` | GET | ✅ | Returns block type, elements, children list |
| `docx/v1/documents/{id}/blocks/{block_id}` | PATCH (update block) | ❌ invalid param | Block update not supported |
| `docx/v1/documents/{id}/blocks/{block_id}/content` | PATCH | ❌ 404 | Content update endpoint does not exist |
| `docx/v1/documents/{id}/blocks/{block_id}` | DELETE | ❌ 404 | Block deletion not supported |
| `docx/v1/documents/{id}/blocks/{block_id}/children` | POST | ✅ | Creates child blocks (the only working write endpoint) |
| `docx/v1/documents/{id}/blocks/{block_id}/children` | GET | ✅ | Lists children with pagination |
| `docx/v1/documents/{id}/blocks/{block_id}/children/batch_update` | POST | ❌ 404 | Batch update endpoint does not exist |
| `docx/v1/documents/{id}/blocks/{block_id}/children/batch_update` | PATCH | ❌ 404 | Also doesn't exist |

### Drive Operations

| Endpoint | Method | Result | Notes |
|----------|--------|--------|-------|
| `drive/v1/files/upload_all` | POST (multipart) | ✅ | Uploads a local file to Drive |
| `drive/v1/import_tasks` | POST | ✅ | Creates async import task (md→docx) |
| `drive/v1/import_tasks/{ticket}` | GET | ✅ | Polls import status; `job_status: 0` = done |
| `drive/v1/files/{token}?type=docx` | DELETE | ✅ | Deletes a document |
| `drive/v1/files/{token}?type=file` | DELETE | ✅ | Deletes an uploaded file |

## Block Type Reference

```python
BLOCK_TYPES = {
    1:  "Page",       # Document root (block_id == document_id)
    2:  "Text",       # Paragraph
    3:  "Heading1",   # JSON key: "heading1"
    4:  "Heading2",   # JSON key: "heading2"
    5:  "Heading3",   # JSON key: "heading3"
    6:  "Heading4",   # JSON key: "heading4"
    7:  "Heading5",   # JSON key: "heading5"
    8:  "Heading6",   # JSON key: "heading6"
    9:  "Heading7",   # JSON key: "heading7"
    10: "Heading8",   # JSON key: "heading8"
    11: "Heading9",   # JSON key: "heading9"
    12: "Bullet",     # Bullet list item
    13: "Ordered",    # Ordered list item
    14: "Code",       # Code block (in markdown import)
    15: "Quote",      # Blockquote (in markdown import)
    22: "Divider",    #  ---
}
```

## Example: Creating a Heading Block

```bash
curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/$DOC_ID/blocks/$PARENT_ID/children" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [{
      "block_type": 3,
      "heading1": {
        "elements": [{
          "text_run": {
            "content": "Section Title",
            "text_element_style": {}
          }
        }],
        "style": {}
      }
    }],
    "index": -1
  }'
```

## Key Lesson

The **only** reliable way to put structured content into a Feishu document is:
1. Write content as markdown in a local file
2. Upload via `drive/v1/files/upload_all` (multipart form)
3. Import via `drive/v1/import_tasks` (specifying `type: docx`)
4. Poll until `job_status: 0`
5. Clean up the uploaded markdown file

Block-by-block API is only suitable for adding single elements to an existing document, but you can never delete or modify blocks afterward.
