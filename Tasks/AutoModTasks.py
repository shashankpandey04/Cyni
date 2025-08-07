import asyncio
import time
import logging
from discord.ext import tasks, commands

class AutoModTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_caches.start()

    def cog_unload(self):
        self.cleanup_caches.cancel()

    @tasks.loop(minutes=5)
    async def cleanup_caches(self):
        """Clean up old entries from AutoMod caches."""
        try:
            current_time = time.time()
            if hasattr(self.bot, 'get_cog'):
                on_message_cog = self.bot.get_cog('OnMessage')
                if on_message_cog and hasattr(on_message_cog, 'user_message_cache'):
                    cache = on_message_cog.user_message_cache
                    users_to_remove = []
                    
                    for user_id, timestamps in cache.items():
                        cache[user_id] = [ts for ts in timestamps if current_time - ts <= 30]
                        
                        if not cache[user_id]:
                            users_to_remove.append(user_id)
                    
                    for user_id in users_to_remove:
                        del cache[user_id]
                
                on_join_cog = self.bot.get_cog('OnMemberJoin')
                if on_join_cog and hasattr(on_join_cog, 'join_timestamps'):
                    cache = on_join_cog.join_timestamps
                    guilds_to_remove = []
                    
                    for guild_id, timestamps in cache.items():
                        cache[guild_id] = [ts for ts in timestamps if current_time - ts <= 60]
                        
                        if not cache[guild_id]:
                            guilds_to_remove.append(guild_id)
                    
                    for guild_id in guilds_to_remove:
                        del cache[guild_id]
                        
            logging.debug("AutoMod cache cleanup completed")
            
        except Exception as e:
            logging.error(f"Error in AutoMod cache cleanup: {e}")

    @cleanup_caches.before_loop
    async def before_cleanup_caches(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoModTasks(bot))
