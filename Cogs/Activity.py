import discord
from discord.ext import commands
from utils.utils import log_command_usage


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="activity",
        extras={
            "category": "Activity"
        }
    )
    async def activity(self, ctx):
        """
        Activity commands.
        """
        pass

    @activity.command(
        name="leaderboard",
        extras={
            "category": "Activity"
        }
    )
    async def leaderboard(self, ctx):
        """
        Get the activity leaderboard.
        """
        embed = discord.Embed(
            title="Activity Leaderboard",
            color=0x2F3136
        )
        guild_id = ctx.guild.id
        staff_activity = await self.bot.staff_activity.find_by_id(guild_id)
        if not staff_activity:
            embed.description = "No activity data."
            return await ctx.send(embed=embed)

        staff_activity["staff"] = sorted(staff_activity["staff"], key=lambda x: x["messages"], reverse=True)
        
        for i in range(0, len(staff_activity["staff"]), 25):
            embed.description = ""
            for member in staff_activity["staff"][i:i+25]:
                user = ctx.guild.get_member(member["_id"])
                if user:
                    embed.description += f"> {user.mention}\n<a:animated_arrow:1345685591538401320> {member['messages']} messages\n\n"
            await ctx.send(embed=embed)

    @activity.command(
        name="reset",
        extras={
            "category": "Activity"
        }
    )
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx):
        """
        Reset the activity leaderboard.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,"Activity Reset")
        guild_id = ctx.guild.id
        staff_activity = await self.bot.staff_activity.find_by_id(guild_id)
        if not staff_activity:
            return await ctx.send("No activity data.")
        
        await self.bot.staff_activity.delete(guild_id)
        await ctx.send("Activity data reset.")

    @activity.command(
        name="stats",
        extras={
            "category": "Activity"
        }
    )
    async def stats(self, ctx, member: discord.Member = None):
        """
        Get a member's activity stats.
        """
        if not member:
            member = ctx.author

        guild_id = ctx.guild.id
        staff_activity = await self.bot.staff_activity.find_by_id(guild_id)
        if not staff_activity:
            return await ctx.send("No activity data.")
        
        member_data = None
        for member_ in staff_activity["staff"]:
            if member_["_id"] == member.id:
                member_data = member_
                break
        
        if not member_data:
            return await ctx.send("No activity data for this member.")
        
        embed = discord.Embed(
            title=f"{member}'s Activity Stats",
            color=0x2F3136
        )
        embed.add_field(
            name="Messages",
            value=member_data["messages"]
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Activity(bot))
