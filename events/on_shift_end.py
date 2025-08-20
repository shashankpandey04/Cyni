import discord
from bson import ObjectId
from discord.ext import commands
from utils.constants import RED_COLOR


class OnShiftEnd(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_shift_end(self, object_id: ObjectId):

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

        guild_roles = await guild.fetch_roles()
        if on_duty_role in guild_roles:
            try:
                await staff_member.remove_roles(on_duty_role, atomic=True)
            except discord.HTTPException:
                pass
        total_duration_seconds = document.get('duration', 0)
        hours, remainder = divmod(total_duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        total_duration = f"{hours}h {minutes}m {seconds}s" if total_duration_seconds > 0 else "Not Applicable"
        if channel is not None:
            await channel.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('offshift')} Shift Ended",
                    description=(
                        f"> **Shift Details for {staff_member.mention}**\n\n"
                        f"> **Shift Type:** {document['type'].capitalize()}\n"
                        f"> **Shift Start:** <t:{int(document['start_epoch'])}:F>\n"
                        f"> **Shift End:** <t:{int(document['end_epoch'])}:F>\n"
                        f"> **Total Duration:** {total_duration}"
                    ),
                    color=RED_COLOR
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
    await bot.add_cog(OnShiftEnd(bot))