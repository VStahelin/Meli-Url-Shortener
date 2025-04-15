import redis
import os

HOST = os.getenv("REDIS_HOST", "redis")
PORT = os.getenv("REDIS_PORT", "6379")

REDIS_URL = f"redis://{HOST}:{PORT}/0"

DEFAULT_TIMEOUT = 60 * 60 * 24  # 1 day

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
