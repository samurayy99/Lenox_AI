# cache_manager.py

import redis
import json
import os

# Configure Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

CACHE_EXPIRATION = 3600  # Cache expiration time in seconds (1 hour)

def set_cache(key, data):
    redis_client.setex(key, CACHE_EXPIRATION, json.dumps(data))

def get_cache(key):
    data = redis_client.get(key)
    if data is not None and isinstance(data, (str, bytes, bytearray)):  # Ensure data is of correct type
        return json.loads(data)
    return None

def invalidate_cache(key):
    redis_client.delete(key)