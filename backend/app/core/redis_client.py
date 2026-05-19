from redis import Redis
from app.core.config import settings

def get_redis_connection() -> Redis:
    # Important: do NOT use decode_responses=True with RQ.
    return Redis.from_url(settings.REDIS_URL)