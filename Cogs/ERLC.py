import discord
from discord.ext import commands
from discord import app_commands
import roblox
import re
from typing import List, Optional, Tuple

from utils.constants import YELLOW_COLOR, BLANK_COLOR, RED_COLOR, GREEN_COLOR
import utils.prc_api as prc_api
from utils.prc_api import ServerPlayers, ServerStatus, ServerKillLogs, ServerJoinLogs, ResponseFailed, ServerLinkNotFound
from cyni import is_management, is_staff, is_erlc_staff, is_erlc_management
from utils.utils import get_discord_by_roblox, log_command_usage
from utils.pagination import Pagination
from UI.erlc import StaffRoles, LoggingChannels

class ERLC(commands.Cog):
    """ERLC server management commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.roblox_client = roblox.Client()
        # Cache for Roblox user info to reduce API calls
        self._roblox_cache = {}

    async def cog_unload(self):
        """Clean up when cog is unloaded."""
        self._roblox_cache.clear()
        
        # Close roblox client session if it has one
        try:
            if hasattr(self.roblox_client, 'close'):
                await self.roblox_client.close()
                print("ERLC cog: Roblox client closed")
            elif hasattr(self.roblox_client, 'aclose'):
                await self.roblox_client.aclose()
                print("ERLC cog: Roblox client aclosed")
            elif hasattr(self.roblox_client, '_client') and hasattr(self.roblox_client._client, 'aclose'):
                await self.roblox_client._client.aclose()
                print("ERLC cog: Roblox internal client closed")
        except Exception as e:
            print(f"ERLC cog: Error closing roblox client: {e}")

    @staticmethod
    def is_server_linked():
        """Check if the server is linked to an ERLC server."""
        async def predicate(ctx: commands.Context):
            try:
                await ctx.bot.prc_api._fetch_server_status(ctx.guild.id)
                return True
            except (prc_api.ResponseFailed, Exception):
                raise ServerLinkNotFound("Server is not linked to an ERLC server.")
        return commands.check(predicate)

    async def _get_roblox_user_info(self, user_id: int) -> Tuple[str, str]:
        """Get Roblox user info with caching and error handling."""
        if user_id in self._roblox_cache:
            cached_data = self._roblox_cache[user_id]
            return cached_data['name'], cached_data['link']
        
        try:
            user = await self.roblox_client.get_user(user_id)
            name = user.name
            link = f"[{name}](https://roblox.com/users/{user_id}/profile)"
            
            # Cache the result
            self._roblox_cache[user_id] = {'name': name, 'link': link}
            return name, link
        except roblox.UserNotFound:
            return "Unknown", "Unknown"
        except Exception as e:
            self.bot.logger.error(f"Error fetching Roblox user {user_id}: {e}")
            return "Error", "Error"

    def _create_base_embed(self, title: str, ctx: commands.Context, description: str = "") -> discord.Embed:
        """Create a base embed with common styling."""
        return discord.Embed(
            title=title,
            description=description,
            color=BLANK_COLOR
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None
        ).set_footer(
            text="Cyni Bot | ERLC Integration",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
    
    async def _handle_prc_error(self, ctx: commands.Context, error: Exception, action: str):
        """Handle PRC API errors with specific messages."""
        if isinstance(error, ResponseFailed):
            if error.code == 422:
                embed = discord.Embed(
                    title="Server Offline",
                    description="Your ERLC server appears to be offline.",
                    color=YELLOW_COLOR
                )
            elif error.code == 401:
                embed = discord.Embed(
                    title="Invalid API Key",
                    description="Your server's API key is invalid. Please re-link your server.",
                    color=RED_COLOR
                )
            elif error.code == 403:
                embed = discord.Embed(
                    title="Access Denied",
                    description="Access denied to the ERLC server. Check your permissions.",
                    color=RED_COLOR
                )
            elif error.code == 429:
                embed = discord.Embed(
                    title="Rate Limited",
                    description="Too many requests. Please try again later.",
                    color=YELLOW_COLOR
                )
            else:
                embed = discord.Embed(
                    title=f"PRC API Error ({error.code})",
                    description="There seems to be an issue with the PRC API. Try again later.",
                    color=RED_COLOR
                )
        else:
            self.bot.logger.error(f"Error in {action}: {error}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while {action}.",
                color=RED_COLOR
            )
        
        return embed

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
        name="config",
        aliases=["erlc-settings"],
        extras={
            "category": "ERLC"
        }
    )
    @commands.guild_only()
    @is_erlc_management()
    async def erlc_config(self, ctx):
        """
        Configure your ERLC server settings.
        """
        if not ctx.author or not hasattr(ctx.author, 'id'):
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Unable to identify the command user.",
                    color=RED_COLOR
                )
            )
            
        try:
            if isinstance(ctx, commands.Context):
                await log_command_usage(self.bot, ctx.guild, ctx.author, "ERLC Config")
        except:
            pass
            
        try:
            sett = await self.bot.settings.find_by_id(ctx.guild.id)
            if not sett:
                sett = {}
            
            # Ensure ERLC settings structure exists
            if 'erlc' not in sett:
                sett['erlc'] = {}
                
        except KeyError:
            sett = {'erlc': {}}
            
        try:
            embed1 = discord.Embed(
                title="ERLC Staff Roles Configuration",
                description=(
                    "> Configure the roles that have access to ERLC commands.\n\n"
                    "<:anglesmallright:1268850037861908571> **ERLC Staff Roles**\n"
                    "- Roles that can use basic ERLC commands like server info, players, kills, etc.\n\n"
                    "<:anglesmallright:1268850037861908571> **ERLC Management Roles**\n"
                    "- Roles that can use management ERLC commands like linking servers and advanced configurations.\n\n"
                    "> Use the dropdowns below to select the appropriate roles for your server."
                ),
                color=BLANK_COLOR
            )
            
            embed2 = discord.Embed(
                title="ERLC Logging Channels Configuration",
                description=(
                    "> Configure where ERLC events will be logged.\n\n"
                    "<:anglesmallright:1268850037861908571> **Kill Logs Channel**\n"
                    "- Channel where ERLC kill logs will be automatically posted.\n\n"
                    "<:anglesmallright:1268850037861908571> **Join Logs Channel**\n"
                    "- Channel where ERLC join/leave logs will be automatically posted.\n\n"
                    "> Use the dropdowns below to select the appropriate channels for logging."
                ),
                color=BLANK_COLOR
            )

            all_embeds = [embed1, embed2]
            views = [
                StaffRoles(self.bot, ctx, sett),
                LoggingChannels(self.bot, ctx, sett)
            ]
            
            view = Pagination(self.bot, ctx.author.id, all_embeds, views)
            await ctx.send(embed=embed1, view=view)

        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(
                    title="Something went wrong",
                    description=f"```{e}```",
                    color=RED_COLOR
                )
            )

    @server.command(
        name="link",
        description="Link your Discord server to the ERLC server."
    )
    @is_erlc_management()
    @app_commands.describe(key="The ERLC server key.")
    async def server_link(self, ctx: commands.Context, key: str):
        """Link Discord server to ERLC server."""
        try:
            # Validate the key format
            if not key or len(key) < 10:
                embed = discord.Embed(
                    title="Invalid Key Format",
                    description="The provided key appears to be too short. Please provide a valid ERLC server key.",
                    color=RED_COLOR
                )
                return await ctx.send(embed=embed, ephemeral=True)
            
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
            
            await ctx.send(embed=embed, ephemeral=True)
            
        except ResponseFailed as e:
            embed = await self._handle_prc_error(ctx, e, "linking server")
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            self.bot.logger.error(f"Error linking server: {e}")
            embed = discord.Embed(
                title="Error",
                description="An error occurred while linking the server.",
                color=RED_COLOR
            )
            await ctx.send(embed=embed, ephemeral=True)

    @server.command(
        name="info",
        description="Get information about the ERLC server."
    )
    @is_erlc_staff()
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

            embed = self._create_base_embed(
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
            
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            
            await ctx.send(embed=embed)
            
        except ResponseFailed as e:
            embed = await self._handle_prc_error(ctx, e, "fetching server information")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = await self._handle_prc_error(ctx, e, "fetching server information")
            await ctx.send(embed=embed)

    @server.command(
        name="staff",
        description="Get information about the ERLC server staff."
    )
    @is_erlc_staff()
    @is_server_linked()
    async def erlc_staff(self, ctx: commands.Context):
        """Get information about the ERLC server staff."""
        await ctx.typing()
        
        try:
            players: List[ServerPlayers] = await self.bot.prc_api._fetch_server_players(ctx.guild.id)
            embed = self._create_base_embed("Server Staff", ctx)

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
                        name=f"{category} ({len(staff_list)})",
                        value='\n'.join(staff_links),
                        inline=False
                    )

            if not embed.fields:
                embed.description = "> There are no staff members in this server."

            await ctx.send(embed=embed)
            
        except ResponseFailed as e:
            embed = await self._handle_prc_error(ctx, e, "fetching staff information")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = await self._handle_prc_error(ctx, e, "fetching staff information")
            await ctx.send(embed=embed)

    @server.command(
        name="kills",
        description="Get the kill logs of the server."
    )
    @is_erlc_staff()
    @is_server_linked()
    async def kills(self, ctx: commands.Context):
        """Get server kill logs."""
        await ctx.typing()
        
        try:
            kill_logs: List[ServerKillLogs] = await self.bot.prc_api._fetch_server_killlogs(ctx.guild.id)
            embed = self._create_base_embed("Server Kill Logs", ctx)

            if not kill_logs:
                embed.description = "> No kill logs found."
                return await ctx.send(embed=embed)

            # Sort logs by timestamp (newest first) and build description
            sorted_logs = sorted(kill_logs, key=lambda log: log.timestamp or 0, reverse=True)
            log_entries = []
            
            for log in sorted_logs:
                if len('\n'.join(log_entries)) > 3800:  # Leave room for other embed content
                    break
                
                # Check if timestamp is valid
                timestamp_str = f"<t:{int(log.timestamp)}:R>" if log.timestamp else "Unknown time"
                    
                entry = (f"> [{log.killer_username}](https://roblox.com/users/{log.killer_user_id}/profile) "
                        f"killed [{log.killed_username}](https://roblox.com/users/{log.killed_user_id}/profile) "
                        f"• {timestamp_str}")
                log_entries.append(entry)

            embed.description = '\n'.join(log_entries) if log_entries else "> No recent kill logs found."
            await ctx.send(embed=embed)
            
        except ResponseFailed as e:
            embed = await self._handle_prc_error(ctx, e, "fetching kill logs")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = await self._handle_prc_error(ctx, e, "fetching kill logs")
            await ctx.send(embed=embed)

    @server.command(
        name="players",
        description="Get current players in the server."
    )
    @is_erlc_staff()
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
                if not player_list:
                    return "None"
                
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
                description_parts.append(f"**{status.Name} Staff [{len(staff_players)}]**\n{staff_text}")
            
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

            if not description.strip():
                description = "> No players currently online."

            embed = self._create_base_embed(f"Server Players [{len(players)}]", ctx, description)
            await ctx.send(embed=embed)

        except ResponseFailed as e:
            embed = await self._handle_prc_error(ctx, e, "fetching player information")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = await self._handle_prc_error(ctx, e, "fetching player information")
            await ctx.send(embed=embed)

    @server.command(
        name="check",
        description="Check if all ERLC players are in the Discord server."
    )
    @is_erlc_staff()
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
            
            # Create a more efficient search pattern
            member_names = set()
            for member in guild_members.values():
                member_names.add(member.name.lower())
                member_names.add(member.display_name.lower())
                if member.global_name:
                    member_names.add(member.global_name.lower())
            
            for player in players:
                member_found = False
                player_name_lower = player.username.lower()
                
                # Quick check against pre-built set
                if player_name_lower in member_names:
                    member_found = True
                else:
                    # Fallback to regex for partial matches
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

            embed = self._create_base_embed("Players in ERLC Not in Discord", ctx)
            embed.description = '\n'.join(missing_players) if missing_players else "> All players are in the Discord server."
            
            await msg.edit(embed=embed)
            
        except ResponseFailed as e:
            embed = await self._handle_prc_error(ctx, e, "performing Discord check")
            await msg.edit(embed=embed)
        except Exception as e:
            embed = await self._handle_prc_error(ctx, e, "performing Discord check")
            await msg.edit(embed=embed)

    @server.command(
        name="joinlogs",
        description="Get the join and leave logs of the server."
    )
    @is_erlc_staff()
    @is_server_linked()
    async def join_logs(self, ctx: commands.Context):
        """Get server join and leave logs."""
        embed = discord.Embed(
            title="Getting Join Logs...",
            description="Fetching server join and leave logs.",
            color=BLANK_COLOR
        )
        msg = await ctx.send(embed=embed)
        
        try:
            join_logs: List[ServerJoinLogs] = await self.bot.prc_api._fetch_server_join_logs(ctx.guild.id)
            
            if not join_logs:
                embed = discord.Embed(
                    title="No Join Logs Found",
                    description="No recent join logs were found.",
                    color=BLANK_COLOR
                )
                return await msg.edit(embed=embed)
            
            embed = self._create_base_embed("Server Join & Leave Logs", ctx)

            # Sort logs by timestamp (newest first) and build description
            sorted_logs = sorted(join_logs, key=lambda log: log.Timestamp, reverse=True)
            log_entries = []
            
            # Create user cache to reduce API calls
            username_cache = {}
            
            for log in sorted_logs:
                if len('\n'.join(log_entries)) > 3800:  # Leave room for other embed content
                    break
                
                # Parse player info
                player_parts = log.Player.split(":")
                if len(player_parts) > 1:
                    player_name = player_parts[0]
                    player_id = player_parts[1]
                    
                    # Cache usernames to reduce API calls
                    if player_id not in username_cache:
                        try:
                            username_cache[player_id] = await self.bot.roblox._get_username_by_id(int(player_id))
                        except Exception:
                            username_cache[player_id] = player_name
                    
                    player_link = f"[{username_cache[player_id]}](https://roblox.com/users/{player_id}/profile)"
                else:
                    player_name = player_parts[0]
                    player_link = player_name
                
                status = 'Joined' if log.Join else 'Left'
                # Check if timestamp is valid
                timestamp_str = f"<t:{int(log.Timestamp)}:R>" if log.Timestamp is not None else "Unknown time"
                entry = f"> **{status}:** {player_link} • {timestamp_str}"
                log_entries.append(entry)

            embed.description = '\n'.join(log_entries) if log_entries else "> No join logs found."
            await msg.edit(embed=embed)
            
        except ResponseFailed as e:
            embed = await self._handle_prc_error(ctx, e, "fetching join logs")
            await msg.edit(embed=embed)
        except Exception as e:
            embed = await self._handle_prc_error(ctx, e, "fetching join logs")
            await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(ERLC(bot))