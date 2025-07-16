import discord
from discord.ext import commands
import logging
from cyni import afk_users
import re
from datetime import timedelta

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Pre-compile regex for better performance
        self.n_word_pattern = re.compile(r'n[i1]gg[aeiou]r?', re.IGNORECASE)

    async def _handle_ping_command(self, message):
        """Handle simple ping command."""
        if message.content == "ping":
            await message.channel.send("🟢 Pong!")
            return True
        return False

    async def _handle_n_word_filter(self, message):
        """Handle n-word filtering with timeout."""
        if self.n_word_pattern.search(message.content):
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, you can't say that word here!", 
                    delete_after=5
                )
                
                timeout_until = discord.utils.utcnow() + timedelta(seconds=5)
                await message.author.edit(timed_out_until=timeout_until, reason="N-word usage")
            except discord.Forbidden:
                # Log if bot doesn't have permission to timeout
                logging.warning(f"Unable to timeout user {message.author.id} for n-word usage")
            except Exception as e:
                logging.error(f"Error in n-word filter: {e}")
            return True
        return False

    async def _handle_afk_removal(self, message):
        """Handle AFK status removal when user sends a message."""
        if message.author.id not in afk_users:
            return False
            
        try:
            # Remove from memory
            del afk_users[message.author.id]
            
            # Remove from database
            await self.bot.afk.delete_by_id({"_id": message.author.id})
            
            # Remove [AFK] from nickname
            if message.author.display_name.startswith("[AFK]"):
                new_nick = message.author.display_name.replace("[AFK]", "").strip()
                await message.author.edit(nick=new_nick)
            
            # Send welcome back message
            await message.channel.send(
                f"Welcome back {message.author.mention}! I removed your AFK status.",
                delete_after=2
            )
            
        except discord.Forbidden:
            # Still remove from memory and database even if can't change nick
            pass
        except Exception as e:
            logging.error(f"Error removing AFK status: {e}")
        
        return True

    async def _handle_afk_mentions(self, message):
        """Handle mentions of AFK users."""
        if not message.mentions:
            return
            
        for mentioned_user in message.mentions:
            if mentioned_user.id in afk_users:
                try:
                    await message.channel.send(
                        f"`{mentioned_user}` is currently AFK. Reason: {afk_users[mentioned_user.id]}",
                        delete_after=15
                    )
                except Exception as e:
                    logging.error(f"Error sending AFK mention notification: {e}")

    async def _handle_anti_ping(self, message, settings):
        """Handle anti-ping module."""
        anti_ping_module = settings.get("anti_ping_module", {})
        
        if not anti_ping_module.get("enabled", False) or not message.mentions:
            return
            
        try:
            # Check if author has exempt roles
            author_role_ids = [role.id for role in message.author.roles]
            exempt_roles = anti_ping_module.get("exempt_roles", [])
            
            if any(role_id in exempt_roles for role_id in author_role_ids):
                return
            
            # Check if mentioned user has affected roles
            affected_roles = anti_ping_module.get("affected_roles", [])
            
            for mentioned_user in message.mentions:
                mentioned_role_ids = [role.id for role in mentioned_user.roles]
                
                for role_id in mentioned_role_ids:
                    if role_id in affected_roles:
                        # Find the role object for mention
                        role = message.guild.get_role(role_id)
                        if role:
                            embed = discord.Embed(
                                title="Anti-Ping Warning",
                                description=f"{message.author.mention} please do not ping users with the role {role.mention}.",
                                color=discord.Color.red()
                            ).set_image(
                                url="https://media.tenor.com/aslruXgPKHEAAAAM/discord-ping.gif"
                            )
                            
                            await message.channel.send(
                                message.author.mention,
                                embed=embed,
                                delete_after=15
                            )
                            return  # Only send one warning per message
                        
        except Exception as e:
            logging.error(f"Error in anti-ping module: {e}")

    async def _handle_staff_activity(self, message, settings):
        """Handle staff activity tracking."""
        basic_settings = settings.get('basic_settings', {})
        staff_roles = basic_settings.get('staff_roles', [])
        
        if not staff_roles or not basic_settings.get('management_roles'):
            return
            
        # Check if user has staff role
        author_role_ids = [role.id for role in message.author.roles]
        if not any(role_id in staff_roles for role_id in author_role_ids):
            return
            
        try:
            staff_data = await self.bot.staff_activity.find_by_id(message.guild.id)
            
            if not staff_data:
                # Create new staff activity record
                await self.bot.staff_activity.insert({
                    "_id": message.guild.id,
                    "staff": [{
                        "_id": message.author.id,
                        "messages": 1
                    }]
                })
            else:
                # Update existing staff member or add new one
                staff_member_found = False
                updated_staff = []
                
                for member in staff_data["staff"]:
                    if member["_id"] == message.author.id:
                        updated_staff.append({
                            "_id": message.author.id,
                            "messages": member["messages"] + 1
                        })
                        staff_member_found = True
                    else:
                        updated_staff.append(member)
                
                if not staff_member_found:
                    updated_staff.append({
                        "_id": message.author.id,
                        "messages": 1
                    })
                
                await self.bot.staff_activity.upsert({
                    "_id": message.guild.id,
                    "staff": updated_staff
                })
                
        except Exception as e:
            logging.error(f"Error updating staff activity: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Handle all message events with optimized processing.
        """
        try:
            # Early returns for efficiency
            if message.author == self.bot.user or message.author.bot:
                return
                
            if not message.guild:  # Skip DMs
                return

            # Handle ping command
            if await self._handle_ping_command(message):
                return

            # Handle n-word filter (early return if triggered)
            if await self._handle_n_word_filter(message):
                return

            # Handle AFK removal (early return if user was AFK)
            if await self._handle_afk_removal(message):
                return

            # Handle AFK mentions
            await self._handle_afk_mentions(message)

            # Get settings once and reuse
            settings = await self.bot.settings.get(message.guild.id)
            if not settings:
                return

            # Handle anti-ping module
            await self._handle_anti_ping(message, settings)

            # Handle staff activity tracking
            await self._handle_staff_activity(message, settings)

        except Exception as e:
            logging.error(f"Error in on_message event: {e}")
            
        # Process commands at the end
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(OnMessage(bot))
