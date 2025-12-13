from __future__ import annotations

import json
from typing import AsyncIterator, Dict, Any


async def sse_content(resp) -> AsyncIterator[str]:
    """Parse OpenAI-style SSE stream and yield content deltas."""
    async for line in resp.aiter_lines():
        if not line:
            continue
        if not line.startswith("data:"):
            continue
        data = line[len("data:"):].strip()
        if data == "[DONE]":
            break
        try:
            obj = json.loads(data)
        except Exception:
            continue
        # OpenAI compatible chunk format
        try:
            delta = obj["choices"][0]["delta"]
            content = delta.get("content")
            if content:
                yield content
        except Exception:
            continue
