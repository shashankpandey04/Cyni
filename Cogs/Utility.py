import discord
from discord.ext import commands

from cyni import afk_users
from utils.constants import BLANK_COLOR
from utils.utils import discord_time
from cyni import up_time

OWNER = 1201129677457215558
LOGGING_CHANNEL = 1257705346525560885


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        extras={
            "category": "General"
        }
    )
    async def ping(self, ctx):
        """
        Get the bot's latency.
        """
        await ctx.send(f"<:serveronline:1268850002768171098> Pong! {round(self.bot.latency * 1000)}ms")

    @commands.hybrid_command(
        name="about",
        extras={
            "category": "General"
        }
    )
    async def about(self, ctx):
        """
        Get information about the bot.
        """
        embed = discord.Embed(
            title="Cyni",
            description=f"A multipurpose Discord bot.\n**<:serveronline:1268850002768171098> Uptime:** {up_time}\n**Latency:** {round(self.bot.latency * 1000)}ms\n**Servers:** {len(self.bot.guilds)}\n**Users:** {len(self.bot.users)}\n**Library:** discord.py\n**Creator:** <@{OWNER}>,\n**Version:** v7.1",
            color=BLANK_COLOR
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
    async def afk(self, ctx, *, reason: str = "No reason provided."):
        """
        Set your status as AFK.
        """
        await ctx.send(f"`{ctx.author}` is now AFK. Reason: {reason}")
        try:
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
        except discord.Forbidden:
            pass
        afk_users[ctx.author.id] = reason


    @commands.hybrid_command(
        name="whois",
        extras={
            "category": "General"
        }
    )
    async def whois(self, ctx, user: discord.Member = None):
        """
        Get information about a user.
        """
        try:
            if user is None:
                user = ctx.author

            server_permissions = []
            if user.guild.owner:
                server_permissions.append("<:moderation:1268850116798844969> Server Owner")
            elif user.guild_permissions.administrator:
                server_permissions.append("<:moderation:1268850116798844969> Administrator")
            elif user.guild_permissions.manage_messages:
                server_permissions.append("<:moderation:1268850116798844969> Moderator")

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
            status = user.status
            if status == discord.Status.online:
                status = "Online"
            elif status == discord.Status.idle:
                status = "Idle"
            elif status == discord.Status.dnd:
                status = "Do Not Disturb"
            elif status == discord.Status.offline:
                status = "Offline"
            embed = discord.Embed(
                title=f"{user.name}",
                description= " ",
                color=BLANK_COLOR
            ).set_author(
                name=f"{ctx.author}",
                icon_url=ctx.author.avatar.url
            ).add_field(
                name="User Information",
                value=f'''**Mention:** {user.mention}\n**Nickname:** {user.display_name}\n**Status:** {status}\n**Joined Server Timestamp:** {joined_timestamp}\n**Created Account Timestamp:** {created_timestamp}''',
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
                value=", ".join([role.mention for role in user.roles[1:]]) if user.roles[1:] else "None",
                inline=False
            ).set_thumbnail(url=user.avatar.url)
            specific_role_id = 1158043149424398406
            specific_guild_id = 1152949579407442050
            guild = self.bot.get_guild(specific_guild_id)
            member_in_guild = guild.get_member(user.id)
            if member_in_guild:
                specific_role = guild.get_role(specific_role_id)
                if specific_role in member_in_guild.roles:
                    embed.description += f"<:cyniverified:1269139230911893534> Cyni Staff"
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

    @commands.hybrid_command(
        name="serverinfo",
        extras={
            "category": "General"
        }
    )
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
            value=f'''
                **ID:** {guild.id}
                **Owner:** {guild.owner.mention}
                **Verification Level:** {guild.verification_level}
                **Boost Tier:** {guild.premium_tier}
                **Boost Count:** {guild.premium_subscription_count}
                **Member Count:** {guild.member_count}
                **Role Count:** {len(guild.roles)}
                **Emoji Count:** {len(guild.emojis)}
                **Channel Count:** {len(guild.channels)}'''
        )

        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="invite",
        extras={
            "category": "General"
        }
    )
    async def invite(self, ctx):
        """
        Get the bot's invite link.
        """
        await ctx.send(f"Invite me to your server: https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot")

    @commands.hybrid_command(
        name="patreon",
        extras={
            "category": "General"
        }
    )
    async def patreon(self, ctx):
        """
        Get the bot's Patreon link.
        """
        await ctx.send("[Patreon](https://www.patreon.com/CodingNerd04)")

    @commands.hybrid_command(
        name="vote",
        extras={
            "category": "General"
        }
    )
    async def vote(self, ctx):
        """
        Vote for the bot.
        """
        await ctx.send("[Top.gg](https://top.gg/bot/1136945734399295538/vote)")

    @commands.hybrid_command(
        name="help",
        extras={
            "category": "General"
        }
    )
    async def help(self, ctx):
        """
        Get help with the bot.
        """
        await ctx.send("Join the support server for help: https://discord.gg/J96XEbGNDm")

    @commands.hybrid_command(
        name="dashboard",
        extras={
            "category": "General"
        }
    )
    async def dashboard(self, ctx):
        """
        Get the bot's dashboard link.
        """
        await ctx.send("Cyni Dashboard is under development!\n[Dashboard](https://cyni.tg1cre.easypanel.host/)")
    
async def setup(bot):
    await bot.add_cog(Utility(bot=bot))