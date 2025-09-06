import json
from typing import Any, List, Optional

import redis.asyncio as redis

from app.config import get_settings


class RedisCache:
    def __init__(self, url: str):
        self.client = redis.from_url(url, decode_responses=True)
        self.key_recent = "flagged_recent"
        self.max_recent = 100

    async def push_flagged(self, tx_id: str, payload: Optional[dict] = None) -> None:
        pipe = self.client.pipeline()
        await pipe.lpush(self.key_recent, tx_id)
        await pipe.ltrim(self.key_recent, 0, self.max_recent - 1)
        if payload is not None:
            await pipe.set(f"tx:{tx_id}", json.dumps(payload))
        await pipe.execute()

    async def recent_flagged_ids(self, limit: int = 50) -> List[str]:
        return await self.client.lrange(self.key_recent, 0, max(0, limit - 1))


_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    global _cache
    if _cache is None:
        settings = get_settings()
        _cache = RedisCache(settings.REDIS_URL)
    return _cache
