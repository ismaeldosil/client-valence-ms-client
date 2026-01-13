"""Session store with Redis support for conversation continuity."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SessionData:
    """Session data stored for a user/conversation."""
    session_id: str
    user_id: str
    conversation_id: str
    created_at: str
    last_activity: str
    message_count: int = 0


class SessionStore(ABC):
    """Abstract base class for session stores."""

    @abstractmethod
    async def get(self, user_id: str, conversation_id: str) -> Optional[SessionData]:
        """Get session for user/conversation pair."""
        pass

    @abstractmethod
    async def set(self, user_id: str, conversation_id: str, session_id: str) -> None:
        """Store session for user/conversation pair."""
        pass

    @abstractmethod
    async def delete(self, user_id: str, conversation_id: str) -> bool:
        """Delete session for user/conversation pair."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get session store statistics."""
        pass


class MemorySessionStore(SessionStore):
    """In-memory session store (for development/fallback)."""

    def __init__(self, ttl_hours: int = 24):
        self._sessions: dict[str, SessionData] = {}
        self._ttl_hours = ttl_hours

    def _make_key(self, user_id: str, conversation_id: str) -> str:
        return f"{user_id}:{conversation_id}"

    async def get(self, user_id: str, conversation_id: str) -> Optional[SessionData]:
        key = self._make_key(user_id, conversation_id)
        session = self._sessions.get(key)
        if session:
            # Update last activity
            session.last_activity = datetime.now(UTC).isoformat()
            session.message_count += 1
        return session

    async def set(self, user_id: str, conversation_id: str, session_id: str) -> None:
        key = self._make_key(user_id, conversation_id)
        now = datetime.now(UTC).isoformat()
        self._sessions[key] = SessionData(
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            created_at=now,
            last_activity=now,
            message_count=1,
        )

    async def delete(self, user_id: str, conversation_id: str) -> bool:
        key = self._make_key(user_id, conversation_id)
        if key in self._sessions:
            del self._sessions[key]
            return True
        return False

    async def get_stats(self) -> dict:
        return {
            "type": "memory",
            "active_sessions": len(self._sessions),
        }


class RedisSessionStore(SessionStore):
    """Redis-backed session store for production."""

    def __init__(self, redis_url: str, ttl_hours: int = 24, key_prefix: str = "teams:session"):
        self._redis_url = redis_url
        self._ttl_seconds = ttl_hours * 3600
        self._key_prefix = key_prefix
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as redis
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _make_key(self, user_id: str, conversation_id: str) -> str:
        return f"{self._key_prefix}:{user_id}:{conversation_id}"

    async def get(self, user_id: str, conversation_id: str) -> Optional[SessionData]:
        try:
            r = await self._get_redis()
            key = self._make_key(user_id, conversation_id)
            data = await r.get(key)

            if data:
                session_dict = json.loads(data)
                session = SessionData(**session_dict)
                # Update last activity and message count
                session.last_activity = datetime.now(UTC).isoformat()
                session.message_count += 1
                await r.setex(key, self._ttl_seconds, json.dumps(session.__dict__))
                return session
            return None
        except Exception as e:
            logger.error("redis_get_error", error=str(e))
            return None

    async def set(self, user_id: str, conversation_id: str, session_id: str) -> None:
        try:
            r = await self._get_redis()
            key = self._make_key(user_id, conversation_id)
            now = datetime.now(UTC).isoformat()
            session = SessionData(
                session_id=session_id,
                user_id=user_id,
                conversation_id=conversation_id,
                created_at=now,
                last_activity=now,
                message_count=1,
            )
            await r.setex(key, self._ttl_seconds, json.dumps(session.__dict__))
        except Exception as e:
            logger.error("redis_set_error", error=str(e))

    async def delete(self, user_id: str, conversation_id: str) -> bool:
        try:
            r = await self._get_redis()
            key = self._make_key(user_id, conversation_id)
            result = await r.delete(key)
            return result > 0
        except Exception as e:
            logger.error("redis_delete_error", error=str(e))
            return False

    async def get_stats(self) -> dict:
        try:
            r = await self._get_redis()
            keys = await r.keys(f"{self._key_prefix}:*")
            return {
                "type": "redis",
                "active_sessions": len(keys),
                "connected": True,
            }
        except Exception as e:
            return {
                "type": "redis",
                "active_sessions": 0,
                "connected": False,
                "error": str(e),
            }

    async def close(self):
        if self._redis:
            await self._redis.close()


def create_session_store(store_type: str, redis_url: str, ttl_hours: int) -> SessionStore:
    """Factory function to create appropriate session store."""
    if store_type == "redis":
        logger.info("session_store_init", type="redis", ttl_hours=ttl_hours)
        return RedisSessionStore(redis_url, ttl_hours)
    else:
        logger.info("session_store_init", type="memory", ttl_hours=ttl_hours)
        return MemorySessionStore(ttl_hours)
