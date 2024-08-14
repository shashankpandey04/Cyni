import discord
from discord.ext import commands
import time
import asyncio

from utils.constants import YELLOW_COLOR, BLANK_COLOR, RED_COLOR, GREEN_COLOR
import utils.prc_api as prc_api
from utils.prc_api import ServerPlayers, ServerStatus, ServerKillLogs, ServerJoinLogs, ResponseFailed
from discord import app_commands
from cyni import is_management, is_staff

import roblox
import re
from utils.utils import get_discord_by_roblox

class ERLC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_server_linked():
        async def predicate(ctx: commands.Context):
            guild_id = ctx.guild.id
            try:
                await ctx.bot.prc_api.get_server_status(guild_id)
            except prc_api.ResponseFailed as exc:
                raise prc_api.ServerLinkNotFound(str(exc))
            return True
        return commands.check(predicate)
    
    @commands.hybrid_group(
        name="erlc",
        extras={
            "category": "ERLC"
        }
    )
    async def server(self, ctx):
        """
        Manage your ERLC server.
        """
        pass

    @server.command(
        name="info",
        extras={
            "category": "ERLC"
        }
    )
    @is_staff()
    @is_server_linked()
    async def erlc_info(self, ctx):
        """
        Get information about the ERLC server.
        """
        server_id = ctx.guild.id
        status: ServerStatus = await ctx.bot.prc_api.get_server_status(server_id)
        players: ServerPlayers = await ctx.bot.prc_api.get_server_players(server_id)
        queue: int = await ctx.bot.prc_api.get_server_queue(server_id)
        client = roblox.Client()

        embed = discord.Embed(
            title=f"{status.name}",
            color=BLANK_COLOR
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        ).add_field(
            name="Basic Information",
            value= (
                f"**> Join Code:** [{status.join_key}](https://policeroleplay.community/join/{status.join_key})\n"
                f"**> In-Game Players:** {status.current_players}/{status.max_players}\n"
                f"**> Queue:** {queue}\n"
            ),
            inline=False
        ).add_field(
            name="Server Information",
            value=(
                f"> **Owner:** [{(await client.get_user(status.owner_id)).name}](https://roblox.com/users/{status.owner_id}/profile)\n"
                f"> **Co-Owners:** {f', '.join([f'[{user.name}](https://roblox.com/users/{user.id}/profile)' for user in await client.get_users(status.co_owner_ids, expand=False)])}"
            ),
            inline=False
        ).add_field(
            name="Server Staff",
            value=(
                f"> **Moderators:** {len(list(filter(lambda x: x.permission == 'Server Moderator', players)))}\n"
                f"> **Administrators:** {len(list(filter(lambda x: x.permission == 'Server Administrator', players)))}\n"
                f"> **Staff In-Game:** {len(list(filter(lambda x: x.permission != 'Normal', players)))}\n"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    @server.command(
        name="staff",
        extras={
            "category": "ERLC"
        }
    )
    @is_staff()
    @is_server_linked()
    async def erlc_staff(self, ctx):
        """
        Get information about the ERLC server staff.
        """
        server_id = ctx.guild.id
        players: ServerPlayers = await ctx.bot.prc_api.get_server_players(server_id)
        client = roblox.Client()

        embed = discord.Embed(
            title="Server Staff",
            color=BLANK_COLOR
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        )

        actual_players = []
        key_maps = {}
        for item in players:
            if item.permission == "Normal":
                actual_players.append(item)
            else:
                if item.permission not in key_maps:
                    key_maps[item.permission] = [item]
                else:
                    key_maps[item.permission].append(item)

        new_maps = [
            "Server Owners",
            "Server Administrator",
            "Server Moderator"
        ]
        new_vals = [
            key_maps.get('Server Owner', []) + key_maps.get('Server Co-Owner', []),
            key_maps.get('Server Administrator', []),
            key_maps.get('Server Moderator', [])
        ]
        new_keymap = dict(zip(new_maps, new_vals))

        for key, value in new_keymap.items():
            if (value := '\n'.join([f'> [{player.username}](https://roblox.com/users/{player.id}/profile)' for player in value])) not in ['', '\n']:
                embed.add_field(
                    name=f'{key}',
                    value=value,
                    inline=False
                )
        
        if len(embed.fields) > 0:
            embed.description = "> There are no staff members in this server."

        await ctx.send(embed=embed)

    @server.command(
        name="kills",
        extras={
            "category": "ERLC"
        }
    )
    @is_staff()
    @is_server_linked()
    async def kills(self, ctx: commands.Context):
        guild_id = int(guild_id)
        kill_logs: list[ServerKillLogs] = await self.bot.prc_api.fetch_kill_logs(guild_id)
        embed = discord.Embed(
            color=BLANK_COLOR,
            title="Server Kill Logs",
            description=""
        )

        sorted_kill_logs = sorted(kill_logs, key=lambda log: log.timestamp, reverse=True)
        for log in sorted_kill_logs:
            if len(embed.description) > 3800:
                break
            embed.description += f"> [{log.killer_username}](https://roblox.com/users/{log.killer_user_id}/profile) killed [{log.killed_username}](https://roblox.com/users/{log.killed_user_id}/profile) • <t:{int(log.timestamp)}:R>\n"

        if embed.description in ['', '\n']:
            embed.description = "> No kill logs found."


        embed.set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon
        )

        await ctx.send(embed=embed)

    @server.command(
        name="players",
        extras={
            "category": "ERLC"
        }
    )
    @is_staff()
    @is_server_linked()
    async def server_players(self, ctx: commands.Context):
        try:
            guild_id = int(ctx.guild.id)
            status: ServerStatus = await self.bot.prc_api.get_server_status(guild_id)
            players: list[ServerPlayers] = await self.bot.prc_api.get_server_players(guild_id)
            queue: int = await self.bot.prc_api.get_server_queue(guild_id)
            embed = discord.Embed(
                title=f"Server Players [{len(players)}]",
                color=BLANK_COLOR,
                description=""
            )
            actual_players = []
            staff = []
            for item in players:
                if item.permission == "Normal":
                    actual_players.append(item)
                else:
                    staff.append(item)

            embed.description += (
                f"**{status.name} Staff [{len(staff)}]**\n" + 
                ', '.join([f'[{plr.username} ({plr.team})](https://roblox.com/users/{plr.id}/profile)' for plr in staff])
            )
            
            
            embed.description += (
                f"\n\n**Online Players [{len(actual_players)}]**\n" +
                ', '.join([f'[{plr.username} ({plr.team})](https://roblox.com/users/{plr.id}/profile)' for plr in actual_players])
            )
            
            embed.description += (
                f"\n\n**Queue [{len(queue)}]**\n" +
                ', '.join([f'[{plr.username}](https://roblox.com/users/{plr.id}/profile)' for plr in queue])
            )
            
            embed.set_author(
                name=ctx.guild.name,
                icon_url=ctx.guild.icon
            )
            if len(embed.description) > 3999:
                embed.description = ""
                embed.description += (
                    f"**Server Staff [{len(staff)}]**\n" + 
                    ', '.join([f'{plr.username} ({plr.team})' for plr in staff])
                )
            
                embed.description += (
                    f"\n\n**Online Players [{len(actual_players)}]**\n" +
                    ', '.join([f'{plr.username} ({plr.team})' for plr in actual_players])
                )

                embed.description += (
                    f"\n\n**Queue [{len(queue)}]**\n" +
                    ', '.join([f'{plr.username}' for plr in queue])
                )

            await ctx.send(embed=embed)

        except Exception as e:
            print(e)
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="An error occurred while fetching the players from the PRC API.",
                    color=BLANK_COLOR
                )
            )

    @server.command(
        name="check",
        description="Perform a Discord check on your server to see if all players are in the Discord server."
    )
    @is_staff()
    @is_server_linked()
    async def check(self, ctx: commands.Context):
        msg = await ctx.send(
            embed=discord.Embed(
                title="Checking...",
                description="This may take a while.",
                color=BLANK_COLOR
            )
        )
        guild_id = ctx.guild.id
        try:
            players: list[ServerPlayers] = await self.bot.prc_api.get_server_players(guild_id)
        except ResponseFailed:
            return await msg.edit(
                embed=discord.Embed(
                    title="PRC API Error",
                    description="An error occurred while fetching the players from the PRC API.",
                    color=BLANK_COLOR
                )
            )

        if not players:
            return await msg.edit(
                embed=discord.Embed(
                    title=" No Players Found",
                    description="No players were found in the server.",
                    color=BLANK_COLOR
                )
            )

        embed = discord.Embed(
            title="Players in ERLC Not in Discord",
            color=BLANK_COLOR,
            description=""
        )

        for player in players:
            pattern = re.compile(re.escape(player.username), re.IGNORECASE)
            member_found = False

            for member in ctx.guild.members:
                if pattern.search(member.name) or pattern.search(member.display_name) or (hasattr(member, 'global_name') and member.global_name and pattern.search(member.global_name)):
                    member_found = True
                    break

            if not member_found:
                try:
                    discord_id = await get_discord_by_roblox(self.bot, player.username)
                    if discord_id:
                        member = ctx.guild.get_member(discord_id)
                        if member:
                            member_found = True
                except discord.HTTPException:
                    pass

            if not member_found:
                embed.description += f"> [{player.username}](https://roblox.com/users/{player.id}/profile)\n"

        if embed.description == "":
            embed.description = "> All players are in the Discord server."

        embed.set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon
        )
        await msg.edit(embed=embed)

    @server.command(
        name="link",
        description="Link your Discord server to the ERLC server."
    )
    @is_staff()
    @is_management()
    async def server_link(self, ctx: commands.Context, key: str):
        try:
            status: int | ServerStatus = await self.bot.prc_api.send_test_request(key)
            if isinstance(status, int):
                await (ctx.send if not ctx.interaction else ctx.interaction.response.send_message)(
                    embed=discord.Embed(
                        title="Incorrect Key",
                        description="This Server Key is invalid and nonfunctional. Ensure you've entered it correctly.",
                        color=BLANK_COLOR
                    ),
                    ephemeral=True
                )
            else:
                await self.bot.erlc_keys.upsert({
                    "_id": ctx.guild.id,
                    "key": key
                })

                await (ctx.send if not ctx.interaction else ctx.interaction.response.send_message)(
                    embed=discord.Embed(
                        title="Successfully Changed",
                        description="I have changed the Server Key successfully. You can now run ERLC commands on your server.",
                        color=GREEN_COLOR
                    ),
                    ephemeral=True
                )
        except Exception as e:
            print(e)
            await (ctx.send if not ctx.interaction else ctx.interaction.response.send_message)(
                embed=discord.Embed(
                    title="Error",
                    description="An error occurred while linking the server.",
                    color=RED_COLOR
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ERLC(bot))