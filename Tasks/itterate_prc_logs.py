from collections import defaultdict
import discord
import re
from discord.ext import tasks
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR
from utils.prc_api import ServerKillLogs, ServerJoinLogs, ResponseFailed
    
_guild_cache = {}
_member_search_cache = defaultdict(dict)
_cache_timeout = 300

async def get_cached_member_by_username(guild, username):
    """Get member by username with caching"""
    now = time.time()
    cache_key = f"{guild.id}_{username.lower()}"

    if cache_key in _member_search_cache[guild.id]:
        member_obj, cached_time = _member_search_cache[guild.id][cache_key]
        if now - cached_time < _cache_timeout:
            return member_obj

    pattern = re.compile(re.escape(username), re.IGNORECASE)
    member = None

    for m in guild.members:
        if (
            pattern.search(m.name)
            or pattern.search(m.display_name)
            or (hasattr(m, "global_name") and m.global_name and pattern.search(m.global_name))
        ):
            member = m
            break

    if not member:
        try:
            members = await guild.query_members(query=username, limit=1)
            member = members[0] if members else None
        except discord.HTTPException:
            member = None

    _member_search_cache[guild.id][cache_key] = (member, now)
    return member

async def handle_discord_check_batch(bot, guild, players_not_in_discord, alert_channel, alert_message, kick_after=0):
    """Handle batch of players not in Discord"""
    if not players_not_in_discord:
        return
    
    try:
        usernames = [player.username for player in players_not_in_discord]
        command = f":pm {', '.join(usernames)} {alert_message}"

        await bot.prc_api.run_command(guild.id, command)

        if not hasattr(bot, 'discord_check_counter'):
            bot.discord_check_counter = {}
        
        players_to_kick = []
        for player in players_not_in_discord:
            key = f"{guild.id}_{player.username}"
            if key not in bot.discord_check_counter:
                bot.discord_check_counter[key] = 1
            else:
                bot.discord_check_counter[key] += 1

            if bot.discord_check_counter[key] >= kick_after and kick_after > 0:
                players_to_kick.append(player)
                bot.discord_check_counter.pop(key)

        if players_to_kick and alert_channel is not None:
            await send_batch_warning_embed(players_to_kick, alert_channel, bot)

    except Exception as e:
        bot.logger.error(f"Error in handle_discord_check_batch: {e}")
        
async def send_batch_warning_embed(players, alert_channel, bot):
    """Send warning embed for multiple players"""
    try:
        player_list = []
        for player in players:
            player_list.append(f"[{player.username}](https://roblox.com/users/{player.id}/profile)")
        
        embed = discord.Embed(
            title="Discord Check Warning",
            description=f"""
            > The following players have been kicked from the server for not joining the Discord server after multiple warnings:
            
            {chr(10).join([f"> • {player}" for player in player_list])}
            """,
            color=BLANK_COLOR,
        )

        await alert_channel.send(embed=embed)
    except discord.HTTPException as e:
        bot.logger.error(f"Failed to send batch embed: {e}")
    except Exception as e:
        bot.logger.error(f"Error in send_batch_warning_embed: {e}", exc_info=True)

