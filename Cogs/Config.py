import discord
from discord.ext import commands
from menu import BasicConfig, AntiPingView, ModerationModule, StaffInfraction, ServerManagement, PartnershipModule
from utils.pagination import Pagination
from cyni import is_management
from utils.constants import BLANK_COLOR, RED_COLOR
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
        try:
            if isinstance(ctx,commands.Context):
                await log_command_usage(self.bot,ctx.guild,ctx.author,"Config")
        except:
            pass
        try:
            sett = await self.bot.settings.find_by_id(ctx.guild.id)
            if not sett:
                sett = {}
        except KeyError:
            sett = {}
        try:
            embed1 = discord.Embed(
                title="Basic Configuration",
                description="> This is the basic configuration for your server. But what does it do?\n"
                            "> The basic configuration allows you to set the following settings:\n"
                            "> These settings are crucial for the bot to function properly.\n\n"
                            "<:anglesmallright:1268850037861908571> **Staff Role**\n"
                            "- The role that is considered as discord staff and can use Moderation commands and other staff commands.\n\n"
                            "<:anglesmallright:1268850037861908571> **Management Role**\n"
                            "- The role that is considered as discord management and can use Management commands link Staff Infraction, Application Results, Ban Appeal Results, etc.\n\n"
                            "<:anglesmallright:1268850037861908571> **Prefix**\n"
                            "- The prefix that the bot will use for commands."
                            ,
                color=BLANK_COLOR
            )

            embed2 = discord.Embed(
                title="Anti-Ping Module",
                description="> What is Anti-Ping? Anti-Ping prevents users from pinging specific roles.\n"
                            "> To configure Anti-Ping, you need to set the following settings:\n\n"
                            "<:anglesmallright:1268850037861908571> **Anti-Ping Roles**\n"
                            "- These roles clarify the individuals who are affected by Anti-Ping, and are classed as important individuals to Cyni. An individual who pings someone with these affected roles, will activate Anti-Ping.\n\n"
                            "<:anglesmallright:1268850037861908571> **Bypass Roles**\n"
                            "-  An individual who holds one of these roles will not be able to trigger Anti-Ping filters, and will be able to ping any individual within the Affected Roles list without Cyni intervening."
                            ,
                color=BLANK_COLOR
            )

            embed3 = discord.Embed(
                title="Moderation Module",
                description="> What is Moderation module? The moderation module allows you to configure the following settings:\n\n"
                            "<:anglesmallright:1268850037861908571> **Moderation Log Channel**\n"
                            "- The channel where moderation logs will be sent.\n"
                            "<:anglesmallright:1268850037861908571> **Ban Appeal Channel**\n"
                            "- The channel where ban appeals will be sent.\n"
                            "<:anglesmallright:1268850037861908571> **Audit Log Channel**\n"
                            "- The channel where audit logs will be sent like message edits, message deletes, etc.",
                color=BLANK_COLOR
            )

            embed4 = discord.Embed(
                title="Staff Infraction Module",
                description="> What is Staff Management module? The staff management module allows you to configure the following settings:\n"
                            "<:anglesmallright:1268850037861908571> **Promotion Log Channel**\n"
                            "- The channel where staff promotions will be sent.\n\n"
                            "<:anglesmallright:1268850037861908571> **Demotion Log Channel**\n"
                            "- The channel where staff demotions will be sent.\n\n"
                            "<:anglesmallright:1268850037861908571> **Warning Log Channel**\n"
                            "- The channel where staff warnings will be sent like staff strikes and warnings."
                            ,
                color=BLANK_COLOR
            )

            embed5 = discord.Embed(
                title="Server Management Module",
                description="> What is Server Management module? The server management module allows you to configure the following settings:\n\n"
                            "<:anglesmallright:1268850037861908571> **Application Results Channel**\n"
                            "- The channel where application results will be sent.\n\n"
                            "<:anglesmallright:1268850037861908571> **Cyni Logging Channel**\n"
                            "- The channel where Cyni command & config change logs will be sent."
                            "<:anglesmallright:1268850037861908571> **Suggestion Channel**\n"
                            "- The channel where suggestions will be sent and users can vote on them.",
                color=BLANK_COLOR
            )

            embed6 = discord.Embed(
                title="Partnership Module",
                description="> What is Partnership module? The partnership module allows you to configure the following settings:\n\n"
                            "<:anglesmallright:1268850037861908571> **Partnership Module Enabled**\n"
                            "- Enable or disable the partnership module.\n\n"
                            "<:anglesmallright:1268850037861908571> **Partnership Channel**\n"
                            "- The channel where partnership logs will be sent.\n\n"
                            "<:anglesmallright:1268850037861908571> **Partner Role**\n"
                            "- The role that is considered as a partner and automatically given when a partnership is logged."
                            ,
                color=BLANK_COLOR
            )

            all_embed = [embed1, embed2, embed3, embed4, embed5, embed6]
            views = [
                BasicConfig(self.bot, sett, ctx.author.id), 
                AntiPingView(self.bot, sett, ctx.author.id), 
                ModerationModule(bot=self.bot,setting=sett,user_id=ctx.author.id),
                StaffInfraction(bot=self.bot,setting=sett,user_id=ctx.author.id),
                ServerManagement(bot=self.bot,setting=sett,user_id=ctx.author.id),
                PartnershipModule(bot=self.bot,setting=sett,user_id=ctx.author.id)
            ]
            view = Pagination(self.bot, ctx.author.id, all_embed, views)
            await ctx.send(embed=embed1, view=view)

        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Something went wrong",
                    description=f"```{e}```",
                    color=RED_COLOR
                )
            )

async def setup(bot):
    await bot.add_cog(Config(bot))
