# Token Bucket System
import time
import json


def refill(tokens, last_refill, now, max_tokens, rate):
    elapsed = now - last_refill
    tokens = min(max_tokens, tokens + elapsed * rate)
    return tokens, now


# ================= MEMORY ================= #

class MemoryRateLimiter:
    def __init__(self, bot):
        self.bot = bot
        self.buckets = {}

        self.FREE = 20
        self.PREMIUM = 100
        self.REFILL = 2

    async def consume(self, guild_id):
        now = time.time()

        is_premium = await self.bot.cache.is_premium(guild_id)
        max_tokens = self.PREMIUM if is_premium else self.FREE

        bucket = self.buckets.get(guild_id, {
            "tokens": max_tokens,
            "last": now
        })

        tokens, last = refill(
            bucket["tokens"],
            bucket["last"],
            now,
            max_tokens,
            self.REFILL
        )

        if tokens < 1:
            return False, tokens

        tokens -= 1

        self.buckets[guild_id] = {
            "tokens": tokens,
            "last": last
        }

        return True, tokens


# ================= REDIS ================= #

class RedisRateLimiter:
    def __init__(self, bot, redis):
        self.bot = bot
        self.redis = redis

        self.FREE = 20
        self.PREMIUM = 100
        self.REFILL = 2

    async def consume(self, guild_id):
        now = time.time()
        key = f"rate:{guild_id}"

        raw = await self.redis.get(key)

        is_premium = await self.bot.cache.is_premium(guild_id)
        max_tokens = self.PREMIUM if is_premium else self.FREE

        if raw:
            bucket = json.loads(raw)
        else:
            bucket = {
                "tokens": max_tokens,
                "last": now
            }

        tokens, last = refill(
            bucket["tokens"],
            bucket["last"],
            now,
            max_tokens,
            self.REFILL
        )

        if tokens < 1:
            return False, tokens

        tokens -= 1

        await self.redis.set(
            key,
            json.dumps({
                "tokens": tokens,
                "last": last
            }),
            ex=60
        )

        return True, tokens