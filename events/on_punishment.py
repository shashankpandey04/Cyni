import discord
from bson import ObjectId
from discord.ext import commands
from utils.constants import GREEN_COLOR
import os
from dotenv import load_dotenv
import requests

load_dotenv()

class OnPunishment(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_punishment(self, warning: ObjectId, author: discord.User, thumbnail: str):

        warning = await self.bot.punishments.find_by_id(warning)
        if warning is None:
            return

        guild: discord.Guild = self.bot.get_guild(warning["guild_id"])
        if guild is None:
            return

        guild_settings = await self.bot.settings.find_by_id(guild.id)
        if not guild_settings:
            return

        channel_id = guild_settings.get("roblox", {}).get("punishments", {}).get("channel")
        channel: discord.TextChannel = guild.get_channel(channel_id) if channel_id else None

        # PANEL_URL = os.getenv('PANEL_URL')
        # PANEL_KEY = os.getenv('PANEL_KEY')
        # response = requests.post(
        #     f"{PANEL_URL}/api/v1/modpanel/punishments",
        #     headers={"Authorization": f"Bearer {PANEL_KEY}"},
        #     json=warning
        # )
        # if response.status_code != 200:
        #     self.bot.logger.error(f"Failed to log punishment to panel: {response.status_code} - {response.text}")

        log_embed = discord.Embed(
                title=f"{self.bot.emoji.get('caution')} Logged Punishment",
                color=GREEN_COLOR,
            ).add_field(
                name="Punishment Information",
                value=(
                    f"> **Player:** {warning['user_name']}\n"
                    f"> **Type:** {warning['type']}\n"
                    f"> **Reason:** {warning['reason']}\n"
                    f"> **At:** <t:{int(warning['timestamp'])}>\n"
                    f"> **ID:** `{warning['snowflake']}`\n"
                ),
                inline=False
            ).add_field(
                name="Moderator Information",
                value=(
                    f"> **Mention:** <@{warning['moderator_id']}>\n"
                    f"> **Username:** {warning['moderator_name']}\n"
                    f"> **ID:** `{warning['moderator_id']}`"
                )
            ).set_author(
                name=author.name,
                icon_url=author.display_avatar.url if author.display_avatar else None
            ).set_thumbnail(
                url=thumbnail
            )
        
        # Bypass ThrottledLogger for now - direct send
        try:
            await channel.send(embed=log_embed)
        except discord.HTTPException as e:
            self.bot.logger.error(f"Failed to send punishment log to channel {channel.id}: {e}")
        except Exception as e:
            self.bot.logger.error(f"Unexpected error sending punishment log: {e}")
            
        # Original throttled logger code (commented out for testing)
        # logger = self.bot.get_cog("ThrottledLogger")
        # await logger.log_embed(channel, log_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(OnPunishment(bot))
