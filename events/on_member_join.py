import discord
import time
from discord.ext import commands

from utils.constants import GREEN_COLOR
from utils.utils import discord_time
import datetime

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        This event is triggered when a member joins a guild.
        :param member (discord.Member): The member that joined the guild.
        """

        sett = await self.bot.settings.find_by_id(member.guild.id)
        guild = member.guild
        if not sett:
            return
            
        if sett.get("moderation_module", {}).get("enabled", False) is True:
            if sett.get("moderation_module", {}).get("audit_log") is not None:
                guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
                if not guild_log_channel:
                    return
                joined_at = discord_time(datetime.datetime.now())
                embed = discord.Embed(
                        title= " ",
                        description=f"{member.mention} joined the server on {joined_at}",
                        color=GREEN_COLOR
                    ).add_field(
                        name="Account Created",
                        value=f"{discord_time(member.created_at)}",
                    ).add_field(
                        name="Member Count",
                        value=f"{guild.member_count}",
                    ).set_footer(
                        text=f"User ID: {member.id}"
                    )
                try:
                    embed.set_thumbnail(
                        url=member.avatar.url
                    )
                except:
                    pass
                #if cyni_webhook:
                #    await cyni_webhook.send(embed=embed)
                #else:
                await guild_log_channel.send(embed=embed)
        
        if sett.get('welcome_module', {}).get('enabled', False) is True:
            welcome_channel = guild.get_channel(sett['welcome_module']['welcome_channel'])
            welcome_message = sett['welcome_module']['welcome_message']
            welcome_role = guild.get_role(sett['welcome_module']['welcome_role'])
            use_embed = sett['welcome_module']['use_embed']
            embed_color = sett['welcome_module']['embed_color']
            embed_title = sett['welcome_module']['embed_title']

            welcome_message = welcome_message.replace("{user}", member.mention)
            welcome_message = welcome_message.replace("{server}", guild.name)
            welcome_message = welcome_message.replace("{user_name}", member.name)
            welcome_message = welcome_message.replace("{user_discriminator}", member.discriminator)
            welcome_message = welcome_message.replace("{user_id}", str(member.id))
            welcome_message = welcome_message.replace("{server_id}", str(guild.id))
            welcome_message = welcome_message.replace("{member_count}", str(guild.member_count))
            
            if use_embed:
                embed = discord.Embed(
                    title=embed_title,
                    description=welcome_message,
                    color=int(embed_color, 16)
                )
                embed.set_thumbnail(
                    url=member.avatar.url
                )
                await welcome_channel.send(embed=embed)
            else:
                await welcome_channel.send(welcome_message)
            if welcome_role:
                await member.add_roles(welcome_role)

async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))