import discord
from discord.ext import commands
from discord import app_commands
import roblox
import re
from typing import List, Optional

from utils.constants import YELLOW_COLOR, BLANK_COLOR, RED_COLOR, GREEN_COLOR
import utils.prc_api as prc_api
from utils.prc_api import ServerPlayers, ServerStatus, ServerKillLogs, ServerJoinLogs, ResponseFailed
from cyni import is_management, is_staff
from utils.utils import get_discord_by_roblox

class ERLC(commands.Cog):
    """ERLC server management commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.roblox_client = roblox.Client()

    async def cog_unload(self):
        """Clean up when cog is unloaded."""
        # roblox.Client doesn't need explicit closing
        pass

    def is_server_linked():
        """Check if the server is linked to an ERLC server."""
        async def predicate(ctx: commands.Context):
            try:
                await ctx.bot.prc_api._fetch_server_status(ctx.guild.id)
                return True
            except (prc_api.ResponseFailed, Exception) as e:
                raise prc_api.ServerLinkNotFound(str(e))
        return commands.check(predicate)

    async def _get_roblox_user_info(self, user_id: int) -> tuple[str, str]:
        """Get Roblox user info with error handling."""
        try:
            user = await self.roblox_client.get_user(user_id)
            return user.name, f"[{user.name}](https://roblox.com/users/{user_id}/profile)"
        except roblox.UserNotFound:
            return "Unknown", "Unknown"

    async def _create_base_embed(self, title: str, ctx: commands.Context, description: str = "") -> discord.Embed:
        """Create a base embed with common styling."""
        return discord.Embed(
            title=title,
            description=description,
            color=BLANK_COLOR
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon
        ).set_footer(
            text="Cyni Bot | ERLC Integration",
            icon_url=self.bot.user.avatar
        )
    
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
        name="link",
        description="Link your Discord server to the ERLC server."
    )
    @is_management()
    @app_commands.describe(key="The ERLC server key.")
    async def server_link(self, ctx: commands.Context, key: str):
        """Link Discord server to ERLC server."""
        try:
            is_valid = await self.bot.prc_api._send_test_request(key)
            
            if not is_valid:
                embed = discord.Embed(
                    title="Invalid Key",
                    description="The key you provided is invalid. Please provide a valid key.",
                    color=RED_COLOR
                )
            else:
                await self.bot.erlc.upsert({
                    "_id": ctx.guild.id,
                    "key": key
                })
                embed = discord.Embed(
                    title="Successfully Linked",
                    description="Server key updated successfully. You can now use ERLC commands.",
                    color=GREEN_COLOR
                )
            
            respond = ctx.send if not ctx.interaction else ctx.interaction.response.send_message
            await respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error linking server: {e}")
            embed = discord.Embed(
                title="Error",
                description="An error occurred while linking the server.",
                color=RED_COLOR
            )
            respond = ctx.send if not ctx.interaction else ctx.interaction.response.send_message
            await respond(embed=embed, ephemeral=True)

    @server.command(
        name="info",
        description="Get information about the ERLC server."
    )
    @is_staff()
    @is_server_linked()
    async def erlc_info(self, ctx: commands.Context):
        """Get information about the ERLC server."""
        await ctx.typing()
        
        try:
            status: ServerStatus = await self.bot.prc_api._fetch_server_status(ctx.guild.id)
            
            # Get owner information
            _, owner_link = await self._get_roblox_user_info(status.OwnerId)
            
            # Get co-owners information
            co_owners = []
            if not status.CoOwnerIds:
                co_owners.append("No co-owners")
            else:
                for co_owner_id in status.CoOwnerIds:
                    _, co_owner_link = await self._get_roblox_user_info(co_owner_id)
                    co_owners.append(co_owner_link)

            embed = await self._create_base_embed(
                "Emergency Response: Liberty County Server Information",
                ctx,
                f"""
                **Server Details**
                > **Server Name:** `{status.Name}`
                > **Join Code:** [{status.JoinKey}](https://policeroleplay.community/join/{status.JoinKey})
                > **In-Game Players:** {status.CurrentPlayers}/{status.MaxPlayers}

                **Server Ownership**
                > **Owner:** {owner_link}
                > **Co-Owners:** {', '.join(co_owners)}
                """
            )
            embed.set_thumbnail(url=ctx.guild.icon)
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error fetching server info: {e}")
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Failed to fetch server information.",
                color=RED_COLOR
            ))

    @server.command(
        name="staff",
        description="Get information about the ERLC server staff."
    )
    @is_staff()
    @is_server_linked()
    async def erlc_staff(self, ctx: commands.Context):
        """Get information about the ERLC server staff."""
        await ctx.typing()
        
        try:
            players: List[ServerPlayers] = await self.bot.prc_api._fetch_server_players(ctx.guild.id)
            embed = await self._create_base_embed("Server Staff", ctx)

            # Categorize players by permission level
            staff_categories = {
                "Server Owners": [],
                "Server Administrator": [],
                "Server Moderator": []
            }

            for player in players:
                if player.permission in ["Server Owner", "Server Co-Owner"]:
                    staff_categories["Server Owners"].append(player)
                elif player.permission == "Server Administrator":
                    staff_categories["Server Administrator"].append(player)
                elif player.permission == "Server Moderator":
                    staff_categories["Server Moderator"].append(player)

            # Add fields for each staff category
            for category, staff_list in staff_categories.items():
                if staff_list:
                    staff_links = [
                        f'> [{player.username}](https://roblox.com/users/{player.id}/profile)'
                        for player in staff_list
                    ]
                    embed.add_field(
                        name=category,
                        value='\n'.join(staff_links),
                        inline=False
                    )

            if not embed.fields:
                embed.description = "> There are no staff members in this server."

            await ctx.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error fetching staff: {e}")
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Failed to fetch staff information.",
                color=RED_COLOR
            ))

    @server.command(
        name="kills",
        description="Get the kill logs of the server."
    )
    @is_staff()
    @is_server_linked()
    async def kills(self, ctx: commands.Context):
        """Get server kill logs."""
        await ctx.typing()
        
        try:
            kill_logs: List[ServerKillLogs] = await self.bot.prc_api._fetch_server_killlogs(ctx.guild.id)
            embed = await self._create_base_embed("Server Kill Logs", ctx)

            # Sort logs by timestamp (newest first) and build description
            sorted_logs = sorted(kill_logs, key=lambda log: log.timestamp, reverse=True)
            log_entries = []
            
            for log in sorted_logs:
                if len('\n'.join(log_entries)) > 3800:  # Leave room for other embed content
                    break
                
                # Check if timestamp is valid
                timestamp_str = f"<t:{int(log.timestamp)}:R>" if log.timestamp is not None else "Unknown time"
                    
                entry = (f"> [{log.killer_username}](https://roblox.com/users/{log.killer_user_id}/profile) "
                        f"killed [{log.killed_username}](https://roblox.com/users/{log.killed_user_id}/profile) "
                        f"• {timestamp_str}")
                log_entries.append(entry)

            embed.description = '\n'.join(log_entries) if log_entries else "> No kill logs found."
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error fetching kill logs: {e}")
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Failed to fetch kill logs.",
                color=RED_COLOR
            ))

    @server.command(
        name="players",
        description="Get current players in the server."
    )
    @is_staff()
    @is_server_linked()
    async def server_players(self, ctx: commands.Context):
        """Get current players in the server."""
        await ctx.typing()
        
        try:
            status: ServerStatus = await self.bot.prc_api._fetch_server_status(ctx.guild.id)
            players: List[ServerPlayers] = await self.bot.prc_api._fetch_server_players(ctx.guild.id)
            queue = await self.bot.prc_api._fetch_server_queue(ctx.guild.id)
            
            # Separate players by type
            staff_players = [p for p in players if p.permission != "Normal"]
            regular_players = [p for p in players if p.permission == "Normal"]
            
            # Build player lists with proper formatting
            def format_player_list(player_list, include_team=True, include_links=True):
                if include_links:
                    if include_team:
                        return ', '.join([f'[{p.username} ({p.team})](https://roblox.com/users/{p.id}/profile)' for p in player_list])
                    else:
                        return ', '.join([f'[{p.username}](https://roblox.com/users/{p.id}/profile)' for p in player_list])
                else:
                    if include_team:
                        return ', '.join([f'{p.username} ({p.team})' for p in player_list])
                    else:
                        return ', '.join([f'{p.username}' for p in player_list])

            # Build description
            description_parts = []
            
            if staff_players:
                staff_text = format_player_list(staff_players)
                description_parts.append(f"**{status.name} Staff [{len(staff_players)}]**\n{staff_text}")
            
            if regular_players:
                players_text = format_player_list(regular_players)
                description_parts.append(f"**Online Players [{len(regular_players)}]**\n{players_text}")
            
            if queue:
                queue_text = format_player_list(queue, include_team=False)
                description_parts.append(f"**Queue [{len(queue)}]**\n{queue_text}")

            description = '\n\n'.join(description_parts)
            
            # If description is too long, use simplified formatting
            if len(description) > 4000:
                description_parts = []
                
                if staff_players:
                    staff_text = format_player_list(staff_players, include_links=False)
                    description_parts.append(f"**Server Staff [{len(staff_players)}]**\n{staff_text}")
                
                if regular_players:
                    players_text = format_player_list(regular_players, include_links=False)
                    description_parts.append(f"**Online Players [{len(regular_players)}]**\n{players_text}")
                
                if queue:
                    queue_text = format_player_list(queue, include_team=False, include_links=False)
                    description_parts.append(f"**Queue [{len(queue)}]**\n{queue_text}")
                
                description = '\n\n'.join(description_parts)

            embed = await self._create_base_embed(f"Server Players [{len(players)}]", ctx, description)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Failed to fetch player information.",
                color=RED_COLOR
            ))

    @server.command(
        name="check",
        description="Check if all ERLC players are in the Discord server."
    )
    @is_staff()
    @is_server_linked()
    async def check(self, ctx: commands.Context):
        """Perform a Discord check on your server."""
        embed = discord.Embed(
            title="Checking...",
            description="This may take a while.",
            color=BLANK_COLOR
        )
        msg = await ctx.send(embed=embed)
        
        try:
            players: List[ServerPlayers] = await self.bot.prc_api._fetch_server_players(ctx.guild.id)
            
            if not players:
                embed = discord.Embed(
                    title="No Players Found",
                    description="No players were found in the server.",
                    color=BLANK_COLOR
                )
                return await msg.edit(embed=embed)

            missing_players = []
            guild_members = {member.id: member for member in ctx.guild.members}
            
            for player in players:
                member_found = False
                
                # Check by display name patterns
                pattern = re.compile(re.escape(player.username), re.IGNORECASE)
                for member in guild_members.values():
                    if (pattern.search(member.name) or 
                        pattern.search(member.display_name) or 
                        (member.global_name and pattern.search(member.global_name))):
                        member_found = True
                        break
                
                # Check by Roblox-Discord link if not found
                if not member_found:
                    try:
                        discord_id = await get_discord_by_roblox(self.bot, player.username)
                        if discord_id and discord_id in guild_members:
                            member_found = True
                    except Exception:
                        pass
                
                if not member_found:
                    missing_players.append(f"> [{player.username}](https://roblox.com/users/{player.id}/profile)")

            embed = await self._create_base_embed("Players in ERLC Not in Discord", ctx)
            embed.description = '\n'.join(missing_players) if missing_players else "> All players are in the Discord server."
            
            await msg.edit(embed=embed)
            
        except ResponseFailed:
            embed = discord.Embed(
                title="PRC API Error",
                description="An error occurred while fetching players from the PRC API.",
                color=RED_COLOR
            )
            await msg.edit(embed=embed)
        except Exception as e:
            self.bot.logger.error(f"Error in Discord check: {e}")
            embed = discord.Embed(
                title="Error",
                description="An unexpected error occurred during the check.",
                color=RED_COLOR
            )
            await msg.edit(embed=embed)

    @server.command(
        name="joinlogs",
        description="Get the join and leave logs of the server."
    )
    @is_staff()
    @is_server_linked()
    async def join_logs(self, ctx: commands.Context):
        """Get server join and leave logs."""
        await ctx.typing()
        
        try:
            join_logs: List[ServerJoinLogs] = await self.bot.prc_api._fetch_server_join_logs(ctx.guild.id)
            embed = await self._create_base_embed("Server Join & Leave Logs", ctx)

            # Sort logs by timestamp (newest first) and build description
            sorted_logs = sorted(join_logs, key=lambda log: log.Timestamp, reverse=True)
            log_entries = []
            
            for log in sorted_logs:
                if len('\n'.join(log_entries)) > 3800:  # Leave room for other embed content
                    break
                
                # Parse player info
                player_parts = log.Player.split(":")
                if len(player_parts) > 1:
                    player_name = player_parts[0]
                    player_id = player_parts[1]
                    player_link = f"[{player_name}](https://roblox.com/users/{player_id}/profile)"
                else:
                    player_name = player_parts[0]
                    player_link = player_name
                
                status = 'Joined' if log.Join else 'Left'
                # Check if timestamp is valid
                timestamp_str = f"<t:{int(log.Timestamp)}:R>" if log.Timestamp is not None else "Unknown time"
                entry = f"> {player_link} {status} the server • {timestamp_str}"
                log_entries.append(entry)

            embed.description = '\n'.join(log_entries) if log_entries else "> No join logs found."
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error fetching join logs: {e}")
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Failed to fetch join logs.",
                color=RED_COLOR
            ))

async def setup(bot):
    await bot.add_cog(ERLC(bot))