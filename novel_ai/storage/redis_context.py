"""Redis-backed storage for recent story summaries and excerpts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4


try:
    import redis
except ImportError:  # pragma: no cover - exercised when optional dependency is absent.
    redis = None


DEFAULT_NOVEL_ID = "default"


@dataclass(frozen=True)
class StoryContext:
    """Recent generation context used by the story chain."""

    story_name: str
    summary: str
    excerpt: str
    source: str


@dataclass(frozen=True)
class RedisContextConfig:
    """Redis context storage settings."""

    redis_url: Optional[str]
    novel_id: str
    context_ttl: Optional[int]
    recent_excerpt_chars: int
    enabled: bool = True


def load_redis_context_config(
    *,
    redis_url: Optional[str] = None,
    novel_id: Optional[str] = None,
    context_ttl: Optional[int] = None,
    recent_excerpt_chars: Optional[int] = None,
    enabled: bool = True,
) -> RedisContextConfig:
    """Load Redis storage config from CLI overrides and environment variables."""

    env_ttl = os.getenv("REDIS_CONTEXT_TTL", "").strip()
    ttl = context_ttl
    if ttl is None and env_ttl:
        ttl = int(env_ttl)

    env_excerpt_chars = os.getenv("REDIS_RECENT_EXCERPT_CHARS", "").strip()
    excerpt_chars = recent_excerpt_chars
    if excerpt_chars is None and env_excerpt_chars:
        excerpt_chars = int(env_excerpt_chars)

    return RedisContextConfig(
        redis_url=redis_url or os.getenv("REDIS_URL"),
        novel_id=novel_id or os.getenv("REDIS_NOVEL_ID") or DEFAULT_NOVEL_ID,
        context_ttl=ttl,
        recent_excerpt_chars=excerpt_chars or 8000,
        enabled=enabled,
    )


class RedisStoryContextStore:
    """Store and retrieve recent story context from Redis."""

    def __init__(self, config: RedisContextConfig):
        self.config = config
        self._client = None
        self.available = False
        self.status_message = "Redis 未启用"

        if not config.enabled:
            return
        if not config.redis_url:
            self.status_message = "未配置 REDIS_URL"
            return
        if redis is None:
            self.status_message = "未安装 redis 依赖"
            return

        try:
            self._client = redis.Redis.from_url(config.redis_url, decode_responses=True)
            self._client.ping()
        except Exception as exc:  # pragma: no cover - depends on local Redis.
            self._client = None
            self.status_message = f"Redis 不可用：{exc}"
            return

        self.available = True
        self.status_message = "Redis 可用"

    def _key(self, suffix: str) -> str:
        return f"novel:{self.config.novel_id}:{suffix}"

    def get_latest_context(self) -> Optional[StoryContext]:
        """Read latest summary and excerpt from Redis."""

        if not self.available or self._client is None:
            return None

        summary = self._client.get(self._key("latest_summary"))
        excerpt = self._client.get(self._key("latest_excerpt"))
        story_id = self._client.get(self._key("latest_story_id"))
        if not summary or not excerpt:
            return None

        return StoryContext(
            story_name=story_id or "redis_latest",
            summary=summary,
            excerpt=excerpt,
            source="redis",
        )

    def save_story_context(
        self,
        *,
        story_text: str,
        summary: str,
        output_file: str | Path,
        outline_file: str | Path,
        target_length: int,
        model: Optional[str],
        story_id: Optional[str] = None,
    ) -> Optional[str]:
        """Persist the newest story context and history metadata."""

        if not self.available or self._client is None:
            return None

        now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        resolved_story_id = story_id or f"{now}_{uuid4().hex[:8]}"
        excerpt = story_text.strip()[-self.config.recent_excerpt_chars :]
        story_key = self._key(f"story:{resolved_story_id}")

        pipe = self._client.pipeline()
        pipe.set(self._key("latest_summary"), summary)
        pipe.set(self._key("latest_excerpt"), excerpt)
        pipe.set(self._key("latest_story_id"), resolved_story_id)
        pipe.lpush(self._key("stories"), resolved_story_id)
        pipe.hset(
            story_key,
            mapping={
                "story_id": resolved_story_id,
                "outline_file": str(outline_file),
                "output_file": str(output_file),
                "summary": summary,
                "excerpt": excerpt,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "target_length": str(target_length),
                "model": model or "",
            },
        )

        if self.config.context_ttl:
            pipe.expire(self._key("latest_summary"), self.config.context_ttl)
            pipe.expire(self._key("latest_excerpt"), self.config.context_ttl)
            pipe.expire(self._key("latest_story_id"), self.config.context_ttl)
            pipe.expire(story_key, self.config.context_ttl)

        pipe.execute()
        return resolved_story_id
