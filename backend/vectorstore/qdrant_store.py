from qdrant_client import AsyncQdrantClient

from backend.config.settings import get_settings

_client: AsyncQdrantClient | None = None


async def init_qdrant() -> None:
    global _client
    if _client is not None:
        return
    settings = get_settings()
    _client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


def get_qdrant() -> AsyncQdrantClient:
    if _client is None:
        raise RuntimeError("Qdrant is not initialized")
    return _client


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
