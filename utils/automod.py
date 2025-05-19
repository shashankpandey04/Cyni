import discord
import re
import datetime
import logging
from collections import defaultdict
from discord.ext import commands
from better_profanity import profanity
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

CUSTOM_BLACKLIST = ["kys"]

def normalize_text(text):
    leet_dict = {'@': 'a', '4': 'a', '$': 's', '1': 'i', '3': 'e', '0': 'o'}
    text = ''.join(leet_dict.get(c.lower(), c.lower()) for c in text)
    return re.sub(r'\s+', '', text.lower())

def is_custom_blacklisted(text):
    normalized = normalize_text(text)
    return any(phrase in normalized for phrase in CUSTOM_BLACKLIST)

def is_negative_sentiment(text, threshold=-0.6):
    score = sia.polarity_scores(text)
    return score['compound'] < threshold

def is_profane(text):
    return profanity.contains_profanity(text)

# Store message timestamps for spam detection
user_message_times = defaultdict(list)

async def is_exempt_from_automod(message, bot, automod_settings):
    """Check if a user or channel is exempt from AutoMod."""
    # Admins are always exempt
    if message.author.guild_permissions.administrator:
        return True
    
    # Check exempt roles
    exempt_settings = automod_settings.get("exemptions", {})
    exempt_roles = exempt_settings.get("roles", [])
    if any(role.id in exempt_roles for role in message.author.roles):
        return True
    
    # Check exempt channels
    exempt_channels = exempt_settings.get("channels", [])
    if message.channel.id in exempt_channels:
        return True
    
    return False

async def check_for_spam(message, bot, spam_settings):
    """Check if a user is spamming messages."""
    user_id = f"{message.author.id}-{message.guild.id}"
    threshold = spam_settings.get("message_threshold", 5)
    time_window = spam_settings.get("time_window", 3)
    
    # Add current message timestamp
    current_time = datetime.datetime.now().timestamp()
    user_message_times[user_id].append(current_time)
    
    # Remove timestamps outside the time window
    user_message_times[user_id] = [t for t in user_message_times[user_id] 
                                  if current_time - t <= time_window]
    
    # Check if user exceeded threshold
    message_count = len(user_message_times[user_id])
    
    if message_count >= threshold:
        return True, {
            "count": message_count,
            "seconds": time_window
        }
    
    return False, {}

async def check_for_banned_keywords(message, bot, keyword_settings):
    """Check if a message contains banned keywords."""
    keywords = keyword_settings.get("keywords", [])
    
    # No keywords to check
    if not keywords:
        return False, {}
    
    content = message.content.lower()
    
    for keyword in keywords:
        if keyword.lower() in content:
            return True, {
                "keyword": keyword
            }
    
    return False, {}

async def check_for_banned_links(message, bot, link_settings):
    """Check if a message contains banned links."""
    # Regular expression to detect URLs
    url_pattern = re.compile(r'(https?://[^\s]+)|(www\.[^\s]+)|([a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,})')
    
    # Regular expression to detect Discord invites
    invite_pattern = re.compile(r'(discord\.gg\/[a-zA-Z0-9]+)|(discordapp\.com\/invite\/[a-zA-Z0-9]+)|(discord\.com\/invite\/[a-zA-Z0-9]+)')
    
    content = message.content.lower()
    
    # Check for Discord invites if they should be blocked
    if link_settings.get("block_discord_invites", False):
        if invite_pattern.search(content):
            return True, {
                "type": "Discord invite",
                "link": invite_pattern.search(content).group(0)
            }
    
    # Check for URLs
    urls = url_pattern.findall(content)
    if not urls:
        return False, {}
    
    # If block all links is enabled
    if link_settings.get("block_all_links", False):
        # Extract the first URL found
        first_url = next((u for u in urls if u[0] or u[1] or u[2]), None)
        if first_url:
            url = first_url[0] or first_url[1] or first_url[2]
            return True, {
                "type": "URL",
                "link": url
            }
    
    # Process based on whitelist/blacklist mode
    whitelist = link_settings.get("whitelist", [])
    blacklist = link_settings.get("blacklist", [])
    whitelist_mode = link_settings.get("whitelist_mode", False)
    
    for url_tuple in urls:
        url = url_tuple[0] or url_tuple[1] or url_tuple[2]
        
        # Extract domain from URL
        domain = url.split('//')[-1].split('/')[0]
        if domain.startswith('www.'):
            domain = domain[4:]
        
        if whitelist_mode:
            # In whitelist mode, block all domains not in whitelist
            if not any(whitelisted_domain in domain for whitelisted_domain in whitelist):
                return True, {
                    "type": "non-whitelisted URL",
                    "link": url
                }
        else:
            # In blacklist mode, only block domains in blacklist
            if any(blacklisted_domain in domain for blacklisted_domain in blacklist):
                return True, {
                    "type": "blacklisted URL",
                    "link": url
                }
    
    return False, {}

