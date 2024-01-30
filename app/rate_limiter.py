from datetime import datetime
from typing import Optional

import redis.exceptions
from flask_limiter import RateLimitExceeded
from limits.storage import RedisStorage

from app.log import log

lock_redis: Optional[RedisStorage] = None


def set_redis_concurrent_lock(redis: RedisStorage):
    global lock_redis
    lock_redis = redis


def check_bucket_limit(
    lock_name: Optional[str] = None,
    max_hits: int = 5,
    bucket_seconds: int = 3600,
):
    # Calculate current bucket time
    bucket_id = int(datetime.utcnow().timestamp()) % bucket_seconds
    bucket_lock_name = f"bl:{lock_name}:{bucket_id}"
    try:
        value = lock_redis.incr(bucket_lock_name, bucket_seconds)
        if value > max_hits:
            return RateLimitExceeded(lock_name)
    except redis.exceptions.RedisError:
        log.e("Cannot connect to redis")
