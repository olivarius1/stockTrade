"""缓存管理模块，提供 Redis 缓存和内存缓存降级。

为什么保留 Redis：Celery Beat/Worker 需要 Redis 作为消息队列，
计算结果缓存也复用同一 Redis 实例。

缓存策略：仅缓存计算量大的衍生数据（MA、波动率），
实时行情和DB数据不缓存（保证数据一致性）。
"""
import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback cache used when Redis is unavailable
_memory_cache: dict = {}

try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    _redis_available = True
except Exception as e:
    logger.warning(f"Redis unavailable, falling back to in-memory cache: {e}")
    redis_client = None
    _redis_available = False


def get_cache():
    """获取 Redis 客户端实例。"""
    return redis_client


def cache_get(key: str):
    """读取缓存值。Redis 不可用时降级到内存缓存。"""
    if _redis_available:
        try:
            return redis_client.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed, using memory: {e}")
    return _memory_cache.get(key)


def cache_set(key: str, value, expire_seconds: int = 3600):
    """写入缓存值，默认1小时过期。"""
    if _redis_available:
        try:
            redis_client.set(key, value, ex=expire_seconds)
            return
        except Exception as e:
            logger.warning(f"Redis set failed, using memory: {e}")
    _memory_cache[key] = value


def cache_delete(key: str):
    """删除单个缓存键。"""
    if _redis_available:
        try:
            redis_client.delete(key)
            return
        except Exception as e:
            logger.warning(f"Redis delete failed, using memory: {e}")
    _memory_cache.pop(key, None)


def cache_clear_pattern(pattern: str):
    """清除匹配模式的所有缓存键。

    用于K线数据更新后清除衍生计算缓存（MA、波动率等）。
    """
    if _redis_available:
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
            return
        except Exception as e:
            logger.warning(f"Redis clear pattern failed: {e}")
    # 内存缓存不支持模式匹配，逐个检查
    prefix = pattern.replace("*", "")
    keys_to_delete = [k for k in _memory_cache if prefix in k]
    for k in keys_to_delete:
        _memory_cache.pop(k, None)
