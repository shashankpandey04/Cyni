import discord
from discord.ext import commands
import re
from discord import ui
from utils.pagination import Pagination
from cyni import is_management, premium_check, is_roblox_management
from utils.constants import BLANK_COLOR, RED_COLOR
from utils.utils import log_command_usage

class Sessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def send_embeds(self, ctx):
        try:
            """Fetches embed data from DB and sends all embeds in one message with buttons."""
            # Fetch embed data for this guild using bot's erlc_sessions_embed
            data = await self.bot.erlc_sessions_embed.find_one({"guild_id": ctx.guild.id})
            if not data or "embed" not in data or "embeds" not in data["embed"]:
                await ctx.send("No embed data found.")
                return
            embeds = []
            view = ui.View()
            for embed_dict in data["embed"]["embeds"]:
                color = embed_dict.get("color", "#7289da")
                # Convert hex color to int
                if isinstance(color, str):
                    color = int(re.sub(r"[^0-9a-fA-F]", "", color), 16)
                e = discord.Embed(
                    title=embed_dict.get("title", ""),
                    description=embed_dict.get("description", ""),
                    color=color
                )
                if embed_dict.get("titleUrl"):
                    e.url = embed_dict["titleUrl"]
                author = embed_dict.get("author", {})
                if author.get("name"):
                    e.set_author(name=author["name"], url=author.get("url", discord.Embed.Empty), icon_url=author.get("icon", discord.Embed.Empty))
                if embed_dict.get("thumbnail"):
                    e.set_thumbnail(url=embed_dict["thumbnail"])
                if embed_dict.get("image"):
                    e.set_image(url=embed_dict["image"])
                footer = embed_dict.get("footer", {})
                if footer.get("text"):
                    e.set_footer(text=footer["text"], icon_url=footer.get("icon", discord.Embed.Empty))
                if embed_dict.get("timestamp"):
                    e.timestamp = discord.utils.utcnow()
                for field in embed_dict.get("fields", []):
                    e.add_field(name=field.get("name", ""), value=field.get("value", ""), inline=field.get("inline", False))
                embeds.append(e)
                # Add buttons to view
                for btn in embed_dict.get("buttons", []):
                    view.add_item(ui.Button(label=btn.get("label", "Button"), url=btn.get("url", "")))
            await ctx.send(embeds=embeds, view=view)
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.hybrid_group(
        name="sessions",
        description="Manage user sessions."
    )
    async def sessions(self, ctx: commands.Context):
        pass

    @sessions.command(
        name="post",
        extras={
            "usage": "Usage: /sessions post <user_id>",
            "description": "Post a message in a user's session."
        }
    )
    @is_roblox_management()
    async def post_session(self, ctx: commands.Context, channel: discord.TextChannel):
        try:
            """Fetches embed data from DB and sends all embeds in one message with buttons."""
            # Fetch embed data for this guild using bot's erlc_sessions_embed
            data = await self.bot.erlc_sessions_embed.find_one({"guild_id": ctx.guild.id})
            if not data or "embed" not in data or "embeds" not in data["embed"]:
                await ctx.send("No embed data found.")
                return
            embeds = []
            view = ui.View()
            for embed_dict in data["embed"]["embeds"]:
                color = embed_dict.get("color", "#7289da")
                # Convert hex color to int
                if isinstance(color, str):
                    color = int(re.sub(r"[^0-9a-fA-F]", "", color), 16)
                e = discord.Embed(
                    title=embed_dict.get("title", ""),
                    description=embed_dict.get("description", ""),
                    color=color
                )
                if embed_dict.get("titleUrl"):
                    e.url = embed_dict["titleUrl"]
                author = embed_dict.get("author", {})
                if author.get("name"):
                    e.set_author(name=author["name"], url=author.get("url", discord.Embed.Empty), icon_url=author.get("icon", discord.Embed.Empty))
                if embed_dict.get("thumbnail"):
                    e.set_thumbnail(url=embed_dict["thumbnail"])
                if embed_dict.get("image"):
                    e.set_image(url=embed_dict["image"])
                footer = embed_dict.get("footer", {})
                if footer.get("text"):
                    e.set_footer(text=footer["text"], icon_url=footer.get("icon", discord.Embed.Empty))
                if embed_dict.get("timestamp"):
                    e.timestamp = discord.utils.utcnow()
                for field in embed_dict.get("fields", []):
                    e.add_field(name=field.get("name", ""), value=field.get("value", ""), inline=field.get("inline", False))
                embeds.append(e)
                # Add buttons to view
                for btn in embed_dict.get("buttons", []):
                    view.add_item(ui.Button(label=btn.get("label", "Button"), url=btn.get("url", "")))
            await channel.send(embeds=embeds, view=view)
            return await ctx.send(
                embed=discord.Embed(
                    title="Session Posted",
                    description=f"Message has been posted in {channel.mention}",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await ctx.send(f"Error: {e}")


async def setup(bot):
    await bot.add_cog(Sessions(bot))