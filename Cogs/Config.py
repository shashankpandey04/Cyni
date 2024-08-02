import discord
from discord.ext import commands
from menu import BasicConfig, AntiPingView, ModerationModule, StaffInfraction, ServerManagement
from utils.pagination import Pagination
from cyni import is_management
from utils.constants import BLANK_COLOR
from utils.utils import log_command_usage
class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="config",
        aliases=["settings"],
        extras={
            "category": "Settings"
        }
    )
    @commands.guild_only()
    @is_management()
    async def config(self, ctx):
        """
        Configure your server settings.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,"Config")
        try:
            sett = await self.bot.settings.find_by_id(ctx.guild.id)
            if not sett:
                sett = {}
        except KeyError:
            sett = {}
        try:
            anti_ping_enabled = sett["anti_ping_module"]["enabled"]
        except:
            anti_ping_enabled = False
        try:
            moderation_enabled = sett["moderation_module"]["enabled"]
        except KeyError:
            moderation_enabled = False
        try:
            staff_management_enabled = sett["staff_management"]["enabled"]
        except KeyError:
            staff_management_enabled = False
        try:
            server_management_enabled = sett["server_management_module"]["enabled"]
        except KeyError:
            server_management_enabled = False
        try:
            embed1 = discord.Embed(
                title="Basic Configuration",
                description="> This is the basic configuration for your server. But what does it do?\n"
                            "> The basic configuration allows you to set the following settings:\n"
                            "> These settings are crucial for the bot to function properly.\n\n"
                            "<:anglesmallright:1265660647849463829> **Staff Role**\n"
                            "- The role that is considered as discord staff and can use Moderation commands and other staff commands.\n\n"
                            "<:anglesmallright:1265660647849463829> **Management Role**\n"
                            "- The role that is considered as discord management and can use Management commands link Staff Infraction, Application Results, Ban Appeal Results, etc.\n\n"
                            "<:anglesmallright:1265660647849463829> **Prefix**\n"
                            "- The prefix that the bot will use for commands."
                            ,
                color=BLANK_COLOR
            )
            embed2 = discord.Embed(
                title="Anti-Ping Module",
                description="> What is Anti-Ping? Anti-Ping prevents users from pinging specific roles.\n"
                            "> To configure Anti-Ping, you need to set the following settings:\n\n"
                            "<:anglesmallright:1265660647849463829> **Anti-Ping Roles**\n"
                            "- These roles clarify the individuals who are affected by Anti-Ping, and are classed as important individuals to Cyni. An individual who pings someone with these affected roles, will activate Anti-Ping.\n\n"
                            "<:anglesmallright:1265660647849463829> **Bypass Roles**\n"
                            "-  An individual who holds one of these roles will not be able to trigger Anti-Ping filters, and will be able to ping any individual within the Affected Roles list without Cyni intervening."
                            ,
                color=BLANK_COLOR
            ).add_field(
                name="Enable/Disable Anti-Ping Module",
                value = f"{{{'Enabled' if anti_ping_enabled else 'Disabled'}}}"
            )
            embed3 = discord.Embed(
                title="Moderation Module",
                description="> What is Moderation module? The moderation module allows you to configure the following settings:\n\n"
                            "<:anglesmallright:1265660647849463829> **Moderation Log Channel**\n"
                            "- The channel where moderation logs will be sent.\n"
                            "<:anglesmallright:1265660647849463829> **Ban Appeal Channel**\n"
                            "- The channel where ban appeals will be sent.\n"
                            "<:anglesmallright:1265660647849463829> **Audit Log Channel**\n"
                            "- The channel where audit logs will be sent like message edits, message deletes, etc.",
                color=BLANK_COLOR
            ).add_field(
                name="Enable/Disable Moderation Module",
                value = f"{{{'Enabled' if moderation_enabled else 'Disabled'}}}"
            )
            embed4 = discord.Embed(
                title="Staff Infraction Module",
                description="> What is Staff Management module? The staff management module allows you to configure the following settings:\n"
                            "<:anglesmallright:1265660647849463829> **Promotion Log Channel**\n"
                            "- The channel where staff promotions will be sent.\n\n"
                            "<:anglesmallright:1265660647849463829> **Demotion Log Channel**\n"
                            "- The channel where staff demotions will be sent.\n\n"
                            "<:anglesmallright:1265660647849463829> **Warning Log Channel**\n"
                            "- The channel where staff warnings will be sent like staff strikes and warnings."
                            ,
                color=BLANK_COLOR
            ).add_field(
                name="Enable/Disable Staff Infraction Module",
                value = f"{{{'Enabled' if staff_management_enabled else 'Disabled'}}}"
            )
            embed5 = discord.Embed(
                title="Server Management Module",
                description="> What is Server Management module? The server management module allows you to configure the following settings:\n\n"
                            "<:anglesmallright:1265660647849463829> **Application Results Channel**\n"
                            "- The channel where application results will be sent.\n\n"
                            "<:anglesmallright:1265660647849463829> **Cyni Logging Channel**\n"
                            "- The channel where Cyni command & config change logs will be sent.",
                color=BLANK_COLOR
            ).add_field(
                name="Enable/Disable Server Management Module",
                value = f"{{{'Enabled' if server_management_enabled else 'Disabled'}}}"
            )
            all_embed = [embed1, embed2, embed3, embed4, embed5]
            views = [
                BasicConfig(self.bot, sett, ctx.author.id), 
                AntiPingView(self.bot, sett, ctx.author.id), 
                ModerationModule(bot=self.bot,setting=sett,user_id=ctx.author.id),
                StaffInfraction(bot=self.bot,setting=sett,user_id=ctx.author.id),
                ServerManagement(bot=self.bot,setting=sett,user_id=ctx.author.id)
            ]
            view = Pagination(self.bot, ctx.author.id, all_embed, views)
            await ctx.send(embed=embed1, view=view)

        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(Config(bot))
