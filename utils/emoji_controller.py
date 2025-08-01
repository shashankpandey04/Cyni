import os
import discord

class EmojiController:
    def __init__(self, bot, emoji_folder="assets/emojis"):
        self.bot = bot
        self.emoji_folder = emoji_folder
        self.emojis = {}

    async def prefetch_emojis(self):
        """
        Sync local emoji images to application emojis (auto-upload if missing).
        """
        application_emojis = await self.bot.fetch_application_emojis()
        existing_names = {e.name for e in application_emojis}

        for filename in os.listdir(self.emoji_folder):
            if not filename.lower().endswith(".png"):
                continue

            emoji_name = filename[:-4]
            if emoji_name in existing_names:
                continue

            file_path = os.path.join(self.emoji_folder, filename)
            try:
                with open(file_path, "rb") as f:
                    await self.bot.create_application_emoji(name=emoji_name, image=f.read())
                print(f"[EmojiController] Uploaded emoji: {emoji_name}")
            except discord.HTTPException as e:
                print(f"[EmojiController] Failed to upload '{emoji_name}': {e}")

        updated_emojis = await self.bot.fetch_application_emojis()
        self.emojis = {e.name: e.id for e in updated_emojis}

    def get(self, name: str) -> str:
        """
        Get the emoji as a Discord-formatted string: <:name:id>
        """
        emoji_id = self.emojis.get(name)
        if emoji_id:
            return f"<:{name}:{emoji_id}>"
        return "❓"
