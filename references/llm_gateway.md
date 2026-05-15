# Internal LLM Gateway

Base URL:

```text
https://imllm.intermesh.net
```

Endpoint:

```text
POST /v1/chat/completions
```

Headers:

```text
Authorization: Bearer <access-key>
Content-Type: application/json
```

Environment variables:

```env
IM_LLM_BASE_URL=https://imllm.intermesh.net
IM_LLM_API_KEY=your_key_here
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1-mini
```

Never hardcode access keys.
