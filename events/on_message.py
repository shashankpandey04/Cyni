import copy
import discord
from discord.ext import commands
import logging
import roblox

# from numpy import block
from cyni import afk_users
import re
from datetime import timedelta, datetime, timezone
# import asyncio  # Removed unused import
import time
from bson import Int64

from utils.constants import RED_COLOR
from utils.utils import get_prefix, snowflake_generator

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_mentions = {}
        self.n_word_pattern = re.compile(r'n[i1]gg[aeiou]r?', re.IGNORECASE)
        self.user_message_cache = {}
        self.link_patterns = [
            re.compile(r'https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,4})+(?:/[^\s]*)?', re.IGNORECASE),
            re.compile(r'www\.(?:[-\w.])+(?:\.[a-zA-Z]{2,4})+(?:/[^\s]*)?', re.IGNORECASE),
            re.compile(r'(?:[-\w.])+\.(?:com|net|org|edu|gov|mil|int|eu|co\.uk|de|fr|it|es|nl|ca|au|jp|cn|in|br|mx|ru|za|se|no|dk|fi|pl|cz|hu|bg|ro|hr|gr|pt|ie|lu|mt|cy|lv|lt|ee|sk|si)', re.IGNORECASE)
        ]
        self.discord_invite_pattern = re.compile(r'discord\.gg/\w+|discord\.com/invite/\w+|discordapp\.com/invite/\w+', re.IGNORECASE)
        
        self.EMOJI_PLACEHOLDER_USER = "[👤]"
        self.EMOJI_PLACEHOLDER_CHANNEL = "[📺]"
        self.EMOJI_PLACEHOLDER_TIME = "[⏰]"
        self.EMOJI_PLACEHOLDER_MESSAGE = "[💬]"
        self.EMOJI_PLACEHOLDER_SEVERITY = "[⚠️]"
        self.EMOJI_PLACEHOLDER_CONFIDENCE = "[📊]"
        self.EMOJI_PLACEHOLDER_ACTION = "[🎯]"
        self.EMOJI_PLACEHOLDER_CATEGORIES = "[🏷️]"
        self.EMOJI_PLACEHOLDER_SCORE = "[📈]"
        self.EMOJI_PLACEHOLDER_AI = "[🤖]"

    def _is_exempt_from_automod(self, member, automod_settings):
        """Check if a member is exempt from AutoMod."""
        exemptions = automod_settings.get("exemptions", {})
        exempt_roles = exemptions.get("roles", [])

        user_role_ids = [role.id for role in member.roles]
        return any(role_id in exempt_roles for role_id in user_role_ids)

    def _is_channel_exempt_from_automod(self, channel, automod_settings):
        """Check if a channel is exempt from AutoMod."""
        exemptions = automod_settings.get("exemptions", {})
        exempt_channels = exemptions.get("channels", [])
        return channel.id in exempt_channels

    async def _send_automod_alert(self, guild, alert_channel_id, embed):
        """Send AutoMod alert to specified channel."""
        if not alert_channel_id:
            return
            
        try:
            alert_channel = guild.get_channel(alert_channel_id)
            if alert_channel:
                await alert_channel.send(embed=embed)
        except Exception as e:
            logging.error(f"Error sending AutoMod alert: {e}")

    async def _handle_automod_spam_detection(self, message, settings):
        """Handle spam detection AutoMod."""
        automod_settings = settings.get("automod_module", {})
        spam_settings = automod_settings.get("spam_detection", {})
        
        if not automod_settings.get("enabled", False) or not spam_settings.get("enabled", False):
            return False

        if (self._is_exempt_from_automod(message.author, automod_settings) or 
            self._is_channel_exempt_from_automod(message.channel, automod_settings)):
            return False
            
        user_id = message.author.id
        current_time = time.time()
        
        # Initialize user cache if not exists
        if user_id not in self.user_message_cache:
            self.user_message_cache[user_id] = []
            
        # Add current message timestamp
        self.user_message_cache[user_id].append(current_time)
        
        # Clean old messages outside time window
        time_window = spam_settings.get("time_window", 3)
        self.user_message_cache[user_id] = [
            timestamp for timestamp in self.user_message_cache[user_id]
            if current_time - timestamp <= time_window
        ]
        
        # Check if threshold exceeded
        message_threshold = spam_settings.get("message_threshold", 5)
        if len(self.user_message_cache[user_id]) >= message_threshold:
            action = spam_settings.get("action", "mute")
            
            try:
                # Delete the triggering message
                await message.delete()
                
                # Take action based on settings
                if action == "mute":
                    mute_duration = spam_settings.get("mute_duration", 10)
                    timeout_until = discord.utils.utcnow() + timedelta(minutes=mute_duration)
                    await message.author.edit(timed_out_until=timeout_until, reason="AutoMod: Spam detection")
                    action_text = f"muted for {mute_duration} minutes"
                elif action == "kick":
                    await message.author.kick(reason="AutoMod: Spam detection")
                    action_text = "kicked"
                else:  # delete only
                    action_text = "messages deleted"
                
                # Send alert
                embed = discord.Embed(
                    title="🚨 AutoMod: Spam Detected",
                    description=f"**User:** {message.author.mention}\n**Action:** {action_text}\n**Channel:** {message.channel.mention}",
                    color=0xff4444,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Messages in time window", value=f"{len(self.user_message_cache[user_id])}/{message_threshold}", inline=True)
                embed.add_field(name="Time window", value=f"{time_window} seconds", inline=True)
                
                await self._send_automod_alert(message.guild, spam_settings.get("alert_channel"), embed)
                
                # Clear user cache after action
                self.user_message_cache[user_id] = []
                return True
                
            except discord.Forbidden:
                logging.warning(f"AutoMod: Insufficient permissions to handle spam from {message.author.id}")
            except Exception as e:
                logging.error(f"AutoMod spam detection error: {e}")
        
        return False

    async def _handle_automod_keywords(self, message, settings):
        """Handle custom keyword filtering."""
        automod_settings = settings.get("automod_module", {})
        keyword_settings = automod_settings.get("custom_keyword", {})
        
        if not automod_settings.get("enabled", False) or not keyword_settings.get("enabled", False):
            return False
            
        # Check exemptions
        if (self._is_exempt_from_automod(message.author, automod_settings) or 
            self._is_channel_exempt_from_automod(message.channel, automod_settings)):
            return False
            
        keywords = keyword_settings.get("keywords", [])
        if not keywords:
            return False
            
        message_content_lower = message.content.lower()
        triggered_keywords = [keyword for keyword in keywords if keyword in message_content_lower]
        
        if triggered_keywords:
            action = keyword_settings.get("action", "delete")
            
            try:
                # Always delete the message
                await message.delete()
                
                # Take additional action based on settings
                if action == "warn":
                    await message.channel.send(
                        f"{message.author.mention}, your message contained prohibited content and has been removed.",
                        delete_after=10
                    )
                elif action == "mute":
                    timeout_until = discord.utils.utcnow() + timedelta(minutes=10)
                    await message.author.edit(timed_out_until=timeout_until, reason="AutoMod: Prohibited keyword")
                
                # Send alert
                embed = discord.Embed(
                    title="🚨 AutoMod: Prohibited Keywords",
                    description=f"**User:** {message.author.mention}\n**Action:** {action}\n**Channel:** {message.channel.mention}",
                    color=0xff4444,
                    timestamp=datetime.now()
                )
                embed.add_field(name="Triggered Keywords", value=", ".join(triggered_keywords), inline=False)
                embed.add_field(name="Message Content", value=message.content[:1000] + ("..." if len(message.content) > 1000 else ""), inline=False)
                
                await self._send_automod_alert(message.guild, keyword_settings.get("alert_channel"), embed)
                return True
                
            except discord.Forbidden:
                logging.warning(f"AutoMod: Insufficient permissions to handle keyword violation from {message.author.id}")
            except Exception as e:
                logging.error(f"AutoMod keyword detection error: {e}")
        
        return False

    async def _handle_automod_links(self, message, settings):
        """Handle link blocking."""
        automod_settings = settings.get("automod_module", {})
        link_settings = automod_settings.get("link_blocking", {})

        if not automod_settings.get("enabled", False) or not link_settings.get("enabled", False):
            return False
 
        if (self._is_exempt_from_automod(message.author, automod_settings) or 
            self._is_channel_exempt_from_automod(message.channel, automod_settings)):
            return False
        
        message_content = message.content
        
        if link_settings.get("block_discord_invites", False):
            if self.discord_invite_pattern.search(message_content):
                await self._process_link_violation(message, link_settings, "Discord invite", message_content)
                return True
        
        # Check for general links
        found_links = []
        for pattern in self.link_patterns:
            found_links.extend(pattern.findall(message_content))
        
        if not found_links:
            return False
            
        block_all_links = link_settings.get("block_all_links", False)
        whitelist_mode = link_settings.get("whitelist_mode", False)
        whitelist = link_settings.get("whitelist", [])
        blacklist = link_settings.get("blacklist", [])
        
        should_block = False
        violation_reason = ""
        
        if block_all_links:
            should_block = True
            violation_reason = "All links blocked"
        elif whitelist_mode:
            # In whitelist mode, block all links not in whitelist
            should_block = not any(any(domain in link for domain in whitelist) for link in found_links)
            violation_reason = "Link not in whitelist"
        else:
            # In blacklist mode, block links in blacklist
            should_block = any(any(domain in link for domain in blacklist) for link in found_links)
            violation_reason = "Link in blacklist"
        
        if should_block:
            await self._process_link_violation(message, link_settings, violation_reason, message_content, found_links)
            return True
            
        return False

    async def _process_link_violation(self, message, link_settings, reason, content, links=None):
        """Process a link violation."""
        action = link_settings.get("action", "delete")
        
        try:
            # Always delete the message
            await message.delete()
            
            # Take additional action based on settings
            if action == "warn":
                await message.channel.send(
                    f"{message.author.mention}, links are not allowed in this channel.",
                    delete_after=10
                )
            elif action == "mute":
                timeout_until = discord.utils.utcnow() + timedelta(minutes=10)
                await message.author.edit(timed_out_until=timeout_until, reason=f"AutoMod: {reason}")
            
            # Send alert
            embed = discord.Embed(
                title="🚨 AutoMod: Link Blocked",
                description=f"**User:** {message.author.mention}\n**Reason:** {reason}\n**Action:** {action}\n**Channel:** {message.channel.mention}",
                color=0xff4444,
                timestamp=datetime.utcnow()
            )
            
            if links:
                embed.add_field(name="Blocked Links", value="\n".join(links[:5]), inline=False)
            
            embed.add_field(name="Message Content", value=content[:1000] + ("..." if len(content) > 1000 else ""), inline=False)
            
            await self._send_automod_alert(message.guild, link_settings.get("alert_channel"), embed)
            
        except discord.Forbidden:
            logging.warning(f"AutoMod: Insufficient permissions to handle link violation from {message.author.id}")
        except Exception as e:
            logging.error(f"AutoMod link blocking error: {e}")

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
            afk_data = await self.bot.afk.find_by_id(message.author.id)
    
            if message.author.display_name.startswith("[AFK]"):
                new_nick = message.author.display_name.replace("[AFK]", "").strip()
                await message.author.edit(nick=new_nick)
            
            welcome_msg = f"Welcome back {message.author.mention}! I removed your AFK status."
            
            if afk_data and afk_data.get("pings"):
                mentions_count = len(afk_data["pings"])
                welcome_msg += f"\n\n**You were mentioned {mentions_count} time(s) while AFK:**"
                
                recent_mentions = afk_data["pings"][-5:]
                for ping in recent_mentions:
                    welcome_msg += f"\n-# {ping['author']} mentioned you: [Jump to message]({ping['message_url']})"
                
                if mentions_count > 5:
                    welcome_msg += f"\n*...and {mentions_count - 5} more mentions*"
            
            await message.channel.send(welcome_msg, delete_after=15)
            await self.bot.afk.delete_by_id(message.author.id)
            del afk_users[message.author.id]
                
        except discord.Forbidden:
            pass
        return True

    async def _handle_afk_mentions(self, message):
        """Handle mentions of AFK users."""
        if not message.mentions:
            return
            
        for mentioned_user in message.mentions:
            if mentioned_user.id in afk_users:
                try:
                    afk_data = await self.bot.afk.find_by_id(mentioned_user.id)
                    
                    message_url = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                    
                    ping_data = {
                        'message_url': message_url,
                        'author': str(message.author),
                        'timestamp': message.created_at
                    }
                    
                    if afk_data:
                        current_pings = afk_data.get("pings", [])
                        current_pings.append(ping_data)
                        
                        await self.bot.afk.upsert({
                            "_id": mentioned_user.id,
                            "reason": afk_data.get("reason", "No reason provided"),
                            "pings": current_pings,
                            "timestamp": afk_data.get("timestamp")
                        })
                    
                    afk_reason = afk_users[mentioned_user.id]
                    timestamp_text = ""
                    
                    if afk_data and afk_data.get("timestamp"):
                        timestamp_text = f" (AFK since {afk_data['timestamp']})"
                    
                    await message.channel.send(
                        f"`{mentioned_user}` is currently AFK{timestamp_text}. Reason: {afk_reason}",
                        delete_after=15
                    )
                    
                except Exception as e:
                    logging.error(f"Error handling AFK mention notification: {e}")
                    await message.channel.send(
                        f"`{mentioned_user}` is currently AFK. Reason: {afk_users[mentioned_user.id]}",
                        delete_after=15
                    )

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
            
            affected_roles = anti_ping_module.get("affected_roles", [])
            
            for mentioned_user in message.mentions:
                mentioned_role_ids = [role.id for role in mentioned_user.roles]
                
                for role_id in mentioned_role_ids:
                    if role_id in affected_roles:
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
                            return
                        
        except Exception as e:
            logging.error(f"Error in anti-ping module: {e}")

    async def _handle_staff_activity(self, message, settings):
        """Handle staff activity tracking."""
        if not isinstance(message.author, discord.Member):
            return
        if message.author.bot:
            return
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

    async def _handle_custom_commands(self, message):
        """Handle custom commands."""
        if not isinstance(message.author, discord.Member):
            return
        prefix_list = await get_prefix(self.bot, message)
        prefix = prefix_list[-1]
        doc = await self.bot.custom_commands.find_by_id(message.guild.id)
        if not doc:
            return
        if not message.content.startswith(prefix):
            return
        command_name = message.content[len(prefix):].split(" ")[0]
        command_data = doc.get(command_name)
        if not command_data:
            return
        try:
            embed = None
            if command_data.get("title") or command_data.get("description"):
                embed  = discord.Embed(
                    title=command_data.get("title"),
                    description=command_data.get("description"),
                    color=command_data.get("color", discord.Color.blue().value)
                )
            if command_data.get("image") and embed:
                embed.set_image(url=command_data["image"])
            if command_data.get("thumbnail") and embed:
                embed.set_thumbnail(url=command_data["thumbnail"])
            if command_data.get("footer") and embed:
                embed.set_footer(text=command_data["footer"])
            if command_data.get("timestamp") and embed:
                embed.timestamp = datetime.fromtimestamp(command_data["timestamp"])
            if command_data.get("fields") and embed:
                for field in command_data["fields"]:
                    embed.add_field(
                        name=field.get("name", "No Name"),
                        value=field.get("value", "No Value"),
                        inline=field.get("inline", False)
                    )
            if embed and command_data.get("message"):
                await message.channel.send(content=command_data["message"], embed=embed)
            elif embed:
                await message.channel.send(embed=embed)
            elif command_data.get("message"):
                await message.channel.send(content=command_data["message"])
            await message.delete()

        except Exception as e:
            pass

    async def _handle_ai_moderation(self, message, settings):
        """Handle AI moderation tasks."""
        if not settings.get("automod_module", {}).get("ai_automod", {}).get("enabled", False):
            return

        try:
            response = await self.bot.modai.moderate(message.content)
            if response:
                if response.get("confidence", 0.0) < 0.5:
                    return
                if response.get("severity_level") == "clean":
                    return

                severity = response.get("severity_level", "clean")
                color_map = {
                    "clean": 0x00ff00,      # Green
                    "mild": 0xffff00,       # Yellow
                    "moderate": 0xff8800,   # Orange
                    "severe": 0xff0000      # Red
                }
                embed_color = color_map.get(severity, 0xff4444)
                
                embed = discord.Embed(
                    title=f"{self.bot.emoji.get('automod')} CYNI AI Moderation",
                    #description=f"**{self.EMOJI_PLACEHOLDER_USER}** User: {message.author.mention} ({message.author.id})\n**{self.EMOJI_PLACEHOLDER_CHANNEL}** Channel: {message.channel.mention}\n**{self.EMOJI_PLACEHOLDER_TIME}** Time: <t:{int(message.created_at.timestamp())}:R>",
                    color=embed_color,
                ).add_field(
                    name=f"> **User**",
                    value=f"{message.author.mention} ({message.author.id})",
                    inline=True
                ).add_field(
                    name=f"> **Channel**",
                    value=message.channel.mention,
                    inline=True
                ).add_field(
                    name=f"> **Timestamp**",
                    value=f"<t:{int(message.created_at.timestamp())}:R>",
                    inline=True
                )
                
                message_content = message.content
                if len(message_content) > 800:
                    message_content = message_content[:800] + "..."
                
                embed.add_field(
                    name=f"{self.EMOJI_PLACEHOLDER_MESSAGE} **Message Content**",
                    value=f"```{message_content}```",
                    inline=False
                )
                
                confidence_percentage = f"{response.get('confidence', 0.0) * 100:.1f}%"
                embed.add_field(
                    name=f"{self.EMOJI_PLACEHOLDER_SEVERITY} **Severity**",
                    value=f"`{severity.title()}`",
                    inline=True
                ).add_field(
                    name=f"{self.EMOJI_PLACEHOLDER_CONFIDENCE} **Confidence**",
                    value=f"`{confidence_percentage}`",
                    inline=True
                ).add_field(
                    name=f"{self.EMOJI_PLACEHOLDER_ACTION} **Recommended Action**",
                    value=f"`{response.get('recommended_action', 'unknown').replace('_', ' ').title()}`",
                    inline=True
                )
                
                categories = response.get("categories", [])
                if categories:
                    embed.add_field(
                        name=f"{self.EMOJI_PLACEHOLDER_CATEGORIES} **Detected Categories**",
                        value=f"`{', '.join(cat.replace('_', ' ').title() for cat in categories)}`",
                        inline=False
                    )
                
                toxicity_score = response.get("toxicity_score", 0.0)
                score_bar = "█" * int(toxicity_score * 10) + "░" * (10 - int(toxicity_score * 10))
                embed.add_field(
                    name=f"{self.EMOJI_PLACEHOLDER_SCORE} **Toxicity Score**",
                    value=f"`{toxicity_score:.2f}` {score_bar} `({toxicity_score * 100:.1f}%)`",
                    inline=False
                )
                
                embed.set_footer(
                    text=f"CYNI AI Moderation System",
                    icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                )
                logger = self.bot.get_cog("ThrottledLogger")
                alert_channel = self.bot.get_channel(settings.get("automod_module", {}).get("ai_automod", {}).get("alert_channel"))
                await logger.log_embed(alert_channel, embed)

                action = settings.get("automod_module", {}).get("ai_automod", {}).get("action")
                if action == "delete":
                    await message.delete()
                if action == "mute":
                    total_warnings = await self.bot.warnings.find(
                        {
                            'guild_id': message.guild.id
                        }
                    )
                    total_warnings = len(total_warnings)

                    doc = {
                        'guild_id': message.guild.id,
                        'user_id': message.author.id,
                        'reason': f"AI Moderation `{message.content}`",
                        'moderator_id': self.bot.user.id,
                        'timestamp': datetime.now().timestamp(),
                        'case_id': total_warnings + 1,
                        'active': True,
                        'void': False,
                        'type': 'mute',
                    }
                    mute_duration = settings.get("automod_module", {}).get("ai_automod", {}).get("mute_duration", 60)
                    embed = discord.Embed(
                        title="You have been muted",
                        description=f"You have been muted for {mute_duration} seconds.",
                        color=discord.Color.orange()
                    )
                    await message.channel.send(
                        embed=embed
                    )
                    try:
                        await message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(minutes=mute_duration), reason="AI Moderation")
                    except discord.Forbidden:
                        await message.channel.send("I cannot mute this user.")
                    await self.bot.warnings.insert_one(doc)
                elif action == "kick":
                    total_warnings = await self.bot.warnings.find(
                        {
                            'guild_id': message.guild.id
                        }
                    )
                    total_warnings = len(total_warnings)

                    doc = {
                        'guild_id': message.guild.id,
                        'user_id': message.author.id,
                        'reason': f"AI Moderation `{message.content}`",
                        'moderator_id': self.bot.user.id,
                        'timestamp': datetime.now().timestamp(),
                        'case_id': total_warnings + 1,
                        'active': True,
                        'void': False,
                        'type': 'kick',
                    }
                    await self.bot.warnings.insert_one(doc)
                    await message.author.kick(reason="AI Moderation")
                    await message.channel.send(
                        content=f"**Case #{total_warnings + 1}**: {message.author.mention} has been kicked by AI moderation.",
                    )
                    await message.author.send(
                        embed=discord.Embed(
                            title="You have been kicked",
                            description=f"You have been kicked from {message.guild.name} for {doc['reason']}",
                            color=discord.Color.red()
                        )
                    )


        except Exception as e:
            logging.error(f"Error in AI moderation: {e}")

    async def _handle_erlc_logging(self, message):
        """
        Handle ERLC logging for messages.
        """
        settings = await self.bot.settings.find_by_id(message.guild.id)
        if not settings:
            return
        remote_command_channel_id = settings.get("erlc", {}).get("kick_ban_log_channel")
        #self.bot.logger.info(f"Logging ERLC actions to channel: {remote_command_channel_id}")
        channel = self.bot.get_channel(remote_command_channel_id)
        if (
            channel and remote_command_channel_id
        ):
            for embed in message.embeds:
                if not embed.description or not embed.title:
                    continue

                if "Player Kicked" in embed.title:
                    action_type = "Kick"
                elif "Player Banned" in embed.title:
                    action_type = "Ban"
                else:
                    continue
                #self.bot.logger.info(f"Processing ERLC embed for action: {action_type}")

                raw_content = embed.description

                if ("kicked" not in raw_content and action_type == "Kick") or (
                    "banned" not in raw_content and action_type == "Ban"
                ):
                    continue

                try:
                    if action_type == "Kick":
                        user_info, command_info = raw_content.split("kicked ", 1)
                    else:
                        user_info, command_info = raw_content.split("banned ", 1)

                    user_info = user_info.strip()
                    command_info = command_info.strip()
                    roblox_user = (
                        user_info.split(":")[0]
                        .replace("[", "")
                        .replace("]", "")
                        .strip()
                    )
                    profile_link = user_info.split("(")[1].split(")")[0].strip()
                    roblox_id_str = profile_link.split("/")[-2]

                    if not roblox_id_str.isdigit():
                        self.bot.logger.error(
                            f"Extracted Roblox ID is not a number: {roblox_id_str}"
                        )
                        raise ValueError(
                            f"Extracted Roblox ID is not a number: {roblox_id_str}"
                        )

                    roblox_id = int(roblox_id_str)
                    #self.bot.logger.info(f"Extracted Roblox ID: {roblox_id}")

                    reason = command_info.split("`")[1].strip()
                    #self.bot.logger.info(f"Extracted reason: {reason}")
                except (IndexError, ValueError):
                    continue

                discord_user = 0
                document = await self.bot.roblox_oauth.find_one(
                    {"roblox_user_id": roblox_id}
                )
                if document:
                    discord_user = document["discord_user_id"]

                if discord_user == 0:
                    await message.add_reaction("❌")
                    return await message.add_reaction("🔗")

                user = message.guild.get_member(discord_user)
                if not user:
                    try:
                        user = await message.guild.fetch_member(discord_user)
                    except Exception as e:
                        await message.add_reaction("❌")
                        return await message.add_reaction("🔍")

                new_message = copy.copy(message)
                new_message.author = user
                prefix = (await get_prefix(self.bot, message))[-1]
                reason_info = command_info.split("`")[1].strip()
                split_index = reason_info.find(" ")
                if split_index != -1:
                    violator_user = reason_info[:split_index].strip()
                    reason = reason_info[split_index:].strip()
                else:
                    await message.add_reaction("❌")
                    return await message.add_reaction(
                        "📃"
                    )
                if reason.endswith("- Player Not In Game"):
                    reason = reason[: -len("- Player Not In Game")]
                if not reason:
                    await message.add_reaction("❌")
                    return await message.add_reaction(
                        "📃"
                    )
                #self.bot.logger.info(f"Logging ERLC action: {action_type} for user: {violator_user}")
                new_message.content = (
                    f"{prefix}punishments log {violator_user} {action_type} {reason}"
                )
                #self.bot.logger.info(f"Processed command: {new_message.content}")
                await self.bot.process_commands(new_message)
        
    async def _check_shift_status(self, message, shift):
        status = "offduty"
        break_count = 0
        shift_data = None
        
        active_shift = await self.bot.shift_logs.find(
            {
                "guild_id": message.guild.id,
                "user_id": message.author.id,
                "type": shift.lower(),
                "end_epoch": 0
            }
        )
        if active_shift:
            shift_data = active_shift[0] if len(active_shift) > 0 else {}
            
            if shift_data:
                status = "onduty"
                breaks = shift_data.get("breaks", [])
                break_count = len(breaks)

                # Check if any break is currently active
                if breaks:
                    for b in breaks:
                        if isinstance(b, dict):
                            if b.get("end_epoch", 0) == 0:
                                status = "onbreak"
                                break
                        elif isinstance(b, list) and len(b) > 1:
                            if len(b) < 2 or b[1] == 0:
                                status = "onbreak"
                                break
            return status

    async def _start_shift_callback(self, message, shift_type):
        timestamp = int(datetime.now().timestamp())

        active_shift = await self.bot.shift_logs.find(
            {
                "guild_id": message.guild.id,
                "user_id": message.author.id,
                "type": shift_type.lower(),
                "end_epoch": 0
            }
        )
        shift_data = None
        if active_shift:
            shift_data = active_shift[0] if len(active_shift) > 0 else {}
            
        status = await self._check_shift_status(message, shift_type)

        if status == "onbreak":
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": message.author.id,
                    "type": shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        f"breaks.{len(shift_data.get('breaks', [])) - 1}.end_epoch": timestamp
                    }
                }
            )
            oid = await self.bot.shift_logs.find_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": message.author.id,
                    "type": shift_type.lower(),
                    "end_epoch": 0
                }
            )
            self.bot.dispatch("shift_break", oid["_id"], "end", timestamp)
            success_message = "Break ended! You are now back on duty."
        else:
            doc = {
                "guild_id": message.guild.id,
                "user_id": message.author.id,
                "username": message.author.name,
                "nickname": message.author.nick if message.author.nick else message.author.name,
                "type": shift_type.lower(),
                "start_epoch": timestamp,
                "end_epoch": 0,
                "breaks": [],
                "added_time": 0,
                "removed_time": 0,
                "moderations": [],
                "duration": 0
            }
            await self.bot.shift_logs.insert_one(doc)
            success_message = "Shift started successfully!"
            doc_id = await self.bot.shift_logs.find_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": message.author.id,
                    "type": shift_type.lower(),
                    "start_epoch": timestamp
                }
            )
            self.bot.dispatch("shift_start", doc_id["_id"])

        await message.channel.send(
            content=f"{message.author.mention} {success_message}",
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('onshift')} Shift Action",
                description=success_message,
                color=discord.Color.green()
            )
        )
        return await message.add_reaction("✅")

    async def _end_shift_callback(self, message, shift_type):
        timestamp = int(datetime.now().timestamp())

        shift_data = await self.bot.shift_logs.find_one(
            {
                "guild_id": message.guild.id,
                "user_id": message.author.id,
                "type": shift_type.lower(),
                "end_epoch": 0
            }
        )

        if shift_data and shift_data.get("status") == "onbreak":
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": message.author.id,
                    "type": shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        f"breaks.{len(shift_data.get('breaks', [])) - 1}.end_epoch": timestamp
                    }
                }
            )

            shift_data = await self.bot.shift_logs.find_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": message.author.id,
                    "type": shift_type.lower(),
                    "end_epoch": 0
                }
            )

        start_time = shift_data.get('start_epoch', timestamp) if shift_data else timestamp
        end_time = timestamp

        total_duration = end_time - start_time

        total_break_time = 0
        if shift_data and "breaks" in shift_data:
            for b in shift_data["breaks"]:
                if isinstance(b, dict):
                    break_start = b.get("start_epoch")
                    break_end = b.get("end_epoch")
                    
                    if break_start is not None and break_end is not None:
                        effective_start = max(start_time, break_start)
                        effective_end = min(end_time, break_end)
                        
                        if effective_end > effective_start:
                            total_break_time += (effective_end - effective_start)

        duration = max(total_duration - total_break_time, 0)
        
        #print(f"Total shift: {total_duration}s, Break time: {total_break_time}s, Working time: {duration}s")
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60

        await self.bot.shift_logs.update_one(
            {
                "guild_id": message.guild.id,
                "user_id": message.author.id,
                "type": shift_type.lower(),
                "end_epoch": 0,
            },
            {
                "$set": {
                    "end_epoch": timestamp,
                    "duration": duration
                }
            }
        )
        
        doc_id = await self.bot.shift_logs.find_one(
            {
                "guild_id": message.guild.id,
                "user_id": message.author.id,
                "type": shift_type.lower(),
                "end_epoch": timestamp
            }
        )
        
        self.bot.dispatch("shift_end", doc_id["_id"])
        
        await message.channel.send(
            content=f"{message.author.mention} Shift ended.",
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('onshift')} Shift Action",
                description=f"Shift ended. Duration: {hours}h {minutes}m {seconds}s",
                color=discord.Color.red()
            )
        )
        return await message.add_reaction("✅")

    async def _start_break_callback(self, message, shift_type):
        timestamp = int(datetime.now().timestamp())
        
        new_break = {
            "start_epoch": timestamp,
            "end_epoch": 0
        }

        try:
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": message.author.id,
                    "type": shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$push": {"breaks": new_break}
                }
            )
            oid = await self.bot.shift_logs.find_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": message.author.id,
                    "type": shift_type.lower(),
                    "end_epoch": 0
                }
            )
        except Exception as e:
            return await message.channel.send(
                content=f"{message.author.mention} There was an error starting your break.",
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('error')} Error",
                    description="There was an error starting your break.",
                    color=discord.Color.red(),
                )
            )
        self.bot.dispatch("shift_break", oid["_id"], "start", timestamp)
        await message.channel.send(
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('shiftbreak')} Break Started",
                description="You are now on break.",
                color=discord.Color.from_rgb(255, 255, 0),
            )
        )
        return await message.add_reaction("✅")

    async def _log_erlc_punishment(self, username: str, punishment: str, reason: str, message: discord.Message):
        """
        View Roblox punishments for a user.
        """
        try:
            await message.channel.typing()
            if punishment not in ["Warning", "Kick", "Ban", "Bolo"]:
                return await message.channel.send(
                    embed=discord.Embed(
                        title="Invalid Punishment",
                        description=(
                            f"> The punishment `{punishment}` is not a valid punishment type.\n"
                            f"> Please choose from the following: `Warning`, `Kick`, `Ban`, `Bolo`."
                        ),
                        color=RED_COLOR
                    )
                )
            
            setting = await self.bot.settings.find_by_id(message.guild.id)
            if setting is None:
                return await message.channel.send(
                    embed=discord.Embed(
                        title="Missing Settings",
                        description="Please configure the settings for this server.",
                        color=discord.Color.red()
                    )
                )

            if not setting.get("roblox", {}).get("punishments"):
                return await message.channel.send(
                    embed=discord.Embed(
                        title="Missing Punishments",
                        description="Please configure the punishments for this server.",
                        color=discord.Color.red()
                    )
                )
            
            punishment_doc = setting["roblox"]["punishments"]
            if not punishment_doc.get("enabled", False):
                return await message.channel.send(
                    embed=discord.Embed(
                        title="Punishments Disabled",
                        description="Roblox punishments are not enabled for this server.",
                        color=discord.Color.red()
                    )
                )

            channel_id = punishment_doc.get("channel")
            if not channel_id:
                return await message.channel.send(
                    embed=discord.Embed(
                        title="Missing Channel",
                        description="Please configure the punishment log channel for this server.",
                        color=discord.Color.red()
                    )
                )

            roblox_user = await self.bot.roblox.get_user_by_username(username)
            if roblox_user is None:
                return await message.channel.send(
                    embed=discord.Embed(
                        title="Player Not Found",
                        description=(
                            f"> There was an issue while finding the Roblox User: `{username}`. "
                            f"> Please make sure you have entered correct username."
                        ),
                        color=RED_COLOR
                    )
                )
            
            roblox_player = await self.bot.roblox.get_user(roblox_user.id)
            thumbnails = await self.bot.roblox.thumbnails.get_user_avatar_thumbnails(
                [roblox_player], type=roblox.thumbnails.AvatarThumbnailType.headshot
            )
            if not thumbnails or not thumbnails[0]:
                return await message.channel.send(
                    embed=discord.Embed(
                        title="Thumbnail Error",
                        description="Could not retrieve the user's avatar thumbnail.",
                        color=RED_COLOR
                    )
                )
            thumbnail = thumbnails[0].image_url

            timestamp = datetime.now().timestamp()

            doc = {
                "moderator_id": message.author.id,
                "moderator_name": message.author.name,
                "user_id": roblox_player.id,
                "user_name": roblox_player.name,
                "guild_id": message.guild.id,
                "reason": reason,
                "type": punishment.lower(),
                "timestamp": timestamp,
                "snowflake": next(snowflake_generator),
            }

            await self.bot.punishments.insert_one(doc)

            warning = await self.bot.punishments.find_one(
                {
                    "guild_id": message.guild.id,
                    "user_id": roblox_player.id,
                    "type": punishment.lower(),
                    "timestamp": timestamp,
                    "moderator_id": message.author.id,
                }
            )
            self.bot.dispatch("punishment", warning["_id"], message.author, thumbnail)

            await message.add_reaction("✅")

        except Exception as e:
            self.bot.logger.error(f"Error logging punishment: {e}")

    async def _handle_command_logs(self, message):
        settings = await self.bot.settings.find_by_id(message.guild.id)
        if not settings:
            return
        remote_command_channel_id = settings.get("erlc", {}).get("command_log_channel")
        #self.bot.logger.info(f"Logging ERLC actions to channel: {remote_command_channel_id}")
        channel = self.bot.get_channel(remote_command_channel_id)
        if (
            channel and remote_command_channel_id
        ):
            for embed in message.embeds:
                if not embed.description or not embed.title:
                    continue

                if "used the command" in embed.description and ":log" in embed.description:
                    try:
                        user_info, _ = embed.description.split("used the command", 1)
                        user_info = user_info.strip()
                        profile_link = user_info.split("(")[1].split(")")[0].strip()
                        roblox_id_str = profile_link.split("/")[-2]

                        if not roblox_id_str.isdigit():
                            #self.bot.logger.error(f"Extracted Roblox ID is not a number: {roblox_id_str}")
                            raise ValueError(f"Extracted Roblox ID is not a number: {roblox_id_str}")

                        roblox_id = int(roblox_id_str)
                        #self.bot.logger.info(f"Extracted Roblox ID: {roblox_id}")

                        document = await self.bot.roblox_oauth.find_one({"roblox_user_id": roblox_id})
                        if not document:
                            await message.add_reaction("❌")
                            return await message.add_reaction("🔗")

                        discord_user_id = document["discord_user_id"]
                        user = message.guild.get_member(discord_user_id)
                        if not user:
                            try:
                                user = await message.guild.fetch_member(discord_user_id)
                            except Exception:
                                await message.add_reaction("❌")
                                return await message.add_reaction("🔍")

                        new_message = copy.copy(message)
                        new_message.author = user
                        shift_type = None
                        if "shift" in embed.description:
                            shift_type = "Default"
                            if "shift start" in embed.description:
                                await self._start_shift_callback(new_message, shift_type)
                            elif "shift break" in embed.description:
                                await self._start_break_callback(new_message, shift_type)
                            elif "shift end" in embed.description:
                                await self._end_shift_callback(new_message, shift_type)
                        elif "punishments log" in embed.description:
                            try:
                                command_parts = embed.description.split(":log punishments log ", 1)[1].strip().split()
                                if len(command_parts) >= 3:
                                    username = command_parts[0]
                                    punishment = command_parts[1]
                                    reason = " ".join(command_parts[2:])
                                    reason = reason.replace("`", "")
                                    await self._log_erlc_punishment(username=username, punishment=punishment, reason=reason, message=new_message)
                                else:
                                    await message.add_reaction("❌")
                                    return await message.channel.send(
                                        embed=discord.Embed(
                                            title="Invalid Command Format",
                                            description="The punishment log command is missing required arguments.",
                                            color=discord.Color.red()
                                        )
                                    )
                            except Exception as e:
                                logging.error(f"Error processing punishment log command: {e}")
                                await message.add_reaction("❌")
                        else:
                            await message.add_reaction("❌")
                            return await message.add_reaction("🔄")

                    except (IndexError, ValueError) as e:
                        self.bot.logger.error(f"Error processing shift start command: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Handle all message events with optimized processing.
        """
        try:
            if message.author == self.bot.user:
                return

            if not message.guild:
                return

            if message.webhook_id:
                await self._handle_erlc_logging(message)
                await self._handle_command_logs(message)
                return

            await self._handle_ping_command(message)

            await self._handle_afk_removal(message)

            await self._handle_afk_mentions(message)

            settings = await self.bot.settings.find_by_id(message.guild.id)
            if not settings:
                return

            await self._handle_ai_moderation(message, settings)

            await self._handle_automod_spam_detection(message, settings)

            await self._handle_automod_keywords(message, settings)

            await self._handle_automod_links(message, settings)

            await self._handle_anti_ping(message, settings)

            await self._handle_staff_activity(message, settings)

            await self._handle_custom_commands(message)

        except Exception as e:
            logging.error(f"Error in on_message event: {e}")

async def setup(bot):
    await bot.add_cog(OnMessage(bot))