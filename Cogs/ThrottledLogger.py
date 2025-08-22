import asyncio
import time
import discord
from discord.ext import commands
import weakref
import random
from collections import deque

class MegaScaleRequestLimiter:
    def __init__(self, max_per_second=50, base_workers=5):
        # Core queues
        self.guild_queues = {}  # guild_id -> asyncio.Queue
        self.priority_queue = asyncio.Queue(maxsize=max_per_second * 3)  # High priority items
        
        # Worker management
        self.base_workers = base_workers
        self.worker_tasks = []
        self.running = False
        
        # Rate limiting
        self.max_per_second = max_per_second
        self.rate_limit_semaphore = asyncio.Semaphore(max_per_second)
        self.rate_reset_task = None
        
        # Efficient guild tracking
        self.active_guilds = deque()  # Rotating queue of active guild IDs
        self.guild_last_activity = {}  # guild_id -> timestamp
        
        # Auto-scaling
        self.load_monitor_task = None
        self.last_scale_check = time.time()
        self.scale_check_interval = 30  # seconds
        
        # Cleanup
        self.cleanup_task = None
        self.last_cleanup = time.time()
        self.cleanup_interval = 600  # 10 minutes for large scale

    async def start(self, bot):
        self.bot = weakref.ref(bot)
        self.running = True
        
        # Calculate optimal worker count based on guild count
        guild_count = len(bot.guilds)
        optimal_workers = min(20, max(self.base_workers, guild_count // 500))
        
        bot.logger.info(f"[MegaLimiter] Starting with {optimal_workers} workers for {guild_count} guilds")
        
        # Start rate limit semaphore reset
        self.rate_reset_task = asyncio.create_task(self._rate_reset_loop())
        
        # Start workers
        for i in range(optimal_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker)
        
        # Start monitoring tasks
        self.load_monitor_task = asyncio.create_task(self._load_monitor())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    def get_queue(self, guild_id: int):
        if guild_id not in self.guild_queues:
            # Smaller queue size for massive scale
            self.guild_queues[guild_id] = asyncio.Queue(maxsize=100)
        return self.guild_queues[guild_id]

    async def enqueue(self, guild_id: int, func, *args, **kwargs):
        """Enqueue with smart overflow handling."""
        queue = self.get_queue(guild_id)
        
        try:
            # Try to put in guild queue first
            queue.put_nowait((func, args, kwargs))
            
            # Mark guild as active
            self.guild_last_activity[guild_id] = time.time()
            
            # Add to active rotation if not already there
            if guild_id not in list(self.active_guilds)[-100:]:  # Check last 100 to avoid full scan
                self.active_guilds.append(guild_id)
            
        except asyncio.QueueFull:
            # If guild queue is full, try priority queue for emergency overflow
            try:
                await asyncio.wait_for(
                    self.priority_queue.put((func, args, kwargs, guild_id)), 
                    timeout=0.1
                )
                self.bot.logger.info(f"[MegaLimiter] Guild {guild_id} queue full, using priority overflow")
            except (asyncio.QueueFull, asyncio.TimeoutError):
                self.bot.logger.info(f"[MegaLimiter] Dropping request for guild {guild_id} - system overloaded")

    async def _rate_reset_loop(self):
        """Reset rate limit semaphore every second."""
        while self.running:
            await asyncio.sleep(1.0)
            
            # Release all permits (reset to max_per_second)
            current_value = self.rate_limit_semaphore._value
            permits_to_add = self.max_per_second - current_value
            
            for _ in range(max(0, permits_to_add)):
                try:
                    self.rate_limit_semaphore.release()
                except ValueError:
                    break  # Already at maximum

    async def _worker(self, worker_name: str):
        """High-performance worker with smart guild rotation."""
        consecutive_empty = 0
        local_guild_rotation = deque(maxlen=50)  # Local cache of recently active guilds
        
        while self.running:
            try:
                processed_item = False
                
                # 1. Check priority queue first (overflow handling)
                if not self.priority_queue.empty():
                    try:
                        func, args, kwargs, guild_id = self.priority_queue.get_nowait()
                        await self._execute_with_rate_limit(func, args, kwargs, guild_id)
                        self.priority_queue.task_done()
                        processed_item = True
                    except asyncio.QueueEmpty:
                        pass
                
                # 2. Process from guild queues
                if not processed_item:
                    guild_id = self._get_next_active_guild(local_guild_rotation)
                    
                    if guild_id and guild_id in self.guild_queues:
                        queue = self.guild_queues[guild_id]
                        
                        try:
                            func, args, kwargs = queue.get_nowait()
                            await self._execute_with_rate_limit(func, args, kwargs, guild_id)
                            queue.task_done()
                            processed_item = True
                            consecutive_empty = 0
                            
                            # Keep active guild in local rotation
                            if guild_id not in local_guild_rotation:
                                local_guild_rotation.append(guild_id)
                            
                        except asyncio.QueueEmpty:
                            pass
                
                # 3. Adaptive sleep based on load
                if not processed_item:
                    consecutive_empty += 1
                    sleep_time = min(0.1, consecutive_empty * 0.01)  # Backoff when idle
                    await asyncio.sleep(sleep_time)
                else:
                    # Quick yield when busy
                    await asyncio.sleep(0.001)
                
            except Exception as e:
                self.bot.logger.error(f"[MegaLimiter] Worker {worker_name} error: {e}")
                await asyncio.sleep(0.1)

    def _get_next_active_guild(self, local_cache: deque):
        """Efficiently get next active guild without expensive operations."""
        
        # Try local cache first (hot guilds)
        if local_cache:
            guild_id = local_cache.popleft()
            if guild_id in self.guild_queues and not self.guild_queues[guild_id].empty():
                local_cache.append(guild_id)  # Put back at end
                return guild_id
        
        # Try a few from the rotating active list
        for _ in range(min(10, len(self.active_guilds))):
            if not self.active_guilds:
                break
                
            guild_id = self.active_guilds.popleft()
            
            # Check if still active (has queue with items)
            if guild_id in self.guild_queues and not self.guild_queues[guild_id].empty():
                self.active_guilds.append(guild_id)  # Put back at end
                return guild_id
        
        return None

    async def _execute_with_rate_limit(self, func, args, kwargs, guild_id):
        """Execute function with rate limiting."""
        await self.rate_limit_semaphore.acquire()
        
        try:
            await func(*args, **kwargs)
        except Exception as e:
            self.bot.logger.info(f"[MegaLimiter] Execution error for guild {guild_id}: {e}")

    async def _load_monitor(self):
        """Monitor load and auto-scale workers."""
        while self.running:
            await asyncio.sleep(self.scale_check_interval)
            
            try:
                # Calculate load metrics
                total_queued = sum(q.qsize() for q in self.guild_queues.values())
                active_queues = sum(1 for q in self.guild_queues.values() if not q.empty())
                priority_queued = self.priority_queue.qsize()
                
                current_workers = len(self.worker_tasks)
                
                # Auto-scale up if overloaded
                if (total_queued > current_workers * 50 or priority_queued > 10) and current_workers < 20:
                    new_worker = asyncio.create_task(self._worker(f"auto-worker-{current_workers}"))
                    self.worker_tasks.append(new_worker)
                    self.bot.logger.info(f"[MegaLimiter] Scaled UP to {len(self.worker_tasks)} workers (load: {total_queued})")
                
                # Auto-scale down if underutilized (but keep minimum)
                elif total_queued < current_workers * 10 and current_workers > self.base_workers:
                    worker_to_remove = self.worker_tasks.pop()
                    worker_to_remove.cancel()
                    self.bot.logger.info(f"[MegaLimiter] Scaled DOWN to {len(self.worker_tasks)} workers (load: {total_queued})")
                
            except Exception as e:
                self.bot.logger.info(f"[MegaLimiter] Load monitor error: {e}")

    async def _cleanup_loop(self):
        """Aggressive cleanup for massive scale."""
        while self.running:
            await asyncio.sleep(self.cleanup_interval)
            
            try:
                now = time.time()
                stale_guilds = []
                
                # Find stale guilds (inactive for 1 hour)
                for guild_id, last_activity in list(self.guild_last_activity.items()):
                    if now - last_activity > 3600 and guild_id in self.guild_queues:
                        if self.guild_queues[guild_id].empty():
                            stale_guilds.append(guild_id)
                
                # Clean up stale guilds
                for guild_id in stale_guilds:
                    del self.guild_queues[guild_id]
                    del self.guild_last_activity[guild_id]
                    
                    # Remove from active rotation
                    try:
                        while guild_id in self.active_guilds:
                            self.active_guilds.remove(guild_id)
                    except ValueError:
                        pass
                
                if stale_guilds:
                    self.bot.logger.info(f"[MegaLimiter] Cleaned up {len(stale_guilds)} stale guilds")
                
                # Trim active guilds rotation if it gets too long
                while len(self.active_guilds) > 1000:
                    self.active_guilds.popleft()
                
            except Exception as e:
                self.bot.logger.info(f"[MegaLimiter] Cleanup error: {e}")

    def reset_guild_queue(self, guild_id: int):
        """Optimized queue reset."""
        if guild_id in self.guild_queues:
            old_size = self.guild_queues[guild_id].qsize()
            self.guild_queues[guild_id] = asyncio.Queue(maxsize=100)
            self.guild_last_activity[guild_id] = time.time()
            self.bot.logger.info(f"[MegaLimiter] Reset guild {guild_id} queue (was {old_size} items)")

    async def stop(self):
        """Graceful shutdown."""
        print("[MegaLimiter] Shutting down...")
        self.running = False
        
        # Cancel all tasks
        tasks_to_cancel = []
        if self.rate_reset_task:
            tasks_to_cancel.append(self.rate_reset_task)
        if self.load_monitor_task:
            tasks_to_cancel.append(self.load_monitor_task)
        if self.cleanup_task:
            tasks_to_cancel.append(self.cleanup_task)
        tasks_to_cancel.extend(self.worker_tasks)
        
        for task in tasks_to_cancel:
            task.cancel()
        
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
        
        print("[MegaLimiter] Shutdown complete")
    
    def get_stats(self):
        """Comprehensive stats for massive scale."""
        total_queued = sum(q.qsize() for q in self.guild_queues.values())
        active_queues = sum(1 for q in self.guild_queues.values() if not q.empty())
        
        return {
            'total_guilds': len(self.guild_queues),
            'active_guild_queues': active_queues,
            'total_queued_items': total_queued,
            'priority_queue_size': self.priority_queue.qsize(),
            'active_workers': len(self.worker_tasks),
            'rate_limit_permits': self.rate_limit_semaphore._value,
            'active_rotation_size': len(self.active_guilds)
        }


class ThrottledLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.limiter = MegaScaleRequestLimiter(base_workers=max(5, len(bot.guilds) // 1000))

    async def cog_load(self):
        await self.limiter.start(self.bot)

    async def cog_unload(self):
        await self.limiter.stop()

    async def log_embed(self, channel: discord.TextChannel, embed: discord.Embed):
        guild_id = channel.guild.id
        await self.limiter.enqueue(guild_id, channel.send, embed=embed)

    async def clear_logs_for_guild(self, guild_id: int, notify_channel: discord.TextChannel = None):
        self.limiter.reset_guild_queue(guild_id)
        if notify_channel:
            embed = discord.Embed(
                title="⚠️ Raid Logging Suspended",
                description="> Mass spam detected.\n> Logging has been reset for this guild to prevent flooding.",
                color=discord.Color.red()
            )
            await self.limiter.enqueue(guild_id, notify_channel.send, embed=embed)

    @commands.command(name='limiter_stats')
    @commands.is_owner()
    async def limiter_stats(self, ctx):
        stats = self.limiter.get_stats()
        embed = discord.Embed(title="MegaScale Request Limiter Stats", color=discord.Color.green())
        for key, value in stats.items():
            embed.add_field(name=key.replace('_', ' ').title(), value=f"{value:,}", inline=True)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ThrottledLogger(bot))