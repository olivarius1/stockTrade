import redis
from app.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_cache():
    return redis_client

def cache_get(key: str):
    return redis_client.get(key)

def cache_set(key: str, value, expire_seconds: int = 3600):
    redis_client.set(key, value, ex=expire_seconds)

def cache_delete(key: str):
    redis_client.delete(key)