class PRCLogsProcessor:
    """Automated PRC logs processor that sends kill logs and join/leave logs to configured channels."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.last_kill_log_timestamp = {}
        self.last_join_log_timestamp = {}
        self.username_cache = {}
        self.guilds_cache = []
        self.channels_cache = {}
        self.last_cache_update = 0
        self.cache_duration = 300

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
                username = await asyncio.to_thread(self.bot.roblox._get_username_by_id, user_id)
                self.username_cache[user_id] = username
            except Exception as e:
                self.logger.error(f"Error fetching username for user {user_id}: {e}")
                self.username_cache[user_id] = f"User {user_id}"
        return self.username_cache[user_id]

    async def get_guilds_with_erlc_config(self) -> List[Dict]:
        """Get all guilds that have ERLC configuration with logging channels (with caching)."""
        current_time = time.time()
        
        if current_time - self.last_cache_update < self.cache_duration and self.guilds_cache:
            return self.guilds_cache
        
        try:
            guilds = await self.bot.settings.find({
                "$or": [
                    {"erlc.kill_logs_channel": {"$exists": True, "$ne": None}},
                    {"erlc.join_logs_channel": {"$exists": True, "$ne": None}}
                ]
            })
            
            self.guilds_cache = guilds
            self.last_cache_update = current_time
            
            return guilds
        except Exception as e:
            self.logger.error(f"Error fetching guilds with ERLC config: {e}")
            return self.guilds_cache if self.guilds_cache else []

    async def get_cached_channel(self, channel_id: int):
        """Get channel with caching to reduce bot.get_channel calls."""
        if channel_id not in self.channels_cache:
            channel = self.bot.get_channel(channel_id)
            if channel:
                self.channels_cache[channel_id] = channel
            else:
                self.channels_cache[channel_id] = None
        return self.channels_cache[channel_id]

    async def process_kill_logs(self, guild_id: int, kill_logs_channel_id: int):
        """Process and send kill logs for a guild."""
        try:
            kill_logs: List[ServerKillLogs] = await self.bot.prc_api._fetch_server_killlogs(guild_id)

            if not kill_logs:
                return

            last_timestamp = self.last_kill_log_timestamp.get(guild_id, 0)
            new_logs = [log for log in kill_logs if log.Timestamp and log.Timestamp > last_timestamp]

            if not new_logs:
                return

            new_logs.sort(key=lambda x: x.Timestamp or 0)

            channel = await self.get_cached_channel(kill_logs_channel_id)
            if not channel:
                return
            
            batch_size = 10
            for i in range(0, len(new_logs), batch_size):
                batch = new_logs[i:i + batch_size]
                embeds = []

                for log in batch:
                    try:
                        killer_name, killer_link = await self._parse_player_info(log.Killer)
                        killed_name, killed_link = await self._parse_player_info(log.Killed)

                        embed = discord.Embed(
                            title="🔫 ERLC Kill Log",
                            description=f"{killer_link} killed {killed_link} <t:{int(log.Timestamp)}:R>",
                            color=RED_COLOR,
                            timestamp=datetime.fromtimestamp(log.Timestamp) if log.Timestamp else datetime.now()
                        )

                        embed.set_footer(
                            text="ERLC Kill Logs | Cyni Bot",
                            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                        )

                        embeds.append(embed)

                        self.last_kill_log_timestamp[guild_id] = log.Timestamp

                    except Exception as e:
                        self.logger.error(f"Error processing kill log for guild {guild_id}: {e}")

                if embeds:
                    await channel.send(embeds=embeds)
                    await asyncio.sleep(1)

        except ResponseFailed as e:
            if e.code != 422:
                #self.logger.error(f"PRC API error for kill logs guild {guild_id}: {e}")
                pass
        except Exception as e:
            #self.logger.error(f"Unexpected error processing kill logs for guild {guild_id}: {e}")
            pass

    async def _parse_player_info(self, player_info: str):
        """Parse player info into name and profile link."""
        try:
            player_parts = player_info.split(":")
            if len(player_parts) >= 2:
                player_name = player_parts[0]
                player_id = player_parts[1]
                player_link = f"[{player_name}](https://roblox.com/users/{player_id}/profile)"
            else:
                player_name = player_info
                player_link = player_name
            return player_name, player_link
        except Exception as e:
            self.logger.error(f"Error parsing player info: {e}")
            return player_info, player_info

    async def process_join_logs(self, guild_id: int, join_logs_channel_id: int, join_logs: List[ServerJoinLogs]):
        """Process and send join/leave logs for a guild."""
        try:
            
            if not join_logs:
                return

            last_timestamp = self.last_join_log_timestamp.get(guild_id, 0)
            new_logs = []

            # Filter for new logs only
            for log in join_logs:
                if log.Timestamp and log.Timestamp > last_timestamp:
                    new_logs.append(log)

            if not new_logs:
                return

            new_logs.sort(key=lambda x: x.Timestamp or 0)

            channel = await self.get_cached_channel(join_logs_channel_id)
            if not channel:
                return

            batch_size = 10
            for i in range(0, len(new_logs), batch_size):
                batch = new_logs[i:i + batch_size]
                embeds = []

                for log in batch:
                    try:
                        player_parts = log.Player.split(":")
                        if len(player_parts) >= 2:
                            player_name = player_parts[0]
                            player_id = player_parts[1]
                            player_link = f"[{player_name}](https://roblox.com/users/{player_id}/profile)"
                        else:
                            player_name = player_parts[0]
                            player_link = player_name

                        status = 'joined' if log.Join else 'left'
                        color = GREEN_COLOR if log.Join else RED_COLOR
                        emoji = "🟢" if log.Join else "🔴"
                        log_type = "Player Join Log" if log.Join else "Player Leave Log"

                        if log.Timestamp and log.Timestamp < int(time.time()) - 60:
                            continue
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

                        self.last_join_log_timestamp[guild_id] = log.Timestamp

                    except Exception as e:
                        self.logger.error(f"Error processing join log for guild {guild_id}: {e}")

                if embeds:
                    await channel.send(embeds=embeds)
                    await asyncio.sleep(1)

        except ResponseFailed as e:
            if e.code != 422:
                self.logger.error(f"PRC API error for join logs guild {guild_id}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error processing join logs for guild {guild_id}: {e}")


    async def process_discord_checks(bot, items, guild_id):
        """
        This function will process Discord checks for PRC servers.
        """
        try:
            settings = items["ERLC"].get("discord_checks", {})
            if not settings:
                return

            if not settings.get("enabled", False):
                return
            
            message = settings.get("message", "Please join the Private Server Communication channel.")
            channel_id = settings.get("channel_id", 0)
            channel = None
            if channel_id != 0:
                channel = await bot.get_channel(channel_id)
                if not channel:
                    bot.logger.error(f"Channel {channel_id} not found in guild {guild_id}.")
                    return

            guild = await bot.get_guild(guild_id)
            if not guild:
                return

            try:
                players = await bot.prc_api.get_server_players(guild_id)
                if not players:
                    bot.logger.info(f"No players found in guild {guild_id}")
                    return

            except Exception as e:
                bot.logger.error(f"Failed to fetch server data for guild {guild_id}: {e}")
                return
            
            not_in_discord = []
            
            for player in players:
                member = await get_cached_member_by_username(guild, player.username)
                if not member:
                    if player.permission is None or player.permission.lower() not in ["server administrator", "server owner", "server moderator"]:
                        not_in_discord.append(player)
                #======WILL BE IMPLEMENTED IN NEXT UPDATE======
                # else:
                #     callsign_valid = await handle_callsign_check(guild, player.callsign, items, member)
                #     if not callsign_valid:
                #         callsign_violations.append(player)
            try:
                kick_after = settings.get("kick_after", 0)
            except Exception as e:
                bot.logger.error(f"Error getting kick_after setting for guild {guild_id}: {e}")
                kick_after = 0

            if not_in_discord:
                await handle_discord_check_batch(bot, guild, not_in_discord, channel, message, kick_after)

        except Exception as e:
            bot.logger.error(f"Error processing guild {guild_id}: {e}", exc_info=True)
            return

    @tasks.loop(minutes=1, reconnect=True)
    async def process_prc_logs(self):
        """Main task loop to process PRC logs for all configured guilds."""
        try:
            guilds = await self.get_guilds_with_erlc_config()

            for guild_data in guilds:
                guild_id = guild_data.get('_id')
                erlc_config = guild_data.get('erlc', {})

                try:
                    await self.bot.prc_api._fetch_server_status(guild_id)
                except (ResponseFailed, Exception):
                    continue

                kill_logs_channel = erlc_config.get('kill_logs_channel')
                if kill_logs_channel:
                    await self.process_kill_logs(guild_id, kill_logs_channel)
                join_logs: List[ServerJoinLogs] = await self.bot.prc_api._fetch_server_join_logs(guild_id)
                join_logs_channel = erlc_config.get('join_logs_channel')
                if join_logs_channel:
                    await self.process_join_logs(guild_id, join_logs_channel, join_logs)

                discord_checks_channel = erlc_config.get('discord_checks_channel')
                if discord_checks_channel:
                    await self.process_discord_checks(guild_id, discord_checks_channel)

                await asyncio.sleep(0.5)

        except Exception as e:
            self.logger.error(f"Error in PRC logs processing task: {e}")

    @process_prc_logs.before_loop
    async def before_process_prc_logs(self):
        """Wait for the bot to be ready before starting the task."""
        await self.bot.wait_until_ready()

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
