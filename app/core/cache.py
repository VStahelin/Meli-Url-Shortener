import redis
from app.settings import REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
