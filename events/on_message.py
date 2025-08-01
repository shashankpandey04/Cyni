import discord
from discord.ext import commands
import logging

from numpy import block
from cyni import afk_users
import re
from datetime import timedelta, datetime
import asyncio
import time

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Track AFK user mentions
        self.afk_mentions = {}  # {user_id: [{'message_url': str, 'author': str, 'timestamp': datetime}]}
        # Pre-compile regex for better performance
        self.n_word_pattern = re.compile(r'n[i1]gg[aeiou]r?', re.IGNORECASE)
        # AutoMod tracking
        self.user_message_cache = {}  # Track user messages for spam detection
        self.link_patterns = [
            re.compile(r'https?://(?:[-\w.])+(?:\.[a-zA-Z]{2,4})+(?:/[^\s]*)?', re.IGNORECASE),
            re.compile(r'www\.(?:[-\w.])+(?:\.[a-zA-Z]{2,4})+(?:/[^\s]*)?', re.IGNORECASE),
            re.compile(r'(?:[-\w.])+\.(?:com|net|org|edu|gov|mil|int|eu|co\.uk|de|fr|it|es|nl|ca|au|jp|cn|in|br|mx|ru|za|se|no|dk|fi|pl|cz|hu|bg|ro|hr|gr|pt|ie|lu|mt|cy|lv|lt|ee|sk|si)', re.IGNORECASE)
        ]
        self.discord_invite_pattern = re.compile(r'discord\.gg/\w+|discord\.com/invite/\w+|discordapp\.com/invite/\w+', re.IGNORECASE)
        
        # AI Moderation Emoji Placeholders - Replace these with actual emojis later
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
        
        # Check if user has any exempt roles
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
            
        # Check exemptions
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
                    timestamp=datetime.utcnow()
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
                    warning_msg = await message.channel.send(
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
                    timestamp=datetime.utcnow()
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
            del afk_users[message.author.id]
            
            afk_data = await self.bot.afk.find_by_id(message.author.id)
            await self.bot.afk.delete_by_id({"_id": message.author.id})
            
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
            
            if message.author.id in self.afk_mentions:
                del self.afk_mentions[message.author.id]
                
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

    async def _handle_ai_moderation(self, message, settings):
        """Handle AI moderation tasks."""
        if not settings.get("moderation_module", {}).get("ai_moderation", {}).get("enabled", False):
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
                await message.channel.send(embed=embed)

        except Exception as e:
            logging.error(f"Error in AI moderation: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Handle all message events with optimized processing.
        """
        try:
            if message.author == self.bot.user or message.author.bot:
                return
                
            if not message.guild:
                return

            if await self._handle_ping_command(message):
                return

            if await self._handle_n_word_filter(message):
                return

            if await self._handle_afk_removal(message):
                return

            await self._handle_afk_mentions(message)

            settings = await self.bot.settings.get(message.guild.id)
            if not settings:
                return
            
            # premium = self.bot.premium.find_by_id(message.guild.id)
            # if premium and self.bot.is_premium:
            #     await self._handle_ai_moderation(message, settings)
            
            if await self._handle_automod_spam_detection(message, settings):
                pass
            
            if await self._handle_automod_keywords(message, settings):
                pass
            
            if await self._handle_automod_links(message, settings):
                pass

            await self._handle_anti_ping(message, settings)

            await self._handle_staff_activity(message, settings)

        except Exception as e:
            logging.error(f"Error in on_message event: {e}")

async def setup(bot):
    await bot.add_cog(OnMessage(bot))
