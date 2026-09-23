import json
import redis
from typing import Any, Optional
from app.core.config import settings
from app.core.logging import logger

class RedisService:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._fallback_store: dict = {}
        self._is_connected = False
        self._init_client()

    def _init_client(self):
        try:
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.5,
                socket_connect_timeout=1.5
            )
            # Test ping
            self._client.ping()
            self._is_connected = True
            logger.info("Successfully connected to Redis instance.")
        except Exception as e:
            self._is_connected = False
            self._client = None
            logger.warning(f"Redis unavailable ({e}). Gracefully falling back to resilient in-memory cache/bypass.")

    def get(self, key: str) -> Optional[str]:
        if self._is_connected and self._client:
            try:
                return self._client.get(key)
            except Exception as e:
                logger.warning(f"Redis get failed for {key}: {e}. Falling back.")
                self._is_connected = False
        return self._fallback_store.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self._is_connected and self._client:
            try:
                return bool(self._client.set(key, value, ex=ex))
            except Exception as e:
                logger.warning(f"Redis set failed for {key}: {e}. Falling back.")
                self._is_connected = False
        self._fallback_store[key] = value
        return True

    def get_json(self, key: str) -> Optional[Any]:
        val = self.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        try:
            val_str = json.dumps(value)
            return self.set(key, val_str, ex=ex)
        except Exception as e:
            logger.error(f"Failed to serialize JSON for Redis set: {e}")
            return False

    def delete(self, *keys: str) -> int:
        count = 0
        if self._is_connected and self._client:
            try:
                count = self._client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}. Falling back.")
                self._is_connected = False
        for k in keys:
            if k in self._fallback_store:
                del self._fallback_store[k]
                count += 1
        return count

    def delete_pattern(self, pattern: str) -> int:
        """Invalidate keys matching a glob pattern (e.g., 'products:*')."""
        deleted_count = 0
        if self._is_connected and self._client:
            try:
                keys = self._client.keys(pattern)
                if keys:
                    deleted_count = self._client.delete(*keys)
                    return deleted_count
            except Exception as e:
                logger.warning(f"Redis delete_pattern failed: {e}. Falling back.")
                self._is_connected = False
        
        # In-memory wildcard match fallback
        import fnmatch
        keys_to_del = [k for k in self._fallback_store.keys() if fnmatch.fnmatch(k, pattern)]
        for k in keys_to_del:
            del self._fallback_store[k]
            deleted_count += 1
        return deleted_count

    def ping(self) -> bool:
        if self._client:
            try:
                return bool(self._client.ping())
            except Exception:
                return False
        return False

redis_client = RedisService()
