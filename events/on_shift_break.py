import discord
from bson import ObjectId
from discord.ext import commands
from utils.constants import YELLOW_COLOR
import os
from dotenv import load_dotenv
import requests

load_dotenv()

class OnShiftBreak(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_shift_break(self, object_id: ObjectId, status: str, timestamp: int):

        document = await self.bot.shift_logs.find_by_id(object_id)
        if not document:
            return
        
        guild: discord.Guild = self.bot.get_guild(document["guild_id"])
        if guild is None:
            return

        guild_settings = await self.bot.settings.find_by_id(guild.id)
        if not guild_settings:
            return

        try:
            staff_member: discord.Member = await guild.fetch_member(document["user_id"])
        except discord.NotFound:
            return

        if not staff_member:
            return

        channel_id = guild_settings.get("roblox", {}).get("shift_module", {}).get("channel")
        channel: discord.TextChannel = guild.get_channel(channel_id) if channel_id else None

        on_duty_role_id = guild_settings.get("roblox", {}).get("shift_module", {}).get("on_duty_role")
        on_duty_role: discord.Role = guild.get_role(on_duty_role_id) if on_duty_role_id else None

        on_break_role_id = guild_settings.get("roblox", {}).get("shift_module", {}).get("on_break_role")
        on_break_role: discord.Role = guild.get_role(on_break_role_id) if on_break_role_id else None

        guild_roles = await guild.fetch_roles()
        if status == "start":
            if on_break_role in guild_roles:
                try:
                    await staff_member.add_roles(on_break_role, atomic=True)
                except discord.HTTPException:
                    pass
            if on_duty_role in guild_roles:
                try:
                    await staff_member.remove_roles(on_duty_role, atomic=True)
                except discord.HTTPException:
                    pass
        elif status == "end":
            if on_break_role in guild_roles:
                try:
                    await staff_member.remove_roles(on_break_role, atomic=True)
                except discord.HTTPException:
                    pass
            if on_duty_role in guild_roles:
                try:
                    await staff_member.add_roles(on_duty_role, atomic=True)
                except discord.HTTPException:
                    pass

        # PANEL_URL = os.getenv('PANEL_URL')
        # PANEL_KEY = os.getenv('PANEL_KEY')
        # response = requests.post(
        #     f"{PANEL_URL}/api/v1/modpanel/shifts",
        #     headers={"Authorization": f"Bearer {PANEL_KEY}"},
        #     json=document
        # )
        # if response.status_code != 200:
        #     self.bot.logger.error(f"Failed to log shift end to panel: {response.status_code} - {response.text}")

        if channel is not None:
            await channel.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('shiftbreak')} Break {'Started' if status == 'start' else 'Ended'}",
                    description=(
                        f"> **Shift Details for {staff_member.mention}**\n\n"
                        f"> **Shift Type:** {document['type'].capitalize()}\n"
                        f"> **Break {'Started' if status == 'start' else 'Ended'}:** <t:{timestamp}:F>\n"
                        f"> **Nickname:** `{staff_member.nick}`\n"
                    ),
                    color=YELLOW_COLOR
                )
                .set_thumbnail(
                    url=staff_member.display_avatar.url
                )
                .set_footer(
                    text="Shift Management System",
                    icon_url=guild.icon.url if guild.icon else None
                )
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(OnShiftBreak(bot))