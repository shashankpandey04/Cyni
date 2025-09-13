# SelfProfileAPI

The **SelfProfileAPI** provides support for modifying the bot’s guild-specific profile.  
This includes early access to Discord features not yet supported in `discord.py`.

---

## ✨ Supported Fields
- **nick** → Change the bot’s nickname in a guild  
- **bio** → Set the bot’s guild member bio  
- **banner** → Upload a guild-specific banner (base64 image data URI)  
- **avatar** → Upload a guild-specific avatar (base64 image data URI)  

---

## 🔧 Example
```python
from cycord.methods.SelfProfileAPI import GuildSelfMemberAPI

guild_api = GuildSelfMemberAPI(bot)

await guild_api.set_profile(
    guild_id=123456789012345678,
    nick="HyperSync AI",
    bio="Need of tomorrow's AI 🤖"
)
```

## 📌 Notes

- This only updates the bot’s member profile in a specific guild.

- MANAGE_NICKNAME permission is required for nickname updates.

- Bio, banner, and avatar do not require additional guild permissions.

- These fields are guild-scoped and do not affect the bot globally.

## ⚠️ Disclaimer

This feature is experimental and built for CYNI’s early adoption.