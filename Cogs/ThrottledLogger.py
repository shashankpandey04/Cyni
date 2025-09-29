import asyncio
import time
import discord
from discord.ext import commands
import weakref
import random
from collections import deque
import threading

class MegaScaleRequestLimiter:
    def __init__(self, max_per_second=50, base_workers=5):
        # Core queues
        self.guild_queues = {}  # guild_id -> asyncio.Queue
        self.guild_queues_lock = asyncio.Lock()  # Protect queue dictionary
        self.priority_queue = asyncio.Queue(maxsize=max_per_second * 3)
        
        # Worker management
        self.base_workers = base_workers
        self.worker_tasks = []
        self.running = False
        
        # Fixed rate limiting
        self.max_per_second = max_per_second
        self.rate_limit_semaphore = asyncio.Semaphore(max_per_second)
        self.rate_reset_task = None
        self.last_rate_reset = time.time()
        
        # Thread-safe guild tracking
        self.active_guilds = deque()
        self.active_guilds_lock = asyncio.Lock()
        self.guild_last_activity = {}
        
        # Auto-scaling
        self.load_monitor_task = None
        self.last_scale_check = time.time()
        self.scale_check_interval = 30
        
        # Cleanup
        self.cleanup_task = None
        self.last_cleanup = time.time()
        self.cleanup_interval = 600

    async def start(self, bot):
        self.bot = weakref.ref(bot)
        self.running = True
        
        guild_count = len(bot.guilds)
        optimal_workers = min(20, max(self.base_workers, guild_count // 500))
        
        bot.logger.info(f"[MegaLimiter] Starting with {optimal_workers} workers for {guild_count} guilds")
        
        # Start rate limit reset with fixed logic
        self.rate_reset_task = asyncio.create_task(self._rate_reset_loop())
        
        # Start workers
        for i in range(optimal_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker)
        
        # Start monitoring tasks
        self.load_monitor_task = asyncio.create_task(self._load_monitor())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def get_queue(self, guild_id: int):
        """Thread-safe queue retrieval"""
        async with self.guild_queues_lock:
            if guild_id not in self.guild_queues:
                self.guild_queues[guild_id] = asyncio.Queue(maxsize=100)
            return self.guild_queues[guild_id]

    async def enqueue(self, guild_id: int, func, *args, **kwargs):
        """Enqueue with proper synchronization"""
        queue = await self.get_queue(guild_id)
        
        try:
            queue.put_nowait((func, args, kwargs))
            
            # Thread-safe activity tracking
            self.guild_last_activity[guild_id] = time.time()
            
            # Thread-safe active guild tracking
            async with self.active_guilds_lock:
                # Only add if not recently added (avoid duplicates)
                recent_guilds = list(self.active_guilds)[-50:] if len(self.active_guilds) > 50 else list(self.active_guilds)
                if guild_id not in recent_guilds:
                    self.active_guilds.append(guild_id)
            
        except asyncio.QueueFull:
            try:
                await asyncio.wait_for(
                    self.priority_queue.put((func, args, kwargs, guild_id)), 
                    timeout=0.1
                )
                if self.bot():
                    self.bot().logger.warning(f"[MegaLimiter] Guild {guild_id} queue full, using priority overflow")
            except (asyncio.QueueFull, asyncio.TimeoutError):
                if self.bot():
                    self.bot().logger.warning(f"[MegaLimiter] Dropping request for guild {guild_id} - system overloaded")

    async def _rate_reset_loop(self):
        """Fixed rate limit semaphore reset"""
        while self.running:
            try:
                await asyncio.sleep(1.0)
                
                # Create new semaphore instead of manipulating internal state
                old_semaphore = self.rate_limit_semaphore
                self.rate_limit_semaphore = asyncio.Semaphore(self.max_per_second)
                self.last_rate_reset = time.time()
                
                # Let old semaphore be garbage collected
                del old_semaphore
                
            except Exception as e:
                if self.bot():
                    self.bot().logger.error(f"[MegaLimiter] Rate reset error: {e}")
                await asyncio.sleep(1.0)

    async def _worker(self, worker_name: str):
        """Improved worker with better error handling"""
        consecutive_empty = 0
        local_guild_rotation = deque(maxlen=50)
        
        while self.running:
            try:
                processed_item = False
                
                # 1. Priority queue first
                if not self.priority_queue.empty():
                    try:
                        func, args, kwargs, guild_id = self.priority_queue.get_nowait()
                        await self._execute_with_rate_limit(func, args, kwargs, guild_id)
                        self.priority_queue.task_done()
                        processed_item = True
                    except asyncio.QueueEmpty:
                        pass
                
                # 2. Guild queues
                if not processed_item:
                    guild_id = await self._get_next_active_guild(local_guild_rotation)
                    
                    if guild_id:
                        # Get queue safely
                        async with self.guild_queues_lock:
                            queue = self.guild_queues.get(guild_id)
                        
                        if queue:
                            try:
                                func, args, kwargs = queue.get_nowait()
                                await self._execute_with_rate_limit(func, args, kwargs, guild_id)
                                queue.task_done()
                                processed_item = True
                                consecutive_empty = 0
                                
                                # Keep in local rotation
                                if guild_id not in local_guild_rotation:
                                    local_guild_rotation.append(guild_id)
                                
                            except asyncio.QueueEmpty:
                                pass
                
                # 3. Adaptive sleep
                if not processed_item:
                    consecutive_empty += 1
                    sleep_time = min(0.1, consecutive_empty * 0.01)
                    await asyncio.sleep(sleep_time)
                else:
                    await asyncio.sleep(0.001)
                
            except Exception as e:
                if self.bot():
                    self.bot().logger.error(f"[MegaLimiter] Worker {worker_name} error: {e}")
                await asyncio.sleep(0.1)
                # Worker continues - don't let one error kill the worker

    async def _get_next_active_guild(self, local_cache: deque):
        """Thread-safe guild selection"""
        # Try local cache first
        if local_cache:
            guild_id = local_cache.popleft()
            async with self.guild_queues_lock:
                queue = self.guild_queues.get(guild_id)
                if queue and not queue.empty():
                    local_cache.append(guild_id)
                    return guild_id
        
        # Try active guilds rotation
        async with self.active_guilds_lock:
            for _ in range(min(10, len(self.active_guilds))):
                if not self.active_guilds:
                    break
                    
                guild_id = self.active_guilds.popleft()
                
                # Check if queue exists and has items
                async with self.guild_queues_lock:
                    queue = self.guild_queues.get(guild_id)
                    if queue and not queue.empty():
                        self.active_guilds.append(guild_id)  # Put back at end
                        return guild_id
        
        return None

    async def _execute_with_rate_limit(self, func, args, kwargs, guild_id):
        """Execute with proper error handling"""
        try:
            await self.rate_limit_semaphore.acquire()
            await func(*args, **kwargs)
        except discord.HTTPException as e:
            if self.bot():
                self.bot().logger.warning(f"[MegaLimiter] Discord API error for guild {guild_id}: {e}")
        except Exception as e:
            if self.bot():
                self.bot().logger.error(f"[MegaLimiter] Execution error for guild {guild_id}: {e}")

    async def _load_monitor(self):
        """Improved load monitoring"""
        while self.running:
            await asyncio.sleep(self.scale_check_interval)
            
            try:
                # Calculate metrics safely
                async with self.guild_queues_lock:
                    total_queued = sum(q.qsize() for q in self.guild_queues.values())
                    active_queues = sum(1 for q in self.guild_queues.values() if not q.empty())
                
                priority_queued = self.priority_queue.qsize()
                current_workers = len([t for t in self.worker_tasks if not t.done()])
                
                # Remove dead workers
                self.worker_tasks = [t for t in self.worker_tasks if not t.done()]
                
                # Scale up
                if (total_queued > current_workers * 50 or priority_queued > 10) and current_workers < 20:
                    new_worker = asyncio.create_task(self._worker(f"auto-worker-{len(self.worker_tasks)}"))
                    self.worker_tasks.append(new_worker)
                    if self.bot():
                        self.bot().logger.info(f"[MegaLimiter] Scaled UP to {len(self.worker_tasks)} workers")
                
                # Scale down
                elif total_queued < current_workers * 10 and current_workers > self.base_workers:
                    if self.worker_tasks:
                        worker_to_remove = self.worker_tasks.pop()
                        worker_to_remove.cancel()
                        if self.bot():
                            self.bot().logger.info(f"[MegaLimiter] Scaled DOWN to {len(self.worker_tasks)} workers")
                
            except Exception as e:
                if self.bot():
                    self.bot().logger.error(f"[MegaLimiter] Load monitor error: {e}")

    async def _cleanup_loop(self):
        """Thread-safe cleanup"""
        while self.running:
            await asyncio.sleep(self.cleanup_interval)
            
            try:
                now = time.time()
                stale_guilds = []
                
                # Find stale guilds
                async with self.guild_queues_lock:
                    for guild_id, last_activity in list(self.guild_last_activity.items()):
                        if (now - last_activity > 3600 and 
                            guild_id in self.guild_queues and 
                            self.guild_queues[guild_id].empty()):
                            stale_guilds.append(guild_id)
                
                # Clean up stale guilds
                if stale_guilds:
                    async with self.guild_queues_lock:
                        for guild_id in stale_guilds:
                            if guild_id in self.guild_queues:
                                del self.guild_queues[guild_id]
                            if guild_id in self.guild_last_activity:
                                del self.guild_last_activity[guild_id]
                    
                    # Clean from active rotation
                    async with self.active_guilds_lock:
                        # Convert to list, filter, convert back
                        active_list = [gid for gid in self.active_guilds if gid not in stale_guilds]
                        self.active_guilds = deque(active_list)
                    
                    if self.bot():
                        self.bot().logger.info(f"[MegaLimiter] Cleaned up {len(stale_guilds)} stale guilds")
                
                # Trim rotation size
                async with self.active_guilds_lock:
                    while len(self.active_guilds) > 1000:
                        self.active_guilds.popleft()
                
            except Exception as e:
                if self.bot():
                    self.bot().logger.error(f"[MegaLimiter] Cleanup error: {e}")

    async def reset_guild_queue(self, guild_id: int):
        """Thread-safe queue reset"""
        async with self.guild_queues_lock:
            old_size = 0
            if guild_id in self.guild_queues:
                old_size = self.guild_queues[guild_id].qsize()
                # Create completely new queue
                self.guild_queues[guild_id] = asyncio.Queue(maxsize=100)
            else:
                # Ensure queue exists
                self.guild_queues[guild_id] = asyncio.Queue(maxsize=100)
            
            self.guild_last_activity[guild_id] = time.time()
        
        # Add back to active rotation
        async with self.active_guilds_lock:
            if guild_id not in self.active_guilds:
                self.active_guilds.append(guild_id)
        
        if self.bot():
            self.bot().logger.info(f"[MegaLimiter] Reset guild {guild_id} queue (was {old_size} items)")

    async def stop(self):
        """Graceful shutdown"""
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
        """Thread-safe stats"""
        try:
            # Use current state without locks for stats (may be slightly inaccurate but won't block)
            total_queued = sum(q.qsize() for q in self.guild_queues.values() if not q.empty())
            active_queues = sum(1 for q in self.guild_queues.values() if not q.empty())
            active_workers = len([t for t in self.worker_tasks if not t.done()])
            
            return {
                'total_guilds': len(self.guild_queues),
                'active_guild_queues': active_queues,
                'total_queued_items': total_queued,
                'priority_queue_size': self.priority_queue.qsize(),
                'active_workers': active_workers,
                'rate_limit_permits': getattr(self.rate_limit_semaphore, '_value', 0),
                'active_rotation_size': len(self.active_guilds)
            }
        except Exception as e:
            return {'error': str(e)}


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
        """Fixed clear logs method"""
        await self.limiter.reset_guild_queue(guild_id)
        
        if notify_channel:
            embed = discord.Embed(
                title="⚠️ Raid Logging Suspended",
                description="> Mass spam detected.\n> Logging has been reset for this guild to prevent flooding.",
                color=discord.Color.red()
            )
            # Use the reset queue immediately
            await self.limiter.enqueue(guild_id, notify_channel.send, embed=embed)

    @commands.command(name='limiter_stats')
    @commands.is_owner()
    async def limiter_stats(self, ctx):
        stats = self.limiter.get_stats()
        embed = discord.Embed(title="MegaScale Request Limiter Stats", color=discord.Color.green())
        
        for key, value in stats.items():
            if key != 'error':
                embed.add_field(
                    name=key.replace('_', ' ').title(), 
                    value=f"{value:,}" if isinstance(value, int) else str(value), 
                    inline=True
                )
        
        await ctx.reply(embed=embed)

    @commands.command(name='reset_guild_queue')
    @commands.is_owner()
    async def reset_guild_queue_cmd(self, ctx, guild_id: int = None):
        """Manual guild queue reset command"""
        target_guild_id = guild_id or ctx.guild.id
        await self.limiter.reset_guild_queue(target_guild_id)
        await ctx.reply(f"✅ Reset queue for guild {target_guild_id}")

async def setup(bot):
    await bot.add_cog(ThrottledLogger(bot))