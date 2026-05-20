import redis

# use same post (6380) as celery but use database 1 for caching
redis_client = redis.Redis(
    host = "127.0.0.1",
    port = 6380,
    db = 1,
    decode_responses=True
)