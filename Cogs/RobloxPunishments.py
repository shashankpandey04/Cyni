import discord
from discord.ext import commands
import time
from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR
from discord import app_commands
from cyni import is_roblox_management, is_roblox_staff, roblox_staff_check, roblox_management_check
from utils.utils import log_command_usage, snowflake_generator
from utils.pagination import Pagination
from utils.autocompletes import punishment_autocomplete, username_autocomplete
import roblox
import datetime
from utils.basic_pager import BasicPager
from Views.RobloxManagement import PunishmentManage

class RobloxPunishments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="punishments",
        aliases=["punish", "p"],
    )
    @commands.guild_only()
    async def punishment(self, ctx):
        """
        Manage Roblox punishments commands.
        """
        pass

    @punishment.command(
        name="log",
        aliases=["lg"],
        description="Log a Roblox punishment for a user.",
        extras={
            "category": "Roblox Punishments"
        },
        usage="punishment log <username> <punishment> <reason>"
    )
    @commands.guild_only()
    @is_roblox_staff()
    @app_commands.describe(
        username="The Roblox username to log punishments for",
        reason="The reason for the punishment"
    )
    @app_commands.autocomplete(punishment=punishment_autocomplete)
    @app_commands.autocomplete(username=username_autocomplete)
    async def log_punishment(self, ctx, username: str, punishment: str, reason: str):
        """
        View Roblox punishments for a user.
        """
        try:
            await ctx.typing()
            if punishment.lower() not in ["warning", "kick", "ban", "bolo"]:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Invalid Punishment",
                        description=(
                            f"> The punishment `{punishment}` is not a valid punishment type.\n"
                            f"> Please choose from the following: `Warning`, `Kick`, `Ban`, `Bolo`."
                        ),
                        color=RED_COLOR
                    )
                )
            
            setting = await self.bot.settings.find_by_id(ctx.guild.id)
            if setting is None:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Missing Settings",
                        description="Please configure the settings for this server.",
                        color=discord.Color.red()
                    )
                )

            if not setting.get("roblox", {}).get("punishments"):
                return await ctx.send(
                    embed=discord.Embed(
                        title="Missing Punishments",
                        description="Please configure the punishments for this server.",
                        color=discord.Color.red()
                    )
                )
            
            punishment_doc = setting["roblox"]["punishments"]
            if not punishment_doc.get("enabled", False):
                return await ctx.send(
                    embed=discord.Embed(
                        title="Punishments Disabled",
                        description="Roblox punishments are not enabled for this server.",
                        color=discord.Color.red()
                    )
                )

            channel_id = punishment_doc.get("channel")
            if not channel_id:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Missing Channel",
                        description="Please configure the punishment log channel for this server.",
                        color=discord.Color.red()
                    )
                )

            roblox_user = await self.bot.roblox.get_user_by_username(username)
            if roblox_user is None:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Player Not Found",
                        description=(
                            f"> There was an issue while finding the Roblox User: `{username}`. "
                            f"> Please make sure you have entered correct username."
                        ),
                        color=RED_COLOR
                    )
                )
            
            roblox_player = await self.bot.roblox.get_user(roblox_user.id)
            thumbnails = await self.bot.roblox.thumbnails.get_user_avatar_thumbnails(
                [roblox_player], type=roblox.thumbnails.AvatarThumbnailType.headshot
            )
            if not thumbnails or not thumbnails[0]:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Thumbnail Error",
                        description="Could not retrieve the user's avatar thumbnail.",
                        color=RED_COLOR
                    )
                )
            thumbnail = thumbnails[0].image_url

            timestamp = datetime.datetime.now().timestamp()

            doc = {
                "moderator_id": ctx.author.id,
                "moderator_name": ctx.author.name,
                "user_id": roblox_player.id,
                "user_name": roblox_player.name,
                "guild_id": ctx.guild.id,
                "reason": reason,
                "type": punishment.lower(),
                "timestamp": timestamp,
                "snowflake": next(snowflake_generator),
            }

            await self.bot.punishments.insert_one(doc)

            warning = await self.bot.punishments.find_one(
                {
                    "guild_id": ctx.guild.id,
                    "user_id": roblox_player.id,
                    "type": punishment.lower(),
                    "timestamp": timestamp,
                    "moderator_id": ctx.author.id,
                }
            )
            self.bot.dispatch("punishment", warning["_id"], ctx.author, thumbnail)

            mod_embed = discord.Embed(
                title="Punishment Logged",
                description=(
                    f"> **Player:** {roblox_player.name}\n"
                    f"> **Type:** {punishment.capitalize()}\n"
                    f"> **Reason:** {reason}\n"
                    f"> **At:** <t:{int(timestamp)}>\n"
                    f"> **ID:** `{doc['snowflake']}`"
                )
            ).set_author(
                name=ctx.author.name,
                icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
            ).set_thumbnail(
                url=thumbnail
            )
            return await ctx.send(embed=mod_embed)

        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error Occurred",
                    description=str(e),
                    color=discord.Color.red()
                )
            )


    @punishment.command(
        name="view",
        aliases=["v"],
    )
    @commands.guild_only()
    @is_roblox_staff()
    @app_commands.describe(username="The Roblox username to view punishments for")
    @app_commands.autocomplete(username=username_autocomplete)
    async def view_punishments(self, ctx, username: str):
        """View a user's Roblox punishments."""
        try:
            await ctx.typing()
            setting = await self.bot.settings.find_by_id(ctx.guild.id)
            if not setting:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Missing Settings",
                        description="Please configure the settings for this server.",
                        color=RED_COLOR
                    )
                )

            punishment_doc = setting.get("roblox", {}).get("punishments", {})
            if not punishment_doc.get("enabled", False):
                return await ctx.send(
                    embed=discord.Embed(
                        title="Punishments Disabled",
                        description="Roblox punishments are not enabled for this server.",
                        color=RED_COLOR
                    )
                )
            roblox_user = await self.bot.roblox.get_user_by_username(username)
            if roblox_user is None:
                print("Roblox user not found:", username)
                return await ctx.send(
                    embed=discord.Embed(
                        title="Player Not Found",
                        description=(
                            f"> There was an issue while finding the Roblox User: `{username}`. "
                            f"> Please make sure you have entered correct username."
                        ),
                        color=RED_COLOR
                    )
                )
            
            roblox_player = await self.bot.roblox.get_user(roblox_user.id)
            thumbnails = await self.bot.roblox.thumbnails.get_user_avatar_thumbnails(
                [roblox_player], type=roblox.thumbnails.AvatarThumbnailType.headshot
            )
            thumbnail = thumbnails[0].image_url if thumbnails else None
            punishments = await self.bot.punishments.find(
                {
                    "user_name": username,
                    "guild_id": ctx.guild.id
                }
            )
            if not punishments:
                return await ctx.send(
                    embed=discord.Embed(
                        title="No Punishments Found",
                        description="No punishments found for the specified user or in this guild.",
                        color=BLANK_COLOR
                    )
                )

            embeds = [
                discord.Embed(
                    title=f"Punishment #{index + 1}",
                    description=(
                        f"**Moderator Information**\n"
                        f"> **Mention:** <@{punishment['moderator_id']}>\n"
                        f"> **User ID:** `{punishment['moderator_id']}`\n\n"
                        f"**Punishment Information**\n"
                        f"> **Type:** {punishment['type'].capitalize()}\n"
                        f"> **Reason:** {punishment['reason']}\n"
                        f"> **At:** <t:{int(punishment['timestamp'])}:F>\n"
                        f"> **ID:** `{punishment['snowflake']}`"
                    ),
                    color=BLANK_COLOR
                ).set_thumbnail(
                    url=thumbnail
                )
                for index, punishment in enumerate(punishments)
            ]
            if not embeds:
                return await ctx.send(
                    embed=discord.Embed(
                        title="No Punishments Found",
                        description="No punishments found for the specified user or in this guild.",
                        color=BLANK_COLOR
                    )
                )

            pager = BasicPager(
                user_id=ctx.author.id,
                embeds=embeds
            )
            await ctx.send(embed=embeds[0], view=pager)

        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error Occurred",
                    description=f"An unexpected error occurred while processing your request.```{e}```",
                    color=RED_COLOR
                )
            )

    @punishment.command(
        name="manage",
        aliases=["m"],
    )
    @commands.guild_only()
    @is_roblox_staff()
    async def manage(self, ctx, id: str):
        """
        Manage Roblox punishments.
        :param ctx: The context of the command.
        :param id: (snowflake) ID of the punishment to manage.
        """
        try:
            punishment = await self.bot.punishments.find_one(
                {
                    "snowflake": int(id),
                    "guild_id": ctx.guild.id,
                }
            )
            if not punishment:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Punishment Not Found",
                        description="No punishment found with the specified ID in this guild.",
                        color=RED_COLOR
                    )
                )
            if punishment['moderator_id'] != ctx.author.id:
                manager = await roblox_management_check(self.bot, ctx.guild, ctx.author)
                if not manager:
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Insufficient Permissions",
                            description="You do not have permission to manage this punishment.",
                            color=RED_COLOR
                        )
                    )
            elif punishment['moderator_id'] == ctx.author.id:
                staff = await roblox_staff_check(self.bot, ctx.guild, ctx.author)
                if not staff:
                    return await ctx.send(
                        embed=discord.Embed(
                            title="Insufficient Permissions",
                            description="You do not have permission to manage this punishment.",
                            color=RED_COLOR
                        )
                    )
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Insufficient Permissions",
                        description="You do not have permission to manage this punishment.",
                        color=RED_COLOR
                    )
                )
            roblox_player = await self.bot.roblox.get_user(punishment['user_id'])
            thumbnails = await self.bot.roblox.thumbnails.get_user_avatar_thumbnails(
                [roblox_player], type=roblox.thumbnails.AvatarThumbnailType.headshot
            )
            if not thumbnails or not thumbnails[0]:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Thumbnail Error",
                        description="Could not retrieve the user's avatar thumbnail.",
                        color=RED_COLOR
                    )
                )
            thumbnail = thumbnails[0].image_url
            punishment_embed = discord.Embed(
                title="Punishment Details",
                description=(
                    f"**Moderator Information**\n"
                    f"> **Name:** <@{punishment['moderator_id']}>\n"
                    f"> **User ID:** `{punishment['moderator_id']}`\n\n"
                    f"**Punishment Information**\n"
                    f"> **Name:** {punishment['user_name']}\n"
                    f"> **User ID:** `{punishment['user_id']}`\n"
                    f"> **Reason:** {punishment['reason']}\n"
                    f"> **Action Taken:** <t:{int(punishment['timestamp'])}:F>"
                ),
                color=BLANK_COLOR
            ).set_thumbnail(
                url=thumbnail
            ).set_footer(
                text=f"Punishment ID: {punishment['snowflake']}"
            )

            view = PunishmentManage(self.bot, ctx, punishment["snowflake"])

            await ctx.send(embed=punishment_embed, view=view)

        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error Occurred",
                    description=f"An unexpected error occurred while processing your request.```{e}```",
                    color=RED_COLOR
                )
            )


async def setup(bot):
    await bot.add_cog(RobloxPunishments(bot))
