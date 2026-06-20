import asyncio

import discord
from discord.ext import commands


class MegaScaleRequestLimiter:
    def __init__(self, max_per_second=50, base_workers=5):
        self.max_per_second = max_per_second
        self.base_workers = base_workers

        self.queue = asyncio.Queue()
        self.worker_tasks = []
        self.running = False
        self.bot = None

    async def start(self, bot):
        self.bot = bot
        self.running = True

        bot.logger.info(f"[MegaLimiter] Starting with {self.base_workers} workers")

        for i in range(self.base_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)

    async def enqueue(self, guild_id: int, func, *args, **kwargs):
        """
        guild_id kept for compatibility.
        Not used internally.
        """
        await self.queue.put((guild_id, func, args, kwargs))

    async def _worker(self, worker_name: str):
        delay = 1 / self.max_per_second

        while self.running:
            try:
                guild_id, func, args, kwargs = await self.queue.get()

                try:
                    await func(*args, **kwargs)

                except discord.HTTPException as e:
                    if self.bot:
                        self.bot.logger.warning(f"[MegaLimiter] Discord API error: {e}")

                except Exception as e:
                    if self.bot:
                        self.bot.logger.error(f"[MegaLimiter] Worker error: {e}")

                self.queue.task_done()

                await asyncio.sleep(delay)

            except asyncio.CancelledError:
                break

            except Exception as e:
                if self.bot:
                    self.bot.logger.error(f"[MegaLimiter] {worker_name}: {e}")

    async def reset_guild_queue(self, guild_id: int):
        """
        Compatibility method.

        Since we use one global queue now,
        resetting a guild queue does nothing.
        """
        if self.bot:
            self.bot.logger.info(
                f"[MegaLimiter] Queue reset requested for guild {guild_id}"
            )

    async def stop(self):
        self.running = False

        for task in self.worker_tasks:
            task.cancel()

        await asyncio.gather(*self.worker_tasks, return_exceptions=True)

    def get_stats(self):
        return {
            "total_queued_items": self.queue.qsize(),
            "active_workers": len([t for t in self.worker_tasks if not t.done()]),
            "max_per_second": self.max_per_second,
        }


class ThrottledLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.limiter = MegaScaleRequestLimiter(max_per_second=50, base_workers=5)

    async def cog_load(self):
        await self.limiter.start(self.bot)

    async def cog_unload(self):
        await self.limiter.stop()

    async def log_embed(self, channel: discord.TextChannel, embed: discord.Embed):
        await self.limiter.enqueue(channel.guild.id, channel.send, embed=embed)

    async def clear_logs_for_guild(
        self, guild_id: int, notify_channel: discord.TextChannel = None
    ):
        await self.limiter.reset_guild_queue(guild_id)

        if notify_channel:
            embed = discord.Embed(
                title="⚠️ Raid Logging Suspended",
                description=(
                    "> Mass spam detected.\n"
                    "> Logging has been reset for this guild "
                    "to prevent flooding."
                ),
                color=discord.Color.red(),
            )

            await self.log_embed(notify_channel, embed)

    @commands.command(name="limiter_stats")
    @commands.is_owner()
    async def limiter_stats(self, ctx):
        stats = self.limiter.get_stats()

        embed = discord.Embed(title="Limiter Stats", color=discord.Color.green())

        for key, value in stats.items():
            embed.add_field(
                name=key.replace("_", " ").title(), value=str(value), inline=True
            )

        await ctx.reply(embed=embed)

    @commands.command(name="reset_guild_queue")
    @commands.is_owner()
    async def reset_guild_queue_cmd(self, ctx, guild_id: int = None):
        target_guild_id = guild_id or ctx.guild.id

        await self.limiter.reset_guild_queue(target_guild_id)

        await ctx.reply(f"✅ Reset queue for guild {target_guild_id}")


async def setup(bot):
    await bot.add_cog(ThrottledLogger(bot))
