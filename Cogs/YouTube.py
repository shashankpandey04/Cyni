import discord
from discord.ext import commands, tasks
import googleapiclient.discovery
import os
import logging
import datetime
from dotenv import load_dotenv
from cyni import is_management
import re

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube_api = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        self.check_new_videos.start()
        
    def cog_unload(self):
        self.check_new_videos.cancel()
    
    @tasks.loop(minutes=2)
    async def check_new_videos(self):
        await self.bot.wait_until_ready()
        
        try:
            all_configs = await self.bot.db.youtube_config.find().to_list(length=None)
            
            for config in all_configs:
                guild_id = config["guild_id"]
                guild = self.bot.get_guild(guild_id)
                
                if not guild:
                    continue
                
                if "channels" not in config:
                    continue
                    
                for channel_config in config["channels"]:
                    try:
                        channel_id = channel_config["youtube_id"]
                        last_video_id = channel_config.get("last_video_id", "")
                        notification_channel_id = channel_config["discord_channel_id"]
                        
                        new_video = await self.get_latest_video(channel_id, last_video_id)
                        
                        if new_video:
                            notification_channel = guild.get_channel(notification_channel_id)
                            if notification_channel:
                                # Update last video ID in database
                                await self.bot.db.youtube_config.update_one(
                                    {"guild_id": guild_id, "channels.youtube_id": channel_id},
                                    {"$set": {"channels.$.last_video_id": new_video["id"], 
                                             "channels.$.last_check": datetime.datetime.now().timestamp()}}
                                )
                                
                                # Send notification
                                message_format = channel_config.get("message_format", "{everyone} New video from **{channel_name}**!\n{video_url}")
                                await self.send_notification(notification_channel, new_video, message_format)
                                
                    except Exception as e:
                        logging.error(f"Error checking YouTube channel {channel_id}: {e}")
                        continue
                    
        except Exception as e:
            logging.error(f"Error in YouTube notification task: {e}")
    
    async def get_latest_video(self, channel_id, last_video_id):
        try:
            channel_response = self.youtube_api.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()
            
            if not channel_response["items"]:
                return None
                
            uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            playlist_response = self.youtube_api.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=1
            ).execute()
            
            if not playlist_response["items"]:
                return None
                
            video_item = playlist_response["items"][0]
            video_id = video_item["contentDetails"]["videoId"]
            
            if video_id == last_video_id:
                return None
            video_response = self.youtube_api.videos().list(
                part="snippet,statistics",
                id=video_id
            ).execute()
            
            if not video_response["items"]:
                return None
                
            video_data = video_response["items"][0]
            
            publish_time = datetime.datetime.fromisoformat(video_data["snippet"]["publishedAt"].replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
        
            if (now - publish_time).total_seconds() > 3600:
                return None
            
            return {
                "id": video_id,
                "title": video_data["snippet"]["title"],
                "description": video_data["snippet"]["description"],
                "thumbnail": video_data["snippet"]["thumbnails"]["high"]["url"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel_name": video_data["snippet"]["channelTitle"],
                "published_at": publish_time,
                "views": video_data["statistics"].get("viewCount", "0"),
                "likes": video_data["statistics"].get("likeCount", "0")
            }
            
        except Exception as e:
            logging.error(f"Error getting latest video: {e}")
            return None
    
    async def send_notification(self, channel, video, message_format):
        try:
            message = message_format.replace("{video_url}", video["url"])
            message = message.replace("{video_title}", video["title"])
            message = message.replace("{channel_name}", video["channel_name"])
            message = message.replace("{everyone}", "@everyone")
            message = message.replace("{here}", "@here")
            
            embed = discord.Embed(
                title=video["title"],
                url=video["url"],
                description=video["description"][:200] + "..." if len(video["description"]) > 200 else video["description"],
                color=0xFF0000,  # YouTube red
                timestamp=video["published_at"]
            )
            
            embed.set_author(name=video["channel_name"], icon_url="https://www.youtube.com/s/desktop/ca57a816/img/favicon_144.png")
            embed.set_image(url=video["thumbnail"])
            embed.add_field(name="Views", value=video["views"], inline=True)
            embed.add_field(name="Likes", value=video["likes"], inline=True)
            embed.set_footer(text="Published")
            
            await channel.send(content=message, embed=embed)
            
        except Exception as e:
            logging.error(f"Error sending notification: {e}")
    
    @commands.group(name="youtube", aliases=["yt"], invoke_without_command=True)
    @commands.guild_only()
    async def youtube(self, ctx):
        """Manage YouTube notification settings"""
        await ctx.send_help(ctx.command)
    
    @youtube.command(name="add")
    @commands.guild_only()
    @is_management()
    async def add_channel(self, ctx, youtube_url_or_id, discord_channel: discord.TextChannel = None):
        """Add a YouTube channel to notify about new videos"""
        if not discord_channel:
            discord_channel = ctx.channel
            
        youtube_id = self.extract_channel_id(youtube_url_or_id)
        if not youtube_id:
            return await ctx.send("❌ Invalid YouTube channel URL or ID. Please provide a valid channel URL or ID.")
            
        try:
            channel_response = self.youtube_api.channels().list(
                part="snippet",
                id=youtube_id
            ).execute()
            
            if not channel_response["items"]:
                return await ctx.send("❌ YouTube channel not found. Please provide a valid channel URL or ID.")
                
            channel_title = channel_response["items"][0]["snippet"]["title"]
            
            guild_config = await self.bot.db.youtube_config.find_one({"guild_id": ctx.guild.id})
            
            if not guild_config:
                await self.bot.db.youtube_config.insert_one({
                    "guild_id": ctx.guild.id,
                    "channels": [{
                        "youtube_id": youtube_id,
                        "channel_name": channel_title,
                        "discord_channel_id": discord_channel.id,
                        "last_video_id": "",
                        "message_format": "{everyone} New video from **{channel_name}**!\n{video_url}",
                        "last_check": datetime.datetime.now().timestamp()
                    }]
                })
            else:
                for channel in guild_config.get("channels", []):
                    if channel["youtube_id"] == youtube_id and channel["discord_channel_id"] == discord_channel.id:
                        return await ctx.send(f"❌ This YouTube channel is already being tracked in {discord_channel.mention}.")
                
                await self.bot.db.youtube_config.update_one(
                    {"guild_id": ctx.guild.id},
                    {"$push": {"channels": {
                        "youtube_id": youtube_id,
                        "channel_name": channel_title,
                        "discord_channel_id": discord_channel.id,
                        "last_video_id": "",
                        "message_format": "{everyone} New video from **{channel_name}**!\n{video_url}",
                        "last_check": datetime.datetime.now().timestamp()
                    }}}
                )
            
            embed = discord.Embed(
                title="YouTube Notification Added",
                description=f"Successfully added **{channel_title}** to YouTube notifications.\nNew videos will be posted in {discord_channel.mention}.",
                color=0xFF0000  # YouTube red
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Error adding YouTube channel: {e}")
            await ctx.send("❌ An error occurred while adding the YouTube channel. Please try again later.")
    
    @youtube.command(name="remove", aliases=["delete"])
    @commands.guild_only()
    @is_management()
    async def remove_channel(self, ctx, youtube_url_or_id, discord_channel: discord.TextChannel = None):
        """Remove a YouTube channel from notifications"""
        if not discord_channel:
            discord_channel = ctx.channel
        
        youtube_id = self.extract_channel_id(youtube_url_or_id)
        if not youtube_id:
            return await ctx.send("❌ Invalid YouTube channel URL or ID. Please provide a valid channel URL or ID.")
            
        try:
            result = await self.bot.db.youtube_config.update_one(
                {"guild_id": ctx.guild.id},
                {"$pull": {"channels": {"youtube_id": youtube_id, "discord_channel_id": discord_channel.id}}}
            )
            
            if result.modified_count > 0:
                embed = discord.Embed(
                    title="YouTube Notification Removed",
                    description=f"Successfully removed YouTube channel from notifications in {discord_channel.mention}.",
                    color=0xFF0000
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ This YouTube channel is not being tracked in the specified Discord channel.")
            
        except Exception as e:
            logging.error(f"Error removing YouTube channel: {e}")
            await ctx.send("❌ An error occurred while removing the YouTube channel. Please try again later.")
    
    @youtube.command(name="list")
    @commands.guild_only()
    async def list_channels(self, ctx):
        """List all YouTube channels being tracked in this server"""
        try:
            guild_config = await self.bot.db.youtube_config.find_one({"guild_id": ctx.guild.id})
            
            if not guild_config or "channels" not in guild_config or not guild_config["channels"]:
                return await ctx.send("❌ No YouTube channels are being tracked in this server.")
                
            embed = discord.Embed(
                title="YouTube Notifications",
                description=f"YouTube channels being tracked in {ctx.guild.name}",
                color=0xFF0000
            )
            
            for i, channel in enumerate(guild_config["channels"], 1):
                discord_channel = ctx.guild.get_channel(channel["discord_channel_id"])
                discord_channel_mention = discord_channel.mention if discord_channel else "Unknown Channel"
                
                embed.add_field(
                    name=f"{i}. {channel.get('channel_name', 'Unknown')}",
                    value=f"Notifications: {discord_channel_mention}\nChannel ID: `{channel['youtube_id']}`",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Error listing YouTube channels: {e}")
            await ctx.send("❌ An error occurred while listing YouTube channels. Please try again later.")
    
    @youtube.command(name="message")
    @commands.guild_only()
    @is_management()
    async def set_message_format(self, ctx, youtube_url_or_id, *, message_format):
        """Set the notification message format for a YouTube channel
        
        Available placeholders:
        {video_url} - The URL of the video
        {video_title} - The title of the video
        {channel_name} - The name of the YouTube channel
        {everyone} - @everyone mention
        {here} - @here mention
        """
        youtube_id = self.extract_channel_id(youtube_url_or_id)
        if not youtube_id:
            return await ctx.send("❌ Invalid YouTube channel URL or ID. Please provide a valid channel URL or ID.")
            
        try:
            result = await self.bot.db.youtube_config.update_one(
                {"guild_id": ctx.guild.id, "channels.youtube_id": youtube_id},
                {"$set": {"channels.$.message_format": message_format}}
            )
            
            if result.modified_count > 0:
                embed = discord.Embed(
                    title="YouTube Notification Message Updated",
                    description=f"Successfully updated notification message format for YouTube channel.",
                    color=0xFF0000
                )
                embed.add_field(name="New Format", value=f"```{message_format}```", inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ This YouTube channel is not being tracked in this server.")
            
        except Exception as e:
            logging.error(f"Error setting message format: {e}")
            await ctx.send("❌ An error occurred while setting the message format. Please try again later.")
    
    def extract_channel_id(self, url_or_id):
        """Extract YouTube channel ID from a URL or return the ID if it's already a valid ID"""
        if re.match(r'^[A-Za-z0-9_-]{24}$', url_or_id):
            return url_or_id
            
        channel_url_patterns = [
            r'youtube\.com\/channel\/([A-Za-z0-9_-]+)',  # youtube.com/channel/UC...
            r'youtube\.com\/c\/([A-Za-z0-9_-]+)',        # youtube.com/c/...
            r'youtube\.com\/user\/([A-Za-z0-9_-]+)',     # youtube.com/user/...
            r'youtube\.com\/@([A-Za-z0-9_-]+)'           # youtube.com/@...
        ]
        
        for pattern in channel_url_patterns:
            match = re.search(pattern, url_or_id)
            if match:
                username = match.group(1)
                try:
                    response = self.youtube_api.search().list(
                        part="snippet",
                        q=username,
                        type="channel",
                        maxResults=1
                    ).execute()
                    
                    if response["items"]:
                        return response["items"][0]["snippet"]["channelId"]
                except:
                    pass
                
        match = re.search(r'youtube\.com\/channel\/([A-Za-z0-9_-]+)', url_or_id)
        if match:
            return match.group(1)
            
        return None

@commands.Cog.listener()
async def setup(bot):
    if not YOUTUBE_API_KEY:
        logging.warning("YOUTUBE_API_KEY not set. YouTube notifications will not work.")
        return
        
    await bot.add_cog(YouTube(bot))
    
    if "youtube_config" not in await bot.db.list_collection_names():
        await bot.db.create_collection("youtube_config")
