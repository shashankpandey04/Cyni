import discord
from discord.ext import commands

OWNER = 1201129677457215558
LOGGING_CHANNEL = 1257705346525560885


class Others(commands.Cog):
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
        await ctx.send(f"🟢 Pong! {round(self.bot.latency * 1000)}ms")

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
            description="A multipurpose Discord bot.",
            color=0x2A2D31
        )
        embed.add_field(
            name="Creator",
            value=f"<@{OWNER}>",
            inline=False
        )
        embed.add_field(
            name="Library",
            value="discord.py",
            inline=False
        )
        embed.add_field(
            name="Source Code",
            value="[GitHub](https://www.github.com/shashankpandey04/cyni)",
            inline=False
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite", url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot",row=0))
        view.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/J96XEbGNDm",row=0))
        embed.set_footer(text="Cyni v7", icon_url=ctx.guild.icon)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Others(bot=bot))