from utils.mongo import Document
import datetime

class YouTubeConfig(Document):
    def __init__(self, db, collection_name):
        super().__init__(db, collection_name)
        
    async def get_guild_config(self, guild_id):
        """Get YouTube configuration for a guild"""
        return await self.find_by_id(guild_id)
        
    async def add_channel(self, guild_id, youtube_id, channel_name, discord_channel_id, message_format=None):
        """Add a YouTube channel to track"""
        if not message_format:
            message_format = "{everyone} New video from **{channel_name}**!\n{video_url}"
            
        config = await self.find_by_id(guild_id)
        
        if not config:
            # Create new config
            await self.insert({
                "_id": guild_id,
                "channels": [{
                    "youtube_id": youtube_id,
                    "channel_name": channel_name,
                    "discord_channel_id": discord_channel_id,
                    "last_video_id": "",
                    "message_format": message_format,
                    "last_check": datetime.datetime.now().timestamp()
                }]
            })
        else:
            # Update existing config
            await self.update({
                "_id": guild_id,
                "$push": {
                    "channels": {
                        "youtube_id": youtube_id,
                        "channel_name": channel_name,
                        "discord_channel_id": discord_channel_id,
                        "last_video_id": "",
                        "message_format": message_format,
                        "last_check": datetime.datetime.now().timestamp()
                    }
                }
            })
        
    async def remove_channel(self, guild_id, youtube_id, discord_channel_id):
        """Remove a YouTube channel from tracking"""
        return await self.update({
            "_id": guild_id,
            "$pull": {
                "channels": {
                    "youtube_id": youtube_id,
                    "discord_channel_id": discord_channel_id
                }
            }
        })
        
    async def update_last_video(self, guild_id, youtube_id, video_id):
        """Update the last video ID for a channel"""
        return await self.update({
            "_id": guild_id,
            "channels.youtube_id": youtube_id
        }, {
            "$set": {
                "channels.$.last_video_id": video_id,
                "channels.$.last_check": datetime.datetime.now().timestamp()
            }
        })
        
    async def update_message_format(self, guild_id, youtube_id, message_format):
        """Update the notification message format for a channel"""
        return await self.update({
            "_id": guild_id,
            "channels.youtube_id": youtube_id
        }, {
            "$set": {
                "channels.$.message_format": message_format
            }
        })
