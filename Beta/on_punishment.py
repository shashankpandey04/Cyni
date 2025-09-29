import discord
from bson import ObjectId
from discord.ext import commands
from utils.constants import GREEN_COLOR
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp
from datetime import datetime

load_dotenv()

class OnPunishment(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Load fonts once at startup
        try:
            # Try to use Discord's font (Whitney) or similar
            self.title_font = ImageFont.truetype("arial.ttf", 16)
            self.bold_font = ImageFont.truetype("arialbd.ttf", 15)  # Bold for labels
            self.text_font = ImageFont.truetype("arial.ttf", 15)
            self.small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            # Fallback to default font
            self.title_font = ImageFont.load_default()
            self.bold_font = ImageFont.load_default()
            self.text_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()

    async def fetch_image(self, url: str) -> Image.Image:
        """Fetch image from URL and return PIL Image"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(BytesIO(data)).convert('RGBA')
        except Exception as e:
            self.bot.logger.error(f"Failed to fetch image: {e}")
        return None

    def create_punishment_image(self, warning: dict, author: discord.User, thumbnail_url: str, 
                                author_avatar: Image.Image = None, roblox_avatar: Image.Image = None) -> BytesIO:
        """Generate Discord embed-style punishment log image"""
        
        # Discord embed dimensions and colors
        width = 520
        
        # Discord dark theme colors (exact matches)
        bg_color = (47, 49, 54)  # Background
        embed_bg = (43, 45, 49)  # Embed background
        embed_border = (87, 242, 135)  # Green border (from GREEN_COLOR)
        title_color = (255, 255, 255)
        field_name_color = (255, 255, 255)
        field_value_color = (219, 222, 225)  # Slightly dimmed white
        
        # Calculate content first to determine actual height needed
        base_content_height = 350
        
        # Create temporary image for calculations
        temp_img = Image.new('RGBA', (width, base_content_height), bg_color)
        temp_draw = ImageDraw.Draw(temp_img)
        
        embed_x = 10
        embed_y = 10
        embed_width = width - 20
        border_width = 4
        content_x = embed_x + border_width + 12
        y_pos = embed_y + 12
        
        # Calculate heights for author section
        if author_avatar:
            avatar_size = 24
            y_pos += avatar_size + 12
        
        # Title
        y_pos += 28
        
        # Punishment Information field + details
        y_pos += 22  # Field name
        y_pos += 20 * 5  # 5 detail lines
        y_pos += 12  # Spacing
        
        # Moderator Information field + details
        y_pos += 22  # Field name
        y_pos += 20 * 2  # 2 detail lines
        y_pos += 15  # Spacing
        
        final_height = y_pos + 10
        
        img = Image.new('RGBA', (width, final_height), bg_color)
        draw = ImageDraw.Draw(img)
        
        draw.rectangle(
            [(embed_x, embed_y), (embed_x + border_width, final_height - 10)],
            fill=embed_border
        )
        
        draw.rectangle(
            [(embed_x + border_width, embed_y), (embed_x + embed_width, final_height - 10)],
            fill=embed_bg
        )
        
        y_pos = embed_y + 12
        
        if author_avatar:
            avatar_size = 24
            author_avatar_resized = author_avatar.resize((avatar_size, avatar_size))
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            img.paste(author_avatar_resized, (content_x, y_pos), mask)
            
            draw.text((content_x + avatar_size + 8, y_pos + 4), 
                     author.name, fill=field_value_color, font=self.small_font)
            y_pos += avatar_size + 12
        
        title_text = f"Logged Punishment"
        draw.text((content_x, y_pos), title_text, fill=title_color, font=self.title_font)
        y_pos += 28
        
        draw.text((content_x, y_pos), "Punishment Information", fill=field_name_color, font=self.bold_font)
        y_pos += 22
        
        quote_x = content_x + 4
        draw.rectangle([(quote_x, y_pos), (quote_x + 2, y_pos + 100)], fill=(79, 84, 92))
        
        detail_x = quote_x + 10
        punishment_details = [
            ("Player:", warning['user_name']),
            ("Type:", warning['type']),
            ("Reason:", warning['reason'][:50] + "..." if len(warning['reason']) > 50 else warning['reason']),
            ("ID:", warning['snowflake'])
        ]
        
        for label, value in punishment_details:
            draw.text((detail_x, y_pos), f"{label}", fill=field_name_color, font=self.bold_font)
            label_width = draw.textlength(f"{label} ", font=self.bold_font)
            draw.text((detail_x + label_width, y_pos), str(value), fill=field_value_color, font=self.text_font)
            y_pos += 20
        
        y_pos += 18
        
        draw.text((content_x, y_pos), "Moderator Information", fill=field_name_color, font=self.bold_font)
        y_pos += 22
        
        draw.rectangle([(quote_x, y_pos), (quote_x + 2, y_pos + 45)], fill=(79, 84, 92))
        
        moderator_details = [
            ("Username:", warning['moderator_name']),
            ("ID:", str(warning['moderator_id']))
        ]
        
        for label, value in moderator_details:
            draw.text((detail_x, y_pos), f"{label}", fill=field_name_color, font=self.bold_font)
            label_width = draw.textlength(f"{label} ", font=self.bold_font)
            draw.text((detail_x + label_width, y_pos), str(value), fill=field_value_color, font=self.text_font)
            y_pos += 20
        
        y_pos += 15
        
        if roblox_avatar:
            thumb_size = 80
            roblox_avatar_resized = roblox_avatar.resize((thumb_size, thumb_size))
            thumb_x = embed_x + embed_width - thumb_size - 12
            thumb_y = embed_y + 50
            img.paste(roblox_avatar_resized, (thumb_x, thumb_y))
        
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
        output.seek(0)
        
        return output

    @commands.Cog.listener()
    async def on_punishment(self, warning: ObjectId, author: discord.User, thumbnail: str):

        warning = await self.bot.punishments.find_by_id(warning)
        if warning is None:
            return

        guild: discord.Guild = self.bot.get_guild(warning["guild_id"])
        if guild is None:
            return

        guild_settings = await self.bot.settings.find_by_id(guild.id)
        if not guild_settings:
            return

        channel_id = guild_settings.get("roblox", {}).get("punishments", {}).get("channel")
        channel: discord.TextChannel = guild.get_channel(channel_id) if channel_id else None
        
        if channel is None:
            return

        author_avatar = None
        roblox_avatar = None
        
        if author.display_avatar:
            author_avatar = await self.fetch_image(author.display_avatar.url)
        
        if thumbnail:
            roblox_avatar = await self.fetch_image(thumbnail)

        try:
            image_bytes = self.create_punishment_image(warning, author, thumbnail, author_avatar, roblox_avatar)
            
            file = discord.File(image_bytes, filename=f"punishment_{warning['snowflake']}.png")
            
            timestamp = int(warning['timestamp'])
            content = f"🔒 **Punishment Logged** • <t:{timestamp}:R>"
            
            logger = self.bot.get_cog("ThrottledLogger")
            if logger:
                await logger.limiter.enqueue(
                    guild.id, 
                    channel.send, 
                    content=content,
                    file=file
                )
            else:
                await channel.send(content=content, file=file)
                
        except Exception as e:
            self.bot.logger.error(f"Failed to generate/send punishment image: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnPunishment(bot))