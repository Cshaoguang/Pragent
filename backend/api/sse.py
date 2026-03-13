import json
from collections.abc import AsyncIterator


def encode_sse(event: str, payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {data}\n\n"


async def sse_stream(events: AsyncIterator[tuple[str, object]]) -> AsyncIterator[str]:
    async for event_name, payload in events:
        yield encode_sse(event_name, payload)
