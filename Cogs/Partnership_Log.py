import discord
from discord.ext import commands
import time
import asyncio

from utils.constants import YELLOW_COLOR, BLANK_COLOR, RED_COLOR, GREEN_COLOR
from discord import app_commands
from cyni import is_management, is_staff
from utils.utils import log_command_usage
import re
from utils.pagination import Pagination

class Partnership_Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    @is_management()
    @app_commands.describe(title = "Partnership Log Title",)
    @app_commands.describe(description = "Write the description & for new line use \\n\\n")
    @app_commands.describe(representative = "Representative of the partnership")
    @app_commands.describe(image = "Image of the partnership")
    async def log(self, ctx, title: str, *, description: str,invite:str, representative: discord.Member, image: str = None):
        """
        Log a partnership.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,"partnership log")
        sett = await self.bot.settings.find_by_id(ctx.guild.id)
        if not sett:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Settings not found",
                    description = "Please set the settings first",
                    color = RED_COLOR
                )
            )
        try:
            enabled = sett["partnership_module"]["enabled"]
            if not enabled:
                return await ctx.send(
                    embed = discord.Embed(
                        title = "Partnership Module not enabled",
                        description = "Please set the partnership module first",
                        color = RED_COLOR
                    )
                )
        except:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Partnership Module not enabled",
                    description = "Please set the partnership module first",
                    color = RED_COLOR
                )
            )
        try:
            log_channel = self.bot.get_channel(sett["partnership_module"]["partnership_channel"])
        except:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Log Channel not found",
                    description = "Please set the log channel first",
                    color = RED_COLOR
                )
            )
        
        try:
            partner_role = ctx.guild.get_role(sett["partnership_module"]["partner_role"])
        except:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Partner Role not found",
                    description = "Please set the partner role first",
                    color = RED_COLOR
                )
            )
        
        partnership_id = await self.bot.partnership.count_all({})
        partnership_id += 1
        await self.bot.partnership.insert({
            "_id": f"{ctx.guild.id}_{partnership_id}",
            "logged_by": ctx.author.id,
            "title": title,
            "description": description,
            "representative": representative.id,
            "image": image,
            "timestamp": time.time()
        })
        description = re.sub(r'\\n', '\n', description)
        formatted_description = (
            f"{description}\n\n"
            f"Discord Invite: https://discord.gg/{invite}\n"
            f"Representative: {representative.mention}"
        )
        embed = discord.Embed(
            title = title,
            description = formatted_description,
            color = BLANK_COLOR
        ).set_footer(
            text = f"Partnership ID: {partnership_id} | Logged by {ctx.author}",
        )
        if image:
            embed.set_image(url = image)
        await log_channel.send(embed = embed)
        try:
            await representative.add_roles(partner_role, reason = "Partnership Logged")
        except:
            pass
        await ctx.send(
            embed = discord.Embed(
                title = "Partnership Logged",
                description = "The partnership has been logged",
                color = GREEN_COLOR
            ).set_footer(
                text = f"Logged by {ctx.author}",
                icon_url = ctx.author.avatar.url if ctx.author.avatar else " "
            )
        )

    @partnership.command(
        name="all",
        extras={
            "category": "Partnership"
        }
    )
    @is_staff()
    async def all(self, ctx):
        """
        View all partnerships of your server.
        """
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
            description = re.sub(r'\\n', '\n', partnership["description"])
            formatted_description = (
                f"{description}\n\n"
                f"Partner: {partnership['partner']}\n"
                f"Representative: {representative.mention}"
            )
            embed = discord.Embed(
                title=partnership["title"],
                description=formatted_description,
                color=BLANK_COLOR
            ).set_footer(
                text=f"Partnership ID: {partnership['_id']} | Logged by {ctx.guild.get_member(partnership['logged_by'])}",
            )
            if partnership["image"]:
                embed.set_image(url=partnership["image"])
            embeds.append(embed)
        views = [discord.ui.View() for _ in range(len(embeds))]
        view = Pagination(self.bot, ctx.author.id, embeds, views)
        await ctx.send(embed=embeds[0], view=view)

    @partnership.command(
        name="delete",
        extras={
            "category": "Partnership"
        }
    )
    @is_management()
    @app_commands.describe(partnership_id = "ID of the partnership")
    async def delete(self, ctx, partnership_id: int):
        """
        Delete a partnership.
        """
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
        partner_role = ctx.guild.get_role(partnership["partner_role"])
        representative = ctx.guild.get_member(partnership["representative"])
        try:
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

    @partnership.command(
        name="view",
        extras={
            "category": "Partnership"
        }
    )
    @is_staff()
    @app_commands.describe(partnership_id = "ID of the partnership")
    async def view(self, ctx, partnership_id: int):
        """
        View a partnership.
        """
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
            f"Representative: {representative.mention}"
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

async def setup(bot):
    await bot.add_cog(Partnership_Log(bot))