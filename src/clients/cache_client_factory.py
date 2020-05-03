import aioredis as aioredis
import redis

import src.orderbookconstants as obc


class CacheClientFactory:
    def __init__(self):
        pass

    def redis_client(self, host=obc.DEFAULT_REDIS_SYNC_HOST):
        return redis.Redis(host)

    async def async_redis_client(self, host=obc.DEFAULT_REDIS_ASYNC_HOST):
        return await aioredis.create_redis(host)
