import discord
from discord.ext import commands
from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from cyni import is_staff
from discord import app_commands
from utils.utils import log_command_usage
from utils.basic_pager import BasicPager

class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_command(
        name="membercount",
        description="Get the member count of the server.",
    )
    @app_commands.guild_only()
    @is_staff()
    async def membercount(self, ctx: commands.Context):
        """
        Get the member count of the server.
        """
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command can only be used in a server.")
            return
        
        msg = await ctx.send("Calculating member count...")
        member_count = guild.member_count
        embed = discord.Embed(
            title=f"{guild.name}",
            color=ctx.author.top_role.color if ctx.author.top_role.color else BLANK_COLOR
        ).add_field(
            name="Member Count",
            value=member_count,
            inline=False
        ).add_field(
            name="Server Boosts",
            value=guild.premium_subscription_count or 0,
        )
        await msg.edit(content=None, embed=embed)

    @commands.hybrid_group(
        name="members",
        description="Manage members in the server.",
    )
    async def members(self, ctx: commands.Context):
        """
        Manage members in the server.
        """
        pass

    @members.command(
        name="roled",
        description="Get a list of members with a specific role.",
    )
    @app_commands.describe(
        role="The role to get members from.",
        excluded_role="Exclude members with this role (optional)."
    )
    @is_staff()
    async def members_roled(self, ctx: commands.Context, role: discord.Role, excluded_role: discord.Role = None):
        """
        Get a list of members with a specific role, optionally excluding members with another role.
        """
        if not role:
            await ctx.send("Please specify a valid role.")
            return

        members_with_role = role.members
        if excluded_role:
            members_with_role = [member for member in members_with_role if excluded_role not in member.roles]

        member_list = [f"**@{member.name}** (`{member.id}`)" for member in members_with_role]
        if not member_list:
            await ctx.send(
                f"No members found with the role {role.name}" +
                (f" excluding {excluded_role.name}." if excluded_role else ".")
            )
            return

        embeds = [
            discord.Embed(
                title=f"Members with role: {role.name}" + (f" (excluding {excluded_role.name})" if excluded_role else ""),
                description="\n".join(member_list[i:i+45]),
                color=ctx.author.top_role.color if ctx.author.top_role.color else BLANK_COLOR
            )
            for i in range(0, len(member_list), 45)
        ]

        pager = BasicPager(
            user_id=ctx.author.id,
            embeds=embeds
        )
        await ctx.send(embed=embeds[0], view=pager)

async def setup(bot):
    await bot.add_cog(Members(bot))