async def take_automod_action(message, bot, action, violation_type, violation_data):
    """Take appropriate action based on AutoMod settings."""
    try:
        # Always try to delete the message first
        await message.delete()
        
        # Apply additional actions
        if action == "warn":
            # Log warning in the database
            warning_data = {
                "user_id": message.author.id,
                "guild_id": message.guild.id,
                "reason": f"AutoMod: {violation_type} violation",
                "timestamp": datetime.datetime.now().timestamp(),
                "moderator_id": bot.user.id,
                "moderator_name": str(bot.user)
            }
            
            # Add to warnings collection if available
            if hasattr(bot, 'warnings'):
                await bot.warnings.insert_one(warning_data)
                
            # DM the user
            try:
                await message.author.send(f"⚠️ You have been warned in {message.guild.name} for a {violation_type} violation.")
            except:
                # Cannot DM the user, continue silently
                pass
                
        elif action == "mute" or action == "timeout":
            # Get timeout duration from settings, default to 10 minutes
            duration = violation_data.get("mute_duration", 10)
            timeout_duration = datetime.timedelta(minutes=duration)
            
            # Apply timeout
            try:
                await message.author.timeout(timeout_duration, reason=f"AutoMod: {violation_type} violation")
                
                # DM the user
                try:
                    await message.author.send(
                        f"⏱️ You have been timed out in {message.guild.name} for {duration} minutes due to a {violation_type} violation."
                    )
                except:
                    # Cannot DM the user, continue silently
                    pass
            except discord.Forbidden:
                logging.warning(f"Cannot timeout user {message.author.id} in guild {message.guild.id}: Missing permissions")
            except Exception as e:
                logging.error(f"Error timeout user: {e}")
                
        elif action == "kick":
            try:
                # DM the user before kicking
                try:
                    await message.author.send(
                        f"👢 You have been kicked from {message.guild.name} for a {violation_type} violation."
                    )
                except:
                    # Cannot DM the user, continue silently
                    pass
                    
                await message.guild.kick(message.author, reason=f"AutoMod: {violation_type} violation")
            except discord.Forbidden:
                logging.warning(f"Cannot kick user {message.author.id} in guild {message.guild.id}: Missing permissions")
            except Exception as e:
                logging.error(f"Error kicking user: {e}")
                
        elif action == "ban":
            try:
                # DM the user before banning
                try:
                    await message.author.send(
                        f"🔨 You have been banned from {message.guild.name} for a {violation_type} violation."
                    )
                except:
                    # Cannot DM the user, continue silently
                    pass
                    
                await message.guild.ban(message.author, reason=f"AutoMod: {violation_type} violation", delete_message_days=1)
            except discord.Forbidden:
                logging.warning(f"Cannot ban user {message.author.id} in guild {message.guild.id}: Missing permissions")
            except Exception as e:
                logging.error(f"Error banning user: {e}")
    except Exception as e:
        logging.error(f"Error applying AutoMod action: {e}")

async def send_automod_alert(message, bot, settings, violation_title, violation_details):
    """Send an alert to the designated channel about an AutoMod action."""
    alert_channel_id = settings.get("alert_channel")
    if not alert_channel_id:
        return
    
    alert_channel = message.guild.get_channel(alert_channel_id)
    if not alert_channel:
        return
    
    try:
        embed = discord.Embed(
            title=f"🛡️ AutoMod: {violation_title}",
            description=f"AutoMod has detected a violation in {message.channel.mention}",
            color=0xE74C3C,  # Red color
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="User", value=f"{message.author.mention} ({message.author.name}#{message.author.discriminator})", inline=False)
        embed.add_field(name="Violation", value=violation_details, inline=False)
        
        # Add message content preview if available
        if message.content:
            content_preview = message.content
            if len(content_preview) > 1024:
                content_preview = content_preview[:1021] + "..."
            embed.add_field(name="Message Content", value=content_preview, inline=False)
        
        embed.set_footer(text=f"User ID: {message.author.id}")
        
        await alert_channel.send(embed=embed)
    except Exception as e:
        logging.error(f"Error sending AutoMod alert: {e}")

async def activate_raid_lockdown(guild, bot, raid_settings):
    """Lock down the server during a raid."""
    alert_channel_id = raid_settings.get("alert_channel")
    alert_channel = None
    
    if alert_channel_id:
        alert_channel = guild.get_channel(alert_channel_id)
    
    try:
        # Get the default role (@everyone)
        default_role = guild.default_role
        
        # Get exempt channels
        automod_settings = await bot.settings.find_by_id(guild.id)
        exempt_settings = automod_settings.get("automod_module", {}).get("exemptions", {})
        exempt_channels = exempt_settings.get("channels", [])
        
        # Lock down all text channels
        locked_channels = []
        for channel in guild.text_channels:
            if channel.id in exempt_channels:
                continue
                
            try:
                # Save current permissions
                current_perms = channel.overwrites_for(default_role)
                can_send = current_perms.send_messages
                
                # Only lock channels that weren't already locked
                if can_send is not False:
                    await channel.set_permissions(default_role, send_messages=False)
                    locked_channels.append(channel.id)
            except:
                continue
        
        # Store the lockdown info for later unlocking
        raid_lockdown_data = {
            "guild_id": guild.id,
            "locked_at": datetime.datetime.now().timestamp(),
            "locked_channels": locked_channels
        }
        
        await bot.settings.update_one(
            {"_id": guild.id},
            {"$set": {"automod_module.raid_lockdown": raid_lockdown_data}}
        )
        
        # Send alert if channel exists
        if alert_channel:
            embed = discord.Embed(
                title="🚨 Raid Detected - Server Lockdown",
                description="A potential raid was detected. The server has been locked down to prevent spam.",
                color=0xFF0000,
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(
                name="Locked Channels", 
                value=f"{len(locked_channels)} channels have been locked", 
                inline=False
            )
            
            embed.add_field(
                name="Duration", 
                value="Use `/raid unlock` to manually end the lockdown when the raid is over.", 
                inline=False
            )
            
            await alert_channel.send(embed=embed)
            
    except Exception as e:
        logging.error(f"Error activating raid lockdown: {e}")
