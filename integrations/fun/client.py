import discord
from discord.ext import commands


class Fun(commands.Cog):
    """Fun commands."""

    def __init__(self, bot):
        self.bot = bot

    def _base_embed(self, title: str) -> discord.Embed:
        return discord.Embed(
            title=title,
            color=discord.Color.blurple(),
        ).set_footer(text="CYNI | Fun Commands")

    @commands.hybrid_command(
        name="joke",
        description="Get a random joke.",
        extras={"category": "Fun"},
    )
    @commands.guild_only()
    async def joke(self, ctx: commands.Context):
        await ctx.defer()

        response = await self.bot.http_client.get(
            "https://official-joke-api.appspot.com/random_joke"
        )
        response.raise_for_status()

        data = response.json()

        embed = self._base_embed("😂 Random Joke")
        embed.add_field(
            name="Setup",
            value=data["setup"],
            inline=False,
        )
        embed.add_field(
            name="Punchline",
            value=data["punchline"],
            inline=False,
        )

        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="dog",
        description="Get a random dog image.",
        extras={"category": "Fun"},
    )
    @commands.guild_only()
    async def dog(self, ctx: commands.Context):
        await ctx.defer()

        response = await self.bot.http_client.get(
            "https://dog.ceo/api/breeds/image/random"
        )
        response.raise_for_status()

        data = response.json()

        embed = self._base_embed("🐶 Random Dog")
        embed.set_image(url=data["message"])

        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="cat",
        description="Get a random cat image.",
        extras={"category": "Fun"},
    )
    @commands.guild_only()
    async def cat(self, ctx: commands.Context):
        await ctx.defer()

        response = await self.bot.http_client.get(
            "https://api.thecatapi.com/v1/images/search"
        )
        response.raise_for_status()

        data = response.json()

        embed = self._base_embed("🐱 Random Cat")
        embed.set_image(url=data[0]["url"])

        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="meow",
        description="Get a random cat fact.",
        extras={"category": "Fun"},
    )
    @commands.guild_only()
    async def meow(self, ctx: commands.Context):
        await ctx.defer()

        response = await self.bot.http_client.get("https://meowfacts.herokuapp.com/")
        response.raise_for_status()

        data = response.json()

        embed = self._base_embed("🐾 Cat Fact")
        embed.description = f"> {data['data'][0]}"

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
