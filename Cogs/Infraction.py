import discord
from discord.ext import commands
from utils.constants import BLANK_COLOR, RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from utils.autocompletes import infraction_autocomplete, dm_autocomplete
from cyni import is_management
from discord import app_commands
from utils.utils import log_command_usage

class Infraction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="infraction",
        extras={
            "category": "Infraction"
        }
    )
    async def infraction(self, ctx):
        """
        Staff commands.
        """
        pass
        
    @infraction.command(
        name="post",
        extras={
            "category": "Infraction"
        }
    )
    @is_management()
    @app_commands.autocomplete(
        type=infraction_autocomplete
    )
    @app_commands.autocomplete(
        dm=dm_autocomplete
    )
    async def staff_infract(self,ctx,member:discord.Member, type:str,approver:discord.Role,*,reason:str,rank:str,punishment:str = None,role_remove:discord.Role = None,role_add:discord.Role = None, dm: str = "false"):
        '''
        Warn, demote or promote a staff member.
        '''
        await ctx.typing()
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,f"Staff Infraction for {member}")
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if settings is None:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Error",
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )        
        try:
            enabled = settings['staff_management']["enabled"]
            if not enabled:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Module not enabled",
                        description="Please enable Staff Management Module via `/modules` command.",
                        color=BLANK_COLOR
                    )
                )
        except KeyError:
            return await ctx.send(
                    embed=discord.Embed(
                        title="Module not enabled",
                        description="Please enable Staff Management Module via `/modules` command.",
                        color=BLANK_COLOR
                    )
                )
        
        count = await self.bot.infraction_log.count_all(
            {"guild_id": ctx.guild.id}
        )
        infract_embed = discord.Embed(
            title = f"{member} have got {type}.",
            description=" ",
        )
        if role_remove != None:
            await member.remove_roles(role_remove)
        if role_add != None:
            await member.add_roles(role_add)
        
        if approver is not None:
            infract_embed.description += f"\n**Approved by:** {approver}"

        if punishment is not None:
            infract_embed.description += f"\n**Punishment:** {punishment}"

        if reason is not None:
            infract_embed.description += f"\n**Reason:** {reason}"
        
        if rank is not None:
            infract_embed.description += f"\n**Rank:** {rank}"
        
        infract_embed.set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url
        ).set_thumbnail(
            url=member.avatar.url
        ).set_footer(
            text=f"Infraction Case: {count + 1}"
        )

        infraction_doc = {
            "guild_id": ctx.guild.id,
            "member_id": member.id,
            "type": type,
            "approver_id": approver.id,
            "reason": reason,
            "rank": rank,
            "punishment": punishment,
            "date": ctx.message.created_at.strftime("%d %b %Y %H:%M:%S"),
            "case": count + 1
        }

        await self.bot.infraction_log.insert_doc(infraction_doc)

        if type == "warning":
            infract_embed.color = YELLOW_COLOR
            warning_channel = settings["staff_management"]["warning_channel"]
            if warning_channel:
                channel = ctx.guild.get_channel(warning_channel)
                if channel:
                    await channel.send(member.mention ,embed=infract_embed)
                    await ctx.send(
                        embed = discord.Embed(
                            title = "Success",
                            description = f"{member} has been warned.",
                            color = BLANK_COLOR
                        )
                    )
                else:
                    await ctx.send(member.mention,
                        embed = discord.Embed(
                            title = "Error",
                            description = "Staff Warning Log channel not found.",
                            color = RED_COLOR
                        )
                    )
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Channel not setuped",
                        description="Please select Staff Warning Log channel via `/config` command from Staff Management Page.",
                        color = RED_COLOR
                    )
                )
        elif type == "demotion":
            infract_embed.color = RED_COLOR
            demotion_channel = settings["staff_management"]["demotion_channel"]
            if demotion_channel:
                channel = ctx.guild.get_channel(demotion_channel)
                if channel:
                    await channel.send(member.mention, embed=infract_embed)
                    await ctx.send(
                        embed = discord.Embed(
                            title = "Success",
                            description = f"{member} has been demoted.",
                            color = BLANK_COLOR
                        )
                    )
                else:
                    await ctx.send(member.mention,
                        embed = discord.Embed(
                            title = "Error",
                            description = f"Demotion channel not found.",
                            color = RED_COLOR
                        )
                    )
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Channel not setuped",
                        description="Please select Staff Demotion Log channel via `/config` command from Staff Management Page.",
                        color = RED_COLOR
                    )
                )
        elif type == "promotion":
            infract_embed.color = GREEN_COLOR
            promotion_channel = settings["staff_management"]["promotion_channel"]
            if promotion_channel:
                channel = ctx.guild.get_channel(promotion_channel)
                if channel:
                    await channel.send(member.mention,embed=infract_embed)
                    await ctx.send(
                        embed = discord.Embed(
                            title = "Success",
                            description = f"{member} has been promoted.",
                            color = BLANK_COLOR
                        )
                    )
                else:
                    await ctx.send(member.mention,
                        embed = discord.Embed(
                            title = "Error",
                            description = "Promotion channel not found.",
                            color = RED_COLOR
                        )
                    )
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Channel not setuped",
                        description="Please select Staff Promotion Log channel via `/config` command from Staff Management Page.",
                        color = RED_COLOR
                    )
                )
        if dm == "true":
            await member.send(
                embed = infract_embed
            )

            
    @infraction.command(
        name="view",
        extras={
            "category": "Infraction"
        }
    )
    @is_management()
    async def view_infraction(self, ctx, member: discord.Member = None, case: int = None):
        '''
        View the infractions of a staff member.
        '''
        await ctx.typing()
        infract_embed = discord.Embed(
            title=f"{member}'s Infractions" if member else f"Infraction Case {case}",
            description=" ",
            color=BLANK_COLOR
        )

        if member is not None:
            query = {"member_id": member.id, "guild_id": ctx.guild.id}
            infractions = await self.bot.infraction_log.find_by_query(query)
            if not infractions:
                await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="No infraction found.",
                        color=RED_COLOR
                    )
                )
                return
            user = ctx.guild.get_member(infraction['member_id'])
            for infraction in infractions:
                infract_embed.description += f"\n\n**User:** <@{infraction['member_id']}>"
                infract_embed.description += f"\n**Type:** {infraction['type']}"
                infract_embed.description += f"\n**Approver:** <@&{infraction['approver_id']}>"
                infract_embed.description += f"\n**Reason:** {infraction['reason']}"
                infract_embed.description += f"\n**Rank:** {infraction['rank']}"
                infract_embed.description += f"\n**Punishment:** {infraction['punishment']}"
                infract_embed.description += f"\n**Date:** {infraction['date']}"
                infract_embed.description += f"\n**Case:** {infraction.get('case', 'N/A')}"
                infract_embed.set_thumbnail(
                    url=user.avatar.url
                ).add_field(
                    name="Total Infractions",
                    value=len(infractions)
                ).add_field(
                    name="Total Warnings",
                    value=len([infraction for infraction in infractions if infraction['type'] == "warning"])
                ).add_field(
                    name="Total Demotions",
                    value=len([infraction for infraction in infractions if infraction['type'] == "demotion"])
                ).add_field(
                    name="Total Promotions",
                    value=len([infraction for infraction in infractions if infraction['type'] == "promotion"])
                ).add_field(
                    name="Top Role",
                    value=user.top_role.mention
                )
            await ctx.send(embed=infract_embed)

        elif case is not None:
            query = {"case": case, "guild_id": ctx.guild.id}
            infractions = await self.bot.infraction_log.find_by_query(query)
            if infractions:
                infraction = infractions[0]
                user = ctx.guild.get_member(infraction['member_id'])
                infract_embed.description += f"\n\n**User:** <@{infraction['member_id']}>"
                infract_embed.description += f"\n**Type:** {infraction['type']}"
                infract_embed.description += f"\n**Approver:** <@&{infraction['approver_id']}>"
                infract_embed.description += f"\n**Reason:** {infraction['reason']}"
                infract_embed.description += f"\n**Punishment:** {infraction['punishment']}"
                infract_embed.description += f"\n**Date:** {infraction['date']}"
                infract_embed.description += f"\n**Case:** {infraction['case']}"
                infract_embed.set_thumbnail(
                    url=user.avatar.url
                ).add_field(
                    name="Total Infractions",
                    value=len(infractions)
                ).add_field(
                    name="Total Warnings",
                    value=len([infraction for infraction in infractions if infraction['type'] == "warning"])
                ).add_field(
                    name="Total Demotions",
                    value=len([infraction for infraction in infractions if infraction['type'] == "demotion"])
                ).add_field(
                    name="Total Promotions",
                    value=len([infraction for infraction in infractions if infraction['type'] == "promotion"])
                ).add_field(
                    name="Top Role",
                    value=user.top_role.mention
                )
                await ctx.send(embed=infract_embed)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description="No infraction found.",
                        color=RED_COLOR
                    )
                )
        else:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Please provide a member or a case number.",
                    color=RED_COLOR
                )
            )

    @infraction.command(
        name="delete",
        extras={
            "category": "Infraction"
        },
        aliases=["del"]
    )
    @is_management()
    async def delete_infraction(self, ctx, case: int):
        '''
        Delete an infraction.
        '''
        await ctx.typing()
        query = {"case": case, "guild_id": ctx.guild.id}
        infraction = await self.bot.infraction_log.find_by_query(query)
        if not infraction:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="No infraction found.",
                    color=RED_COLOR
                )
            )
            return
        await self.bot.infraction_log.delete_doc(query)
        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"Infraction case {case} has been deleted.",
                color=GREEN_COLOR
            )
        )

    @infraction.command(
        name="clear",
        extras={
            "category": "Infraction"
        }
    )
    @is_management()
    async def clear_infractions(self, ctx, member: discord.Member):
        '''
        Clear all infractions of a staff member.
        '''
        await ctx.typing()
        query = {"member_id": member.id, "guild_id": ctx.guild.id}
        infractions = await self.bot.infraction_log.find_by_query(query)
        if not infractions:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="No infraction found.",
                    color=RED_COLOR
                )
            )
            return
        await self.bot.infraction_log.delete_many(query)
        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description=f"All infractions of {member} have been cleared.",
                color=GREEN_COLOR
            )
        )

async def setup(bot):
    await bot.add_cog(Infraction(bot))