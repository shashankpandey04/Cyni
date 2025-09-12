import discord
from discord.ext import commands
import time

from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR
from discord import app_commands
from cyni import is_management, is_staff, premium_check
from utils.utils import log_command_usage
import re
from utils.pagination import Pagination
from Views.PartnershipModule import PartnershipLogView

class Partnership_Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _log_partnership(self):
        pass

    @commands.hybrid_group(
        name="partnership",
        extras={
            "category": "Partnership"
        }
    )
    async def partnership(self, ctx):
        pass

    @partnership.command(
        name="log",
        extras={
            "category": "Partnership"
        }
    )
    @is_staff()
    @commands.guild_only()
    @premium_check()
    async def log(self, ctx):
        """
        Log a partnership for your server.
        """
        try:
            if isinstance(ctx, commands.Context):
                await log_command_usage(self.bot, ctx.guild, ctx.author, "partnership log")
            
            sett = await self.bot.settings.find_by_id(ctx.guild.id)
            if not sett or not sett.get("partnership_module", {}).get("enabled"):
                return await ctx.send(
                    embed=discord.Embed(
                        title="Partnership Module not enabled",
                        description="Please ensure the partnership module is enabled and settings are configured.",
                        color=RED_COLOR
                    )
                )
            
            log_channel_id = sett["partnership_module"].get("partnership_channel")
            log_channel = self.bot.get_channel(log_channel_id) if log_channel_id else None
            if not log_channel:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Log Channel not found",
                        description="Please set the log channel in the settings.",
                        color=RED_COLOR
                    )
                )

            embed = discord.Embed(
                title="Your Partnership Log is being created!",
                description=" ",
                color=BLANK_COLOR
            )
            partnership_id = await self.bot.partnership.count_all({})
            partnership_id += 1
            await ctx.send(embed=embed, view=PartnershipLogView(self.bot, ctx, partnership_id))
            
        except Exception as e:
            await ctx.send(
                embed = discord.Embed(
                    title = "Error",
                    description = str(e),
                    color = RED_COLOR
                )
            )

    @partnership.command(
        name="all",
        extras={
            "category": "Partnership"
        }
    )
    @is_staff()
    @commands.guild_only()
    @premium_check()
    async def all(self, ctx):
        """
        View all partnerships of your server.
        """
        try:
            if isinstance(ctx, commands.Context):
                await log_command_usage(self.bot, ctx.guild, ctx.author, "partnership all")
            partnerships = await self.bot.partnership.search_id(f"{ctx.guild.id}_")
            if not partnerships:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Partnerships not found",
                        description="No partnerships were found",
                        color=RED_COLOR
                    )
                )
            partnerships = sorted(partnerships, key=lambda x: x["timestamp"], reverse=True)
            embeds = []
            for partnership in partnerships:
                representative = ctx.guild.get_member(partnership["representative"])
                if not representative:
                    representative = await self.bot.fetch_user(partnership["representative"])
                description = re.sub(r'\\n', '\n', partnership["description"])
                formatted_description = (
                    f"{description}\n\n"
                    f"Representative: {representative.mention if representative else 'Couldn\'t find the representative'}"
                )
                partnership_id = partnership["_id"].split("_")[1]
                embed = discord.Embed(
                    title=partnership["title"],
                    description=formatted_description,
                    color=BLANK_COLOR
                ).set_footer(
                    text=f"Partnership ID: {partnership_id} | Logged by {ctx.guild.get_member(partnership['logged_by'])}",
                )
                if partnership["image"]:
                    embed.set_image(url=partnership["image"])
                embeds.append(embed)
            views = [discord.ui.View() for _ in range(len(embeds))]
            view = Pagination(self.bot, ctx.author.id, embeds, views)
            await ctx.send(embed=embeds[0], view=view)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=str(e),
                    color=RED_COLOR
                )
            )

    @partnership.command(
        name="delete",
        extras={
            "category": "Partnership"
        }
    )
    @is_management()
    @premium_check()
    @commands.guild_only()
    @app_commands.describe(partnership_id = "ID of the partnership")
    async def delete(self, ctx, partnership_id: int):
        """
        Delete a partnership.
        """
        try:
            if isinstance(ctx,commands.Context):
                await log_command_usage(self.bot,ctx.guild,ctx.author,"partnership delete")
            partnership = await self.bot.partnership.find_by_id(f"{ctx.guild.id}_{partnership_id}")
            if not partnership:
                return await ctx.send(
                    embed = discord.Embed(
                        title = "Partnership not found",
                        description = "The partnership with the specified ID was not found",
                        color = RED_COLOR
                    )
                )
            partner_role = ctx.guild.get_role(partnership["partner_role"], default = None)
            representative = ctx.guild.get_member(partnership["representative"], default = None)
            try:
                if partner_role:
                    await representative.remove_roles(partner_role, reason = "Partnership Deleted")
            except:
                pass
            await self.bot.partnership.delete_by_id(f"{ctx.guild.id}_{partnership_id}")
            await ctx.send(
                embed = discord.Embed(
                    title = "Partnership Deleted",
                    description = "The partnership has been deleted",
                    color = GREEN_COLOR
                ).set_footer(
                    text = f"Deleted by {ctx.author}",
                    icon_url = ctx.author.avatar.url if ctx.author.avatar else " "
                )
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=str(e),
                    color=RED_COLOR
                )
            )

    @partnership.command(
        name="view",
        extras={
            "category": "Partnership"
        }
    )
    @is_staff()
    @app_commands.describe(partnership_id = "ID of the partnership")
    @commands.guild_only()
    @premium_check()
    async def view(self, ctx, partnership_id: int):
        """
        View a partnership.
        """
        try:
            if isinstance(ctx,commands.Context):
                await log_command_usage(self.bot,ctx.guild,ctx.author,"partnership view")
            partnership = await self.bot.partnership.find_by_id(f"{ctx.guild.id}_{partnership_id}")
            if not partnership:
                return await ctx.send(
                    embed = discord.Embed(
                        title = "Partnership not found",
                        description = "The partnership with the specified ID was not found",
                        color = RED_COLOR
                    )
                )
            representative = ctx.guild.get_member(partnership["representative"])
            description = re.sub(r'\\n', '\n', partnership["description"])
            formatted_description = (
                f"{description}\n\n"
                f"Representative: {representative.mention}\n"
                f"Timestamp: <t:{int(partnership['timestamp'])}:R>\n"
            )
            embed = discord.Embed(
                title = partnership["title"],
                description = formatted_description,
                color = BLANK_COLOR
            ).set_footer(
                text = f"Partnership ID: {partnership_id} | Logged by {ctx.guild.get_member(partnership['logged_by'])}",
            )
            if partnership["image"]:
                embed.set_image(url = partnership["image"])
            await ctx.send(embed = embed)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=str(e),
                    color=RED_COLOR
                )
            )


    @partnership.command(
        name="byuser",
        extras={
            "category": "Partnership"
        }
    )
    @is_staff()
    @app_commands.describe(user = "User to view partnerships of")
    @commands.guild_only()
    @premium_check()
    async def byuser(self, ctx, user: discord.Member):
        """
        View all partnerships of a representative.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,"partnership byuser")
        partnerships = await self.bot.partnership.find(
            {
                "representative": user.id,
                "_id": {"$regex": f"{ctx.guild.id}_"}
            }
        )
        if not partnerships:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Partnerships not found",
                    description = "No partnerships were found",
                    color = RED_COLOR
                )
            )
        partnerships = sorted(partnerships, key=lambda x: x["timestamp"], reverse=True)
        embeds = []
        
        summary_embed = discord.Embed(
            title = f"Partnership Summary for {user.name}",
            description = f"Total Partnerships: {len(partnerships)}\nMost Recent: {partnerships[0]['title']}\nOldest: {partnerships[-1]['title']}",
            color = BLANK_COLOR
        ).set_footer(
            text = "CYNI Partnership Log",
            icon_url = self.bot.user.avatar.url if self.bot.user.avatar else " "
        )
        embeds.append(summary_embed)

        for partnership in partnerships:
            description = re.sub(r'\\n', '\n', partnership["description"])
            formatted_description = (
                f"{description}\n\n"
                f"Representative: {user.mention}"
            )
            embed = discord.Embed(
                title = partnership["title"],
                description = formatted_description,
                color = BLANK_COLOR
            ).set_footer(
                text = f"Partnership ID: {partnership['_id']} | Logged by {ctx.guild.get_member(partnership['logged_by'])}",
            )
            if partnership["image"]:
                embed.set_image(url = partnership["image"])
            embeds.append(embed)
            
        views = [discord.ui.View() for _ in range(len(embeds))]
        view = Pagination(self.bot, ctx.author.id, embeds, views)
        await ctx.send(embed=embeds[0], view=view)

    @partnership.command(
        name="repost",
        extras={
            "category": "Partnership"
        }
    )
    @is_staff()
    @app_commands.describe(partnership_id = "ID of the partnership")
    @commands.guild_only()
    @premium_check()
    async def repost(self, ctx, partnership_id: int):
        """
        Repost a partnership to the partnership channel.
        """
        try:
            if isinstance(ctx,commands.Context):
                await log_command_usage(self.bot,ctx.guild,ctx.author,"partnership repost")
            # doc = {
            #     "_id": f"{ctx.guild.id}_{partnership_id}",
            #     "logged_by": ctx.author.id,
            #     "title": None,
            #     "message": None,
            #     "description": None,
            #     "representative": None,
            #     "other_representatives": [],
            #     "image": None,
            #     "thumbnail": None,
            #     "timestamp": None,
            #     "fields": [],
            #     "footer": None,
            #     "color": discord.Color.blue().value
            # }

            partnership = await self.bot.partnership.find_by_id(f"{ctx.guild.id}_{partnership_id}")
            if not partnership:
                return await ctx.send(
                    embed = discord.Embed(
                        title = "Partnership not found",
                        description = "The partnership with the specified ID was not found",
                        color = RED_COLOR
                    )
                )
            sett = await self.bot.settings.find_by_id(ctx.guild.id)
            if not sett or not sett.get("partnership_module", {}).get("enabled"):
                return await ctx.send(
                    embed=discord.Embed(
                        title="Partnership Module not enabled",
                        description="Please ensure the partnership module is enabled and settings are configured.",
                        color=RED_COLOR
                    )
                )
            log_channel_id = sett["partnership_module"].get("partnership_channel")
            log_channel = self.bot.get_channel(log_channel_id) if log_channel_id else None

            if not log_channel:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Log Channel not found",
                        description="The log channel for partnerships is not configured.",
                        color=RED_COLOR
                    )
                )
            representative = ctx.guild.get_member(partnership["representative"])
            try:
                embed = discord.Embed(
                    title = partnership["title"],
                    description=partnership["description"],
                    color = discord.Color(int(partnership["color"].lstrip('#'), 16))
                )
            except:
                embed = discord.Embed(
                    title = partnership["title"],
                    description=partnership["description"],
                    color = BLANK_COLOR
                )
            if partnership["image"]:
                embed.set_image(url = partnership["image"])
            if partnership["thumbnail"]:
                embed.set_thumbnail(url = partnership["thumbnail"])
            if partnership["footer"]:
                embed.set_footer(text = partnership["footer"])
            for field in partnership["fields"]:
                embed.add_field(name = field["name"], value = field["value"], inline = field.get("inline", False))
            embed.add_field(name = "Representative", value = representative.mention if representative else "Couldn't find the representative", inline = False)
            embed.set_footer(text = f"Partnership ID: {partnership_id} | Logged by {ctx.guild.get_member(partnership['logged_by'])}")
            await log_channel.send(embed = embed)
            await ctx.send(
                embed = discord.Embed(
                    title = "Partnership Reposted",
                    description = f"The partnership has been reposted to {log_channel.mention}",
                    color = discord.Color.green()
                )
            )

        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=str(e),
                    color=RED_COLOR
                )
            )

async def setup(bot):
    await bot.add_cog(Partnership_Log(bot))