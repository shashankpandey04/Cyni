import discord
from discord.ext import commands


class Infraction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="staff",
        extras={
            "category": "Infraction"
        }
    )
    async def staff(self, ctx):
        """
        Staff commands.
        """
        pass

    @staff.command(
        name="promote",
        extras={
            "category": "Infraction"
        }
    )
    async def promote(self, ctx, member: discord.Member,rank:discord.Role,approver:discord.Role,reason: str = None,*,role_remove:discord.Role = None,role_add:discord.Role = None):
        """
        Promote a staff member.
        """
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Error",
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        
        module_enabled = settings["staff_management"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Error",
                    description = "Staff management module is not enabled.",
                    color = discord.Color.red()
                )
            )
        
        embed = discord.Embed(
            title = f"{member} has been promoted to {rank}.",
            color = discord.Color.green()
        )
        if role_remove:
            await member.remove_roles(role_remove)
        if role_add:
            await member.add_roles(role_add)
        
        embed.add_field(
            name="Approved by",
            value=approver.mention
        ).add_field(
            name="Reason",
            value=reason
        ).set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url
        ).set_image(
            url=member.avatar.url
        ).set_footer(
            text=f"ID: {member.id}"
        )
        
        promotion_channel = settings["staff_management"]["promotion_channel"]
        if promotion_channel:
            channel = ctx.guild.get_channel(promotion_channel)
            if channel:
                await channel.send(embed=embed)
                await ctx.send(
                    embed = discord.Embed(
                        title = "Success",
                        description = f"{member} has been promoted to {rank}.",
                        color = discord.Color.green()
                    )
                )
            else:
                await ctx.send(member.mention,
                    embed = discord.Embed(
                        title = "Error",
                        description = "Promotion channel not found.",
                        color = discord.Color.red()
                    )
                )
        else:
            await ctx.send(
                embed = discord.Embed(
                    title="Error",
                    description="Promotion channel not found.",
                    color=discord.Color.red()
                )
            )

    @staff.command(
        name="demote",
        extras={
            "category": "Infraction"
        }
    )
    async def demote(self, ctx, member: discord.Member,rank:discord.Role,approver:discord.Role,reason: str = None,*,role_remove:discord.Role = None,role_add:discord.Role = None,punishment: str = None):
        """
        Demote a staff member.
        """
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Error",
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        
        module_enabled = settings["staff_management"]["enabled"]
        if not module_enabled:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Error",
                    description = "Staff management module is not enabled.",
                    color = discord.Color.red()
                )
            )

        embed = discord.Embed(
            title = f"{member} has been demoted to {rank}.",
            color = discord.Color.red()
        )
        if role_remove:
            await member.remove_roles(role_remove)
        if role_add:
            await member.add_roles(role_add)
        
        embed.add_field(
            name="Approved by",
            value=approver.mention
        ).add_field(
            name="Reason",
            value=reason
        ).set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url
        ).set_thumbnail(
            url=member.avatar.url
        ).set_footer(
            text=f"ID: {member.id}"
        )

        if punishment:
            embed.add_field(
                name="Punishment",
                value=punishment
            )
        
        demotion_channel = settings["staff_management"]["demotion_channel"]
        if demotion_channel:
            channel = ctx.guild.get_channel(demotion_channel)
            if channel:
                await channel.send(embed=embed)
                await ctx.send(
                    embed = discord.Embed(
                        title = "Success",
                        description = f"{member} has been demoted to {rank}.",
                        color = discord.Color.red()
                    )
                )
            else:
                await ctx.send(member.mention,
                    embed = discord.Embed(
                        title = "Error",
                        description = f"Demotion channel not found.",
                        color = discord.Color.red()
                    )
                )
        else:
            await ctx.send(
                embed = discord.Embed(
                    title="Error",
                    description="Demotion channel not found.",
                    color=discord.Color.red()
                )
            )

    @staff.command(
        name="warn",
        extras={
            "category": "Infraction"
        }
    )
    async def warn(self, ctx, member: discord.Member,reason: str = None,punishment: str = None,*,role_remove:discord.Role = None,role_add:discord.Role = None):
        """
        Warn a staff member.
        """
        settings = await self.bot.settings.find_by_id(ctx.guild.id)
        if not settings:
            return await ctx.send(
                embed = discord.Embed(
                    title = "Error",
                    description = "No settings found.\nPlease set up the bot using the `config` command.",
                    color = discord.Color.red()
                )
            )
        embed = discord.Embed(
            title = f"{member} has been warned.",
            color = discord.Color.red()
        )

        if role_remove:
            await member.remove_roles(role_remove)
        if role_add:
            await member.add_roles(role_add)
        
        embed.add_field(
            name="Reason",
            value=reason
        ).set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar.url
        ).set_thumbnail(
            url=member.avatar.url
        ).set_footer(
            text=f"ID: {member.id}"
        )

        if punishment:
            embed.add_field(
                name="Punishment",
                value=punishment
            )
        
        warning_channel = settings["staff_management"]["warning_channel"]
        if warning_channel:
            channel = ctx.guild.get_channel(warning_channel)
            if channel:
                await channel.send(embed=embed)
            else:
                await ctx.send(member.mention,
                    embed = discord.Embed(
                        title = "Error",
                        description = "Warning channel not found.",
                        color = discord.Color.red()
                    )
                )
        else:
            await ctx.send(
                member.mention,
                embed = embed
            )

async def setup(bot):
    await bot.add_cog(Infraction(bot))