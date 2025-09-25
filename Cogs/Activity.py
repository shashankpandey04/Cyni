import discord
from discord.ext import commands
from utils.utils import log_command_usage
from cyni import is_management, is_staff, premium_check
from Views.MessageQuota import MessageQuotaManager
from utils.basic_pager import BasicPager

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
    @is_staff()
    @premium_check()
    @commands.guild_only()
    async def leaderboard(self, ctx):
        """
        Get the activity leaderboard.
        """
        try:
            embeds = []
            embed = discord.Embed(
                title="Activity Leaderboard",
                color=0x2F3136
            )
            guild_id = ctx.guild.id
            staff_activity = await self.bot.staff_activity.find_by_id(guild_id)
            if not staff_activity:
                embed.description = "No activity data."
                embeds.append(embed)
                return await ctx.send(embed=embed)
    
            quota_doc = await self.bot.message_quotas.find_by_id(guild_id)
    
            staff_activity["staff"] = sorted(staff_activity["staff"], key=lambda x: x["messages"], reverse=True)
    
            embed.description = ""
            for idx, member in enumerate(staff_activity["staff"], start=1):
                user = ctx.guild.get_member(member["_id"])
                if user:
                    is_loa = await self.bot.loa.find_one(
                        {"guild_id": guild_id, "user_id": user.id, "active": True}
                    )
                    quota_met = False
                    if quota_doc:
                        for quota_name, quota_data in quota_doc.items():
                            if quota_name != "_id" and quota_data["role_id"] in [role.id for role in user.roles]:
                                if member["messages"] >= quota_data["quota"]:
                                    quota_met = True
                                    break
    
                    status_emoji = "🟢" if quota_met else "🔴"
                    loa_text = "LOA " if is_loa else ""
                    embed.description += (
                        f"**#{idx}** {status_emoji} {loa_text}{user.mention}\n"
                        f"> **{member['messages']}** messages\n\n"
                    )
    
                if idx % 25 == 0:
                    embeds.append(embed)
                    embed = discord.Embed(
                    title="Activity Leaderboard (Continued)",
                    color=0x2F3136
                    )
                    embed.description = ""
    
            if embed.description:
                embeds.append(embed)
    
            pager = BasicPager(
                user_id=ctx.author.id,
                embeds=embeds
            )
            await ctx.send(embed=embeds[0], view=pager)
        except Exception as e:
            return await ctx.reply(
                embed=discord.Embed(
                    title="Error Occured",
                    description=f"Error Details: ```{e}```",
                    color = 0x2F3136
                )
            )
    
    @activity.command(
        name="reset",
        extras={
            "category": "Activity"
        }
    )
    @is_management()
    @premium_check()
    @commands.guild_only()
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

        await self.bot.staff_activity.delete_many({"_id": guild_id})
        await ctx.send(
            embed=discord.Embed(
                title="Activity Data Reset",
                description="All activity data has been reset.",
                color=0x2F3136
            )
        )

    @activity.command(
        name="stats",
        extras={
            "category": "Activity"
        }
    )
    @is_staff()
    @premium_check()
    @commands.guild_only()
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

    @activity.command(
        name="config",
        extras={
            "category": "Activity"
        }
    )
    @is_management()
    @premium_check()
    @commands.guild_only()
    async def config(self, ctx):
        """
        Manage message quotas.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,"Activity Config")
        view = MessageQuotaManager(self.bot, ctx)
        embed = discord.Embed(
            title="Message Quota Management",
            description="Manage message quotas for your server.",
            color=0x2F3136
        )
        doc = await self.bot.message_quotas.find_by_id(ctx.guild.id)
        if not doc or len(doc) == 1:  # Only _id field exists
            embed.description = "> No message quotas found."
        else:
            # the doc structure is like this:
            # {
            #     "_id": guild_id,
            #     "quota_name_1": {
            #         "role_id": int,
            #         "quota": int 
            #     },
            #     "quota_name_2": {
            #         "role_id": int,
            #         "quota": int
            #     }
            #     ...
            # }
            for key in doc:
                if key != "_id":
                    quota = doc[key]
                    role = ctx.guild.get_role(quota["role_id"])
                    role_name = role.name if role else "Role not found"
                    embed.add_field(
                        name=f"Quota: `{key}`",
                        value=f"> Role: `{role_name}`\n> Quota: `{quota['quota']}` messages",
                        inline=False
                    )
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Activity(bot))
