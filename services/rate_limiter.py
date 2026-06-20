# services/rate_limiter.py

import json
import time


def refill(
    tokens: float,
    last_refill: float,
    now: float,
    capacity: int,
    refill_rate: float,
):
    elapsed = now - last_refill

    tokens = min(capacity, tokens + elapsed * refill_rate)

    return tokens, now


class RateLimiter:
    FREE_CAPACITY = 50
    PREMIUM_CAPACITY = 250

    REFILL_RATE = 2.0

    BUCKET_TTL = 300

    def __init__(self, bot, redis):
        self.bot = bot
        self.redis = redis

    async def consume(self, guild_id: int) -> tuple[bool, float]:

        now = time.time()

        key = f"rate:{guild_id}"

        premium = await self.bot.cache.is_premium(guild_id)

        capacity = self.PREMIUM_CAPACITY if premium else self.FREE_CAPACITY

        raw = await self.redis.get(key)

        if raw:
            bucket = json.loads(raw)

        else:
            bucket = {"tokens": capacity, "last": now}

        tokens, last = refill(
            bucket["tokens"], bucket["last"], now, capacity, self.REFILL_RATE
        )

        if tokens < 1:
            retry_after = (1 - tokens) / self.REFILL_RATE

            return False, retry_after

        tokens -= 1

        await self.redis.set(
            key, json.dumps({"tokens": tokens, "last": last}), ex=self.BUCKET_TTL
        )

        return True, 0

    async def reset(self, guild_id: int):

        await self.redis.delete(f"rate:{guild_id}")
