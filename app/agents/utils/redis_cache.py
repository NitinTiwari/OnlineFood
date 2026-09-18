import json
import redis
import settings

class RedisCache:
    @staticmethod
    def _client():
        return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

    @classmethod
    def get(cls, prefix, payload):
        key = f"{prefix}:{hash(str(payload))}"
        client = cls._client()
        data = client.get(key)
        if data:
            return json.loads(data)
        return None

    @classmethod
    def set(cls, prefix, payload, value, ttl=None):
        key = f"{prefix}:{hash(str(payload))}"
        client = cls._client()
        client.setex(key, ttl or settings.REDIS_TTL_SECONDS, json.dumps(value))
