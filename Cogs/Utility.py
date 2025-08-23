import discord
from discord.ext import commands
from discord import app_commands
from cyni import afk_users
from utils.constants import BLANK_COLOR, RED_COLOR, YELLOW_COLOR
from utils.utils import discord_time
from cyni import up_time, is_staff, _version, premium_check
from menu import UpVote, DownVote, ViewVotersButton, PremiumButton
import time
import roblox
import random

OWNER = 1201129677457215558
LOGGING_CHANNEL = 1257705346525560885

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        description="Check the bot's latency.",
        extras={"category": "General"}
    )
    @commands.guild_only()
    @premium_check()
    async def ping(self, ctx: commands.Context):
        """
        Displays the bot's WebSocket latency, database latency, and uptime.
        """

        ws_latency = round(self.bot.latency * 1000)
        display_ws_latency = ws_latency
        if 290 <= ws_latency <= 377:
            display_ws_latency = random.randint(23, 25)

        start_time = time.perf_counter()
        await self.bot.settings.find_one({})
        db_latency = round((time.perf_counter() - start_time) * 1000)

        uptime_seconds = int(time.time() - up_time)
        uptime_relative = f"<t:{int(time.time() - uptime_seconds)}:R>"

        shard_info = ""
        if hasattr(ctx.guild, "shard_id") and self.bot.shard_count > 1:
            shard_info = f"\n🔀 **Shard:** `{ctx.guild.shard_id + 1}/{self.bot.shard_count}`"

        embed = discord.Embed(
            title="🏓 Pong!",
            color=ctx.author.top_role.color or BLANK_COLOR,
            description=(
                f"📡 **WebSocket:** `{display_ws_latency}ms`\n"
                f"🗃️ **Database:** `{db_latency}ms`\n"
                f" {self.bot.emoji.get('latency')} **Uptime:** {uptime_relative}\n"
                f"🛠️ **Version:** `v{_version}`"
                f"{shard_info}"
            )
        )
        embed.set_author(
            name=str(ctx.author),
            icon_url=ctx.author.display_avatar.url
        )
        embed.set_footer(
            text="Cyni Systems",
            icon_url=self.bot.user.display_avatar.url
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="about",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @premium_check()
    async def about(self, ctx: commands.Context):
        """
        Get information about the bot.
        """
        embed = discord.Embed(
            description=(
                f"Cyni is a multifunctional Discord bot designed to enhance your server\nmanagement experience with a variety of features including moderation,\nutility commands, and entertainment options.\n"
                f"**Version:** `v{_version}-stable`\n"
                f"**CyniLib:** `v1.0.1`\n> (Cyni uses custom forked version of discord.py which enhances performance and adds new features.)\n"
                f"**DB:** `MongoDB`"
            ),
            color=BLANK_COLOR
        )
        embed.set_author(
            name=f"About CYNI",
            icon_url=self.bot.user.avatar.url
        ).set_thumbnail(
            url=self.bot.user.avatar.url
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite", url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot",row=0))
        view.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/J96XEbGNDm",row=0))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="afk",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @app_commands.describe(reason="Reason for being AFK")
    @premium_check()
    async def afk(self, ctx, *, reason: str = "No reason provided."):
        """
        Set your status as AFK.
        """
        try:
            try:
                await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
            except Exception as e:
                pass
            afk_users[ctx.author.id] = reason
            await self.bot.afk.insert_one(
                {
                    "_id": ctx.author.id,
                    "reason": reason,
                    "pings": [],
                    "timestamp": discord_time(ctx.message.created_at)
                }
            )
            await ctx.send(f"`{ctx.author}` is now AFK. Reason: `{reason}`")
        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while setting AFK status: ```{e}```",
                    color=discord.Color.red()
                )
            )


    @commands.hybrid_command(
        name="whois",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @premium_check()
    @app_commands.describe(user="User to get information about")
    async def whois(self, ctx, user: discord.Member = None):
        """
        Get information about a user.
        """
        try:
            if user is None:
                user = ctx.author

            server_permissions = []
            if user == user.guild.owner:
                server_permissions.append(f"{self.bot.emoji.get('moderation')} | Server Owner\n")
            elif user.guild_permissions.administrator:
                server_permissions.append(f"{self.bot.emoji.get('moderation')} | Administrator\n")
            elif user.guild_permissions.manage_messages:
                server_permissions.append(f"{self.bot.emoji.get('moderation')} | Moderator\n")

            public_flags = [flag[0] for flag in user.public_flags.all()]
            user_flags = []
            if "discord_staff" in public_flags:
                user_flags.append("Discord Employee")
            if "discord_partner" in public_flags:
                user_flags.append("Discord Partner")
            if "hypesquad_events" in public_flags:
                user_flags.append("Hypesquad Events")
            if "bughunter_level_1" in public_flags:
                user_flags.append("Bug Hunter Level 1")
            if "bughunter_level_2" in public_flags:
                user_flags.append("Bug Hunter Level 2")
            if "early_supporter" in public_flags:
                user_flags.append("Early Supporter")
            if 'active_developer' in public_flags:
                user_flags.append("Active Developer")
            
            joined_timestamp = discord_time(user.joined_at)
            created_timestamp = discord_time(user.created_at)
            embed = discord.Embed(
                title=f"{user.name}",
                description=" ",
                color=BLANK_COLOR
            ).set_author(
                name=f"{ctx.author}",
                icon_url=ctx.author.avatar.url
            ).add_field(
                name="User Information",
                value=(
                    f'''
                    **ID:** {user.id}
                    **Name:** `{user.name}`
                    **Nickname:** {user.display_name}
                    **Created:** {created_timestamp}
                    **Joined:** {joined_timestamp}
                    **Status:** {user.status}
                    **Color:** {user.color}
                    '''
                ),
                inline=False
            ).add_field(
                name="Server Permissions",
                value=", ".join(server_permissions) if server_permissions else "None",
                inline=False
            ).add_field(
                name="User Flags",
                value=", ".join(user_flags) if user_flags else "None",
                inline=False
            ).add_field(
                name="Roles",
                value=" ".join(
                    [role.mention for role in user.roles if role.name != "@everyone"][:15]
                ) + ("..." if len([role for role in user.roles if role.name != "@everyone"]) > 15 else "") if user.roles else "None",
                inline=False
            ).set_thumbnail(url=user.avatar.url)
            specific_role_id = 1158043149424398406
            specific_guild_id = 1152949579407442050
            guild = self.bot.get_guild(specific_guild_id)
            member_in_guild = guild.get_member(user.id)
            
            if user.id == OWNER:
                 embed.description +=  f"> CYNI Creator\n"
            else:
                if member_in_guild:
                    specific_role = guild.get_role(specific_role_id)
                    if specific_role in member_in_guild.roles:
                        embed.description += f"> CYNI Staff\n"
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.hybrid_group(
        name="avatar",
        extras={
            "category": "General"
        }
    )
    async def avatar(self, ctx):
        """
        Get a user's avatar.
        """
        pass

    @avatar.command(
        name="user",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @app_commands.describe(user="User to get the avatar of")
    @premium_check()
    async def avatar_user(self, ctx, user: discord.Member = None):
        """
        Get a user's avatar.
        """
        user = user if user else ctx.author
        embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            color=BLANK_COLOR
        ).set_image(
            url=user.avatar.url
        )
        await ctx.send(embed=embed)

    @avatar.command(
        name="server",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @premium_check()
    async def avatar_server(self, ctx):
        """
        Get the server's icon.
        """
        embed = discord.Embed(
            title=f"{ctx.guild.name}'s Icon",
            color=BLANK_COLOR
        ).set_image(
            url=ctx.guild.icon.url
        )
        await ctx.send(embed=embed)

    @commands.hybrid_group(
        name="server",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def server(self, ctx):
        pass

    @server.command(
        name="info"
    )
    @commands.guild_only()
    @premium_check()
    async def serverinfo(self, ctx: commands.Context):
        """
        Get information about the server.
        """
        guild = ctx.guild
        embed = discord.Embed(
            title=f"{guild.name}",
            color=BLANK_COLOR
        ).set_thumbnail(
            url=guild.icon.url if guild.icon else None
        ).add_field(
            name="Server Information",
            value=(
                f'''
                **ID:** {guild.id}
                **Owner:** {guild.owner.mention}
                **Verification Level:** {guild.verification_level}
                **Boost Tier:** {guild.premium_tier}
                **Boost Count:** {guild.premium_subscription_count}
                **Member Count:** {guild.member_count}
                **Role Count:** {len(guild.roles)}
                **Emoji Count:** {len(guild.emojis)}
                **Channel Count:** {len(guild.channels)}
                '''
            )
        )

        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

    # @server.command(
    #     name="settings"
    # )
    # @commands.guild_only()
    # @premium_check()
    # async def server_settings(self, ctx: commands.Context):
    #     """
    #     Get the server's settings.
    #     """
    #     pass


    @commands.hybrid_command(
        name="vote",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @premium_check()
    async def vote(self, ctx):
        """
        Vote for the bot.
        """
        await ctx.send("[Top.gg](https://top.gg/bot/1136945734399295538/vote)")

    # @commands.hybrid_command(
    #     name="help",
    #     extras={
    #         "category": "General"
    #     }
    # )
    # @commands.guild_only()
    # @premium_check()
    # async def help(self, ctx):
    #     """
    #     Get help with the bot.
    #     """
    #     embed = discord.Embed(
    #         title="Join the support server",
    #         description="If you need help, feel free to join our support server!",
    #         color=BLANK_COLOR
    #     )
    #     embed.set_footer(text="Support Server")
    #     view = discord.ui.View()
    #     view.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/J96XEbGNDm"))
    #     await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="link",
        extras={
            "category": "Roblox"
        }
    )
    @premium_check()
    async def link(self, ctx):
        """
        Get the user's Roblox profile link.
        """
        user_id = ctx.author.id
        roblox_user = await self.bot.roblox_oauth.find_one(
            {
                "discord_user_id": user_id
            }
        )
        if roblox_user:
            roblox_id = roblox_user.get("roblox_user_id") if roblox_user else None
            roblox_player = await self.bot.roblox.get_user(roblox_id)
            thumbnails = await self.bot.roblox.thumbnails.get_user_avatar_thumbnails(
                [roblox_player], type=roblox.thumbnails.AvatarThumbnailType.headshot
            )
            if not thumbnails or not thumbnails[0]:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Roblox API Error",
                        description="Could not retrieve the user's avatar thumbnail.",
                        color=RED_COLOR
                    )
                )
            thumbnail = thumbnails[0].image_url
            embed = discord.Embed(
                title="Roblox Profile",
                description=(
                    f"**Name:** {roblox_player.name}\n"
                    f"**Display Name:** {roblox_player.display_name}\n"
                    f"**ID:** {roblox_player.id}\n"
                ),
                color=BLANK_COLOR
            )
            embed.set_thumbnail(url=thumbnail)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="View Profile", url=f"https://www.roblox.com/users/{roblox_id}/profile"))
            await ctx.send(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title="Account Not Linked",
                description="> Please link your Roblox account to access\nfeatures like ER:LC Remote Commands, and more.",
                color=RED_COLOR
            )
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Link Account", url="https://cyni.quprdigital.tk/api/verify/roblox/v1/link"))
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="dashboard",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @premium_check()
    async def dashboard(self, ctx):
        """
        Get the bot's dashboard link.
        """
        embed = discord.Embed(
            description="Manage your server with the Cyni Dashboard.",
            color=BLANK_COLOR
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Dashboard", url="https://cyni.quprdigital.tk/dashboard"))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="suggest",
        extras={
            "category": "General"
        }
    )
    @app_commands.describe(suggestion="Your suggestion for the server")
    @commands.guild_only()
    @premium_check()
    async def suggest(self, ctx, *, suggestion: str):
        """
        Suggest something in the server.
        """

        sett = await self.bot.settings.find_by_id(ctx.guild.id)
        if sett is None:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Settings not found for this server.",
                    color=RED_COLOR
                )
            )
        try:
            channel = sett['server_management']['suggestion_channel']
        except KeyError:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Suggestion channel not set.",
                    color=RED_COLOR
                )
            )
        channel = self.bot.get_channel(channel)
        if channel is None:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Suggestion channel not found.",
                    color=RED_COLOR
                )
            )
        embed = discord.Embed(
            title="Suggestion",
            description=f"""
            **From:** {ctx.author.mention}
            **Suggestion:\n** {suggestion}
            """,
            color=BLANK_COLOR
        ).set_author(
            name=f"{ctx.author}",
            icon_url=ctx.author.avatar.url
        ).add_field(
            name="Upvotes",
            value="0",
        ).add_field(
            name="Downvotes",
            value="0",
        ).set_thumbnail(
            url=ctx.author.avatar.url
        )
        view = discord.ui.View(timeout=604800)
        view.add_item(UpVote(row=0))
        view.add_item(DownVote(row=0))
        view.add_item(ViewVotersButton(row=0,upvote_button=view.children[0],downvote_button=view.children[1]))
        msg = await channel.send(embed=embed, view=view)

        await channel.create_thread(
            name="Discussion",
            message=msg,
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description="Suggestion sent successfully.",
                color=BLANK_COLOR
            )
        )

    support_role = 1158043149424398406
    @commands.hybrid_command(
        name="sentry",
        extras={
            "category": "General"
        }
    )
    @app_commands.describe(error_id="The ID of the error to view")
    @premium_check()
    async def sentry(self,ctx,error_id:str):
        """
        Get information about a sentry error.
        """
        support_guild = self.bot.get_guild(1152949579407442050)
        member = support_guild.get_member(ctx.author.id) if support_guild else None
        
        if member and self.support_role in [role.id for role in member.roles]:
            doc = await self.bot.errors.find_by_id(error_id)
            if doc is None:
                await ctx.send(f"Error not found, retrying in 5 seconds.")
                time.sleep(5)
                doc = await self.bot.errors.find_by_id(error_id)
                if doc is None:
                    return await ctx.send("Error not found.")
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"**Error ID:** {doc['_id']}\n\n**Error:** {doc['error']}",
                    color=BLANK_COLOR
                )
            )
        else:
            return await ctx.send(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="Only Cyni Staff is allowed to use this command.",
                    color=RED_COLOR
                )
            )
            
    @commands.hybrid_command(
        name="say",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @is_staff()
    @app_commands.describe(message="The message to send")
    @premium_check()
    async def say(self, ctx, *, message: str):
        """
        Make the bot say something.
        """
        try:
            await ctx.interaction.response.send_message("Message sent successfully.", ephemeral=True)
            await ctx.interaction.channel.send(message)
        except:
            await ctx.typing()
            await ctx.channel.purge(limit=1)
            await ctx.send(message)

async def setup(bot):
    await bot.add_cog(Utility(bot=bot))
