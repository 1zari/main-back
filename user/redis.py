import redis
from django.conf import settings

REDIS_HOST = settings.REDIS_HOST or "localhost"
REDIS_PORT = (
    int(settings.REDIS_PORT) if settings.REDIS_PORT is not None else 6379
)
REDIS_DB = int(settings.REDIS_DB) if settings.REDIS_DB is not None else 0
REDIS_PASSWORD = settings.REDIS_PASSWORD  # None이면 None으로 넘김

r = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
)
