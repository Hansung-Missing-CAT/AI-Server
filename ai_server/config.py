from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from redis import Redis
from supabase import Client, create_client

load_dotenv()


class Settings:
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    upstash_redis_url: str | None = os.getenv("UPSTASH_REDIS_URL")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    cat_api_key: str | None = os.getenv("CAT_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    if not settings.upstash_redis_url:
        raise RuntimeError("UPSTASH_REDIS_URL must be set")
    return Redis.from_url(settings.upstash_redis_url, decode_responses=True)
