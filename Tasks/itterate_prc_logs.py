import discord
from discord.ext import tasks
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR
import utils.prc_api as prc_api
from utils.prc_api import ServerKillLogs, ServerJoinLogs, ResponseFailed

class PRCLogsProcessor:
    """Automated PRC logs processor that sends kill logs and join/leave logs to configured channels."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        # Cache to track last processed log timestamps per guild
        self.last_kill_log_timestamp = {}
        self.last_join_log_timestamp = {}
        # Cache for Roblox usernames
        self.username_cache = {}
        # Cache for guilds and channels (refreshed every 5 minutes)
        self.guilds_cache = []
        self.channels_cache = {}
        self.last_cache_update = 0
        self.cache_duration = 300  # 5 minutes in seconds

    def start_task(self):
        """Start the PRC logs processing task."""
        if not self.process_prc_logs.is_running():
            self.process_prc_logs.start()
            self.logger.info("PRC logs processing task started")

    def stop_task(self):
        """Stop the PRC logs processing task."""
        if self.process_prc_logs.is_running():
            self.process_prc_logs.stop()
            self.logger.info("PRC logs processing task stopped")

    def clear_caches(self):
        """Clear all caches to free memory."""
        self.username_cache.clear()
        self.guilds_cache.clear()
        self.channels_cache.clear()
        self.last_cache_update = 0
        self.logger.info("All caches cleared")

    async def get_cached_username(self, user_id: int) -> str:
        """Get username with caching to reduce API calls."""
        if user_id not in self.username_cache:
            try:
                username = await self.bot.roblox._get_username_by_id(user_id)
                self.username_cache[user_id] = username
            except Exception:
                self.username_cache[user_id] = f"User {user_id}"
        return self.username_cache[user_id]

    async def get_guilds_with_erlc_config(self) -> List[Dict]:
        """Get all guilds that have ERLC configuration with logging channels (with caching)."""
        current_time = time.time()
        
        # Check if cache is still valid (5 minutes)
        if current_time - self.last_cache_update < self.cache_duration and self.guilds_cache:
            return self.guilds_cache
        
        try:
            # Find all guilds that have ERLC logging channels configured
            guilds = await self.bot.settings.find({
                "$or": [
                    {"erlc.kill_logs_channel": {"$exists": True, "$ne": None}},
                    {"erlc.join_logs_channel": {"$exists": True, "$ne": None}}
                ]
            })
            
            # Update cache
            self.guilds_cache = guilds
            self.last_cache_update = current_time
            self.logger.info(f"Updated guilds cache with {len(guilds)} guilds")
            
            return guilds
        except Exception as e:
            self.logger.error(f"Error fetching guilds with ERLC config: {e}")
            # Return cached data if available, otherwise empty list
            return self.guilds_cache if self.guilds_cache else []

    async def get_cached_channel(self, channel_id: int):
        """Get channel with caching to reduce bot.get_channel calls."""
        if channel_id not in self.channels_cache:
            channel = self.bot.get_channel(channel_id)
            if channel:
                self.channels_cache[channel_id] = channel
            else:
                # Cache None to avoid repeated lookups for invalid channels
                self.channels_cache[channel_id] = None
        return self.channels_cache[channel_id]

    async def process_kill_logs(self, guild_id: int, kill_logs_channel_id: int):
        """Process and send kill logs for a guild."""
        try:
            # Fetch kill logs from PRC API
            kill_logs: List[ServerKillLogs] = await self.bot.prc_api._fetch_server_killlogs(guild_id)
            
            if not kill_logs:
                return

            # Get last processed timestamp for this guild
            last_timestamp = self.last_kill_log_timestamp.get(guild_id, 0)
            new_logs = []

            # Filter for new logs only
            for log in kill_logs:
                if log.timestamp and log.timestamp > last_timestamp:
                    new_logs.append(log)

            if not new_logs:
                return

            # Sort by timestamp (oldest first for chronological posting)
            new_logs.sort(key=lambda x: x.timestamp or 0)

            # Get the channel (with caching)
            channel = await self.get_cached_channel(kill_logs_channel_id)
            if not channel:
                self.logger.warning(f"Kill logs channel {kill_logs_channel_id} not found for guild {guild_id}")
                return

            # Group logs into batches of 10 to send together
            batch_size = 10
            for i in range(0, len(new_logs), batch_size):
                batch = new_logs[i:i + batch_size]
                embeds = []

                for log in batch:
                    try:
                        # Parse killer info (format: "PlayerName:Id")
                        killer_parts = log.Killer.split(":")
                        if len(killer_parts) >= 2:
                            killer_name = killer_parts[0]
                            killer_id = killer_parts[1]
                            killer_link = f"[{killer_name}](https://roblox.com/users/{killer_id}/profile)"
                        else:
                            killer_name = log.Killer
                            killer_link = killer_name

                        # Parse killed info (format: "PlayerName:Id")
                        killed_parts = log.Killed.split(":")
                        if len(killed_parts) >= 2:
                            killed_name = killed_parts[0]
                            killed_id = killed_parts[1]
                            killed_link = f"[{killed_name}](https://roblox.com/users/{killed_id}/profile)"
                        else:
                            killed_name = log.Killed
                            killed_link = killed_name

                        # Create embed for individual kill log
                        embed = discord.Embed(
                            title="🔫 ERLC Kill Log",
                            description=f"{killer_link} killed {killed_link} <t:{int(log.timestamp)}:R>",
                            color=RED_COLOR,
                            timestamp=datetime.fromtimestamp(log.timestamp) if log.timestamp else datetime.now()
                        )

                        embed.set_footer(
                            text="ERLC Kill Logs | Cyni Bot",
                            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                        )

                        embeds.append(embed)

                        # Update last processed timestamp
                        self.last_kill_log_timestamp[guild_id] = log.timestamp

                    except Exception as e:
                        self.logger.error(f"Error processing kill log for guild {guild_id}: {e}")

                # Send all embeds in this batch at once
                if embeds:
                    await channel.send(embeds=embeds)
                    # Small delay between batches
                    await asyncio.sleep(1)

        except ResponseFailed as e:
            if e.code != 422:  # Don't log server offline errors
                self.logger.error(f"PRC API error for kill logs guild {guild_id}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error processing kill logs for guild {guild_id}: {e}")

    async def process_join_logs(self, guild_id: int, join_logs_channel_id: int):
        """Process and send join/leave logs for a guild."""
        try:
            # Fetch join logs from PRC API
            join_logs: List[ServerJoinLogs] = await self.bot.prc_api._fetch_server_join_logs(guild_id)
            
            if not join_logs:
                return

            # Get last processed timestamp for this guild
            last_timestamp = self.last_join_log_timestamp.get(guild_id, 0)
            new_logs = []

            # Filter for new logs only
            for log in join_logs:
                if log.Timestamp and log.Timestamp > last_timestamp:
                    new_logs.append(log)

            if not new_logs:
                return

            # Sort by timestamp (oldest first for chronological posting)
            new_logs.sort(key=lambda x: x.Timestamp or 0)

            # Get the channel (with caching)
            channel = await self.get_cached_channel(join_logs_channel_id)
            if not channel:
                self.logger.warning(f"Join logs channel {join_logs_channel_id} not found for guild {guild_id}")
                return

            # Group logs into batches of 10 to send together
            batch_size = 10
            for i in range(0, len(new_logs), batch_size):
                batch = new_logs[i:i + batch_size]
                embeds = []

                for log in batch:
                    try:
                        # Parse player info (format: "PlayerName:Id")
                        player_parts = log.Player.split(":")
                        if len(player_parts) >= 2:
                            player_name = player_parts[0]
                            player_id = player_parts[1]
                            player_link = f"[{player_name}](https://roblox.com/users/{player_id}/profile)"
                        else:
                            player_name = player_parts[0]
                            player_link = player_name

                        # Determine action and color
                        status = 'joined' if log.Join else 'left'
                        color = GREEN_COLOR if log.Join else RED_COLOR
                        emoji = "🟢" if log.Join else "🔴"
                        log_type = "Player Join Log" if log.Join else "Player Leave Log"

                        # Create embed for individual join/leave log
                        embed = discord.Embed(
                            title=f"{emoji} {log_type}",
                            description=f"{player_link} {status} the server <t:{int(log.Timestamp)}:R>",
                            color=color,
                            timestamp=datetime.fromtimestamp(log.Timestamp) if log.Timestamp else datetime.now()
                        )

                        embed.set_footer(
                            text="ERLC Join/Leave Logs | Cyni Bot",
                            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                        )

                        embeds.append(embed)

                        # Update last processed timestamp
                        self.last_join_log_timestamp[guild_id] = log.Timestamp

                    except Exception as e:
                        self.logger.error(f"Error processing join log for guild {guild_id}: {e}")

                # Send all embeds in this batch at once
                if embeds:
                    await channel.send(embeds=embeds)
                    # Small delay between batches
                    await asyncio.sleep(1)

        except ResponseFailed as e:
            if e.code != 422:  # Don't log server offline errors
                self.logger.error(f"PRC API error for join logs guild {guild_id}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error processing join logs for guild {guild_id}: {e}")

    @tasks.loop(minutes=1, reconnect=True)
    async def process_prc_logs(self):
        """Main task loop to process PRC logs for all configured guilds."""
        try:
            # Get all guilds with ERLC logging configuration
            guilds = await self.get_guilds_with_erlc_config()

            for guild_data in guilds:
                guild_id = guild_data.get('_id')
                erlc_config = guild_data.get('erlc', {})

                # Check if guild has a linked ERLC server
                try:
                    await self.bot.prc_api._fetch_server_status(guild_id)
                except (ResponseFailed, Exception):
                    # Skip guilds without linked ERLC servers
                    continue

                # Process kill logs if channel is configured
                kill_logs_channel = erlc_config.get('kill_logs_channel')
                if kill_logs_channel:
                    await self.process_kill_logs(guild_id, kill_logs_channel)

                # Process join logs if channel is configured
                join_logs_channel = erlc_config.get('join_logs_channel')
                if join_logs_channel:
                    await self.process_join_logs(guild_id, join_logs_channel)

                # Small delay between guilds to avoid rate limits (reduced since running more frequently)
                await asyncio.sleep(0.5)

        except Exception as e:
            self.logger.error(f"Error in PRC logs processing task: {e}")

    @process_prc_logs.before_loop
    async def before_process_prc_logs(self):
        """Wait for the bot to be ready before starting the task."""
        await self.bot.wait_until_ready()

# Global processor instance
prc_processor = None

def setup_prc_logs_processor(bot):
    """Setup the PRC logs processor."""
    global prc_processor
    prc_processor = PRCLogsProcessor(bot)
    prc_processor.start_task()

def stop_prc_logs_processor():
    """Stop the PRC logs processor."""
    global prc_processor
    if prc_processor:
        prc_processor.stop_task()
        prc_processor.clear_caches()
        prc_processor = None
