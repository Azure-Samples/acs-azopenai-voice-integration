import redis.asyncio as redis

from typing import Any, Optional
from ..utils.logger import setup_logger
import json

class CacheService:
    def __init__(self, redis_url: str, password: str):
        self.redis = redis.Redis(host=redis_url, port=6380, password=password, ssl=True)
        # Initialize logger
        self.logger = setup_logger(__name__) 

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self.redis.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Error getting key '{key}' from Redis: {e}", exc_info=True)
            return None

    async def set(self, key: str, value: Any, expire: int = None) -> None:
        try:
            serialized_value = json.dumps(value)
            await self.redis.set(name=key, value=serialized_value, ex=expire)
            self.logger.debug(f"Set key '{key}' in Redis with value: {value}")
        except Exception as e:
            self.logger.error(f"Error setting key '{key}' in Redis: {e}", exc_info=True)

    async def delete(self, key: str) -> None:
        try:
            await self.redis.delete(key)
            self.logger.debug(f"Deleted key '{key}' from Redis.")
        except Exception as e:
            self.logger.error(f"Error deleting key '{key}' from Redis: {e}", exc_info=True)

    async def delete_by_pattern(self, pattern: str) -> None:
        """Delete all keys matching a given pattern."""
        try:
            # Use scan_iter to efficiently iterate over keys matching the pattern
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)
                self.logger.debug(f"Deleted key '{key}'")
            self.logger.info(f"Deleted keys matching pattern '{pattern}'")
        except Exception as e:
            self.logger.error(f"Error deleting keys matching pattern '{pattern}': {e}", exc_info=True)

    async def clear(self) -> None:
        try:
            await self.redis.flushdb()
            self.logger.info("Successfully cleared Redis database.")
        except Exception as e:
            self.logger.error(f"Error clearing Redis database: {e}", exc_info=True)