import datetime
import discord

from discord.ext import commands

from utils.utils import discord_time, generate_embed


class OnGuildChannelCreate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =========================================================
    # EVENT
    # =========================================================

    @commands.Cog.listener()
    async def on_guild_channel_create(
        self,
        channel: discord.abc.GuildChannel
    ):

        guild = channel.guild

        try:

            # =================================================
            # GET SETTINGS
            # =================================================

            settings = await self.bot.cache.get_settings(
                guild.id
            )

            if not settings:
                return

            moderation = settings.get(
                "moderation_module",
                {}
            )

            if not moderation.get("enabled"):
                return

            # =================================================
            # GET AUDIT LOG CHANNEL
            # =================================================

            audit_log_channel_id = (
                await self.bot.cache.get_audit_log_channel(
                    guild.id
                )
            )

            if not audit_log_channel_id:
                return

            guild_log_channel = guild.get_channel(
                audit_log_channel_id
            )

            # =================================================
            # RECOVERY MODE
            # =================================================

            if not guild_log_channel:

                self.bot.logger.warning(
                    f"[RECOVERY] Invalid audit log "
                    f"cache for guild {guild.id}"
                )

                audit_log_channel_id = (
                    await self.bot.cache.recover_audit_log_channel(
                        guild.id
                    )
                )

                if not audit_log_channel_id:
                    return

                guild_log_channel = guild.get_channel(
                    audit_log_channel_id
                )

            if not guild_log_channel:
                return

            # =================================================
            # PREMIUM
            # =================================================

            premium_status = (
                await self.bot.cache.is_premium(
                    guild.id
                )
            )

            # Premium guild trying to use free bot
            if premium_status and not self.bot.is_premium:
                return

            server_is_premium = premium_status is True

            custom_colors = (
                settings.get(
                    "customization",
                    {}
                ).get(
                    "embed_colors",
                    {}
                )
                if server_is_premium
                else {}
            )

            # =================================================
            # AUDIT LOG ENTRY
            # =================================================

            entry = None

            async for log in guild.audit_logs(
                limit=1,
                action=discord.AuditLogAction.channel_create
            ):
                entry = log
                break

            moderator = (
                entry.user.mention
                if entry and entry.user
                else "Unknown User"
            )

            # =================================================
            # EMBED
            # =================================================

            created_at = discord_time(
                datetime.datetime.utcnow()
            )

            embed = generate_embed(
                guild=guild,
                title="Channel Created",
                category="logging",
                description=(
                    f"{moderator} created "
                    f"{channel.mention} "
                    f"on {created_at}"
                ),
                footer=f"Channel ID: {channel.id}",
                premium=server_is_premium,
                custom_colors=custom_colors,
                fields=[
                    {
                        "name": "Channel Type",
                        "value": str(channel.type).capitalize(),
                        "inline": True
                    },
                    {
                        "name": "Channel ID",
                        "value": str(channel.id),
                        "inline": True
                    },
                    {
                        "name": "Category",
                        "value": (
                            channel.category.name
                            if channel.category
                            else "None"
                        ),
                        "inline": False
                    }
                ]
            )

            # =================================================
            # LOGGER
            # =================================================

            logger = self.bot.get_cog(
                "ThrottledLogger"
            )

            if not logger:
                return

            await logger.log_embed(
                guild_log_channel,
                embed
            )

        except discord.Forbidden:

            self.bot.logger.warning(
                f"Missing permissions "
                f"in guild {guild.id}"
            )

        except discord.HTTPException as e:

            self.bot.logger.error(
                f"Discord HTTPException "
                f"in guild {guild.id}: {e}"
            )

        except Exception:

            self.bot.logger.exception(
                f"Failed handling "
                f"channel create event "
                f"for guild {guild.id}"
            )


async def setup(bot):
    await bot.add_cog(
        OnGuildChannelCreate(bot)
    )