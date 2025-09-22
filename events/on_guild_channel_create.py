import discord
from discord.ext import commands

from utils.constants import RED_COLOR, GREEN_COLOR
from utils.utils import discord_time, generate_embed
from cyni import premium_check_fun
import datetime
import os
from dotenv import load_dotenv
import requests

load_dotenv()

class OnGuildChannelCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """
        This event is triggered when a channel is created in a guild.
        :param channel (discord.TextChannel): The channel that was created.
        """
        try:
            premium_status = await premium_check_fun(self.bot, channel.guild)
            if premium_status in [True] and self.bot.is_premium == False:
                return
                
            sett = await self.bot.settings.find_by_id(channel.guild.id)
            guild = channel.guild
            if not sett:
                return
            if sett.get("moderation_module", {}).get("enabled", False) is False:
                return
            if sett.get("moderation_module", {}).get("audit_log") is None:
                return
            guild_log_channel = guild.get_channel(sett.get("moderation_module", {}).get("audit_log"))
            if not guild_log_channel:
                return
            created_at = discord_time(datetime.datetime.now())

            # Get premium status and custom colors for embed generation
            server_is_premium = (premium_status == True)  # True only if server is premium and using premium bot
            custom_colors = sett.get("customization", {}).get("embed_colors", {}) if server_is_premium else {}

            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                # PANEL_URL = os.getenv('PANEL_URL')
                # PANEL_KEY = os.getenv('PANEL_KEY')
                # response = requests.post(
                #     f"{PANEL_URL}/api/v1/panel/channel/create",
                #     headers={"Authorization": f"Bearer {PANEL_KEY}"},
                #     json=channel.to_dict()
                # )
                # if response.status_code != 200:
                #     self.bot.logger.error(f"Failed to log channel creation to panel: {response.status_code} - {response.text}")

                embed = generate_embed(
                    guild,
                    title="Channel Created",
                    category="logging",
                    description=f"{entry.user.mention} created {channel.name} on {created_at}",
                    footer=f"Channel ID: {channel.id}",
                    premium=server_is_premium,
                    custom_colors=custom_colors,
                    fields=[
                        {"name": "Channel Type", "value": str(channel.type).capitalize(), "inline": True},
                        {"name": "Channel ID", "value": str(channel.id), "inline": True},
                        {"name": "Category", "value": str(channel.category) if channel.category else "None", "inline": False}
                    ]
                )
                logger = self.bot.get_cog("ThrottledLogger")
                await logger.log_embed(guild_log_channel, embed)
        except Exception as e:
            pass

async def setup(bot):
    await bot.add_cog(OnGuildChannelCreate(bot))