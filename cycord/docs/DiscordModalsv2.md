# CyModals - Discord.py Custom Modal Components

A powerful wrapper for Discord modals that allows you to use select menus (channels, users, roles) alongside text inputs in modal dialogs.

## Features

- ✅ **Text Input** - Standard text input fields
- ✅ **Channel Select** - Let users select channels in modals
- ✅ **User Select** - Let users select users in modals  
- ✅ **Role Select** - Let users select roles in modals
- ✅ **Mentionable Select** - Let users select users or roles in modals
- ✅ **Clean ID Returns** - Returns clean IDs instead of complex objects
- ✅ **Easy Integration** - Drop-in replacement for standard modals

## Installation

Simply copy the `CyModals` class into your project:

```python
from cycord.methods.DiscordModalsv2 import CyModals
```

## Quick Start

```python
import discord
from discord.ext import commands
from cycord.methods.DiscordModalsv2 import CyModals

@bot.command()
async def example(ctx):
    modal = CyModals(
        "Example Modal",
        [
            {
                "type": "text",
                "custom_id": "username",
                "label": "Enter Username",
                "required": True,
            },
            {
                "type": "channel",
                "custom_id": "target_channel",
                "label": "Select Channel",
                "placeholder": "Choose a channel...",
            }
        ]
    )
    
    await ctx.send_modal(modal)  # Send via interaction.response.send_modal()
    await modal.wait()
    
    values = modal.values
    username = values.get("username")
    channel_ids = values.get("target_channel", [])
    
    print(f"Username: {username}")
    print(f"Selected channels: {channel_ids}")
```

## Component Types

### 1. Text Input

Standard text input field with full discord.py TextInput options.

```python
{
    "type": "text",
    "custom_id": "description",
    "label": "Description",
    "description": "Enter a detailed description",
    "style": discord.TextStyle.paragraph,  # short or paragraph
    "placeholder": "Type here...",
    "required": True,
    "min_length": 10,
    "max_length": 500,
    "default": "Default text"
}
```

**Returns:** `string`

```python
description = modal.values.get("description")
# Returns: "User typed text here"
```

### 2. Channel Select

Allows users to select one or multiple channels.

```python
{
    "type": "channel",
    "custom_id": "channels",
    "label": "Select Channels",
    "description": "Choose target channels",
    "placeholder": "Pick channels...",
    "min_values": 1,
    "max_values": 3,
    "channel_types": [discord.ChannelType.text, discord.ChannelType.voice]
}
```

**Returns:** `list[str]` (Channel IDs)

```python
channel_ids = modal.values.get("channels", [])
# Returns: ["1234567890123456789", "9876543210987654321"]

# Convert to Discord objects:
channels = [interaction.guild.get_channel(int(id)) for id in channel_ids]
for channel in channels:
    print(f"Selected: {channel.name}")
```

### 3. User Select

Allows users to select one or multiple users.

```python
{
    "type": "user",
    "custom_id": "moderators",
    "label": "Select Moderators",
    "description": "Choose moderators for this action",
    "placeholder": "Select users...",
    "min_values": 1,
    "max_values": 5
}
```

**Returns:** `list[str]` (User IDs)

```python
user_ids = modal.values.get("moderators", [])
# Returns: ["1234567890123456789", "9876543210987654321"]

# Convert to Discord objects:
users = [interaction.guild.get_member(int(id)) for id in user_ids]
for user in users:
    print(f"Selected: {user.display_name}")
```

### 4. Role Select

Allows users to select one or multiple roles.

```python
{
    "type": "role",
    "custom_id": "target_roles",
    "label": "Select Roles",
    "description": "Choose roles to modify",
    "placeholder": "Pick roles...",
    "min_values": 1,
    "max_values": 10
}
```

**Returns:** `list[str]` (Role IDs)

```python
role_ids = modal.values.get("target_roles", [])
# Returns: ["1234567890123456789", "9876543210987654321"]

# Convert to Discord objects:
roles = [interaction.guild.get_role(int(id)) for id in role_ids]
for role in roles:
    print(f"Selected: {role.name}")
```

### 5. Mentionable Select

Allows users to select users OR roles (mentionables).

```python
{
    "type": "mentionable",
    "custom_id": "mentions",
    "label": "Select Mentionables",
    "description": "Choose users or roles",
    "placeholder": "Select mentionables...",
    "min_values": 1,
    "max_values": 25
}
```

**Returns:** `list[str]` (User/Role IDs)

```python
mentionable_ids = modal.values.get("mentions", [])
# Returns: ["1234567890123456789", "9876543210987654321"]

# Convert to Discord objects:
mentionables = []
for id_str in mentionable_ids:
    id_int = int(id_str)
    obj = interaction.guild.get_member(id_int) or interaction.guild.get_role(id_int)
    mentionables.append(obj)
```

## Complete Example

Here's a comprehensive example showing all component types:

```python
import discord
from discord.ext import commands
from cycord.methods.DiscordModalsv2 import CyModals

class ExampleView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Advanced Modal", style=discord.ButtonStyle.primary)
    async def advanced_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CyModals(
            "Advanced Configuration",
            [
                {
                    "type": "text",
                    "custom_id": "event_name",
                    "label": "Event Name",
                    "description": "Enter the name of the event",
                    "required": True,
                    "max_length": 100
                },
                {
                    "type": "text",
                    "custom_id": "event_description",
                    "label": "Event Description",
                    "description": "Detailed description of the event",
                    "style": discord.TextStyle.paragraph,
                    "min_length": 20,
                    "max_length": 1000
                },
                {
                    "type": "channel",
                    "custom_id": "event_channels",
                    "label": "Event Channels",
                    "description": "Select channels for the event",
                    "placeholder": "Choose channels...",
                    "min_values": 1,
                    "max_values": 3,
                    "channel_types": [discord.ChannelType.text, discord.ChannelType.voice]
                },
                {
                    "type": "role",
                    "custom_id": "event_roles",
                    "label": "Ping Roles",
                    "description": "Select roles to ping for this event",
                    "placeholder": "Choose roles to notify...",
                    "max_values": 5
                },
                {
                    "type": "user",
                    "custom_id": "event_organizers",
                    "label": "Event Organizers",
                    "description": "Select users who will organize this event",
                    "min_values": 1,
                    "max_values": 3
                }
            ],
            timeout=600  # 10 minutes
        )
        
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        # Parse all the values
        values = modal.values
        
        event_name = values.get("event_name", "Unnamed Event")
        event_description = values.get("event_description", "No description")
        
        # Convert IDs to Discord objects
        channel_ids = values.get("event_channels", [])
        channels = [interaction.guild.get_channel(int(id)) for id in channel_ids if id]
        
        role_ids = values.get("event_roles", [])
        roles = [interaction.guild.get_role(int(id)) for id in role_ids if id]
        
        organizer_ids = values.get("event_organizers", [])
        organizers = [interaction.guild.get_member(int(id)) for id in organizer_ids if id]
        
        # Create response embed
        embed = discord.Embed(
            title=f"🎉 {event_name}",
            description=event_description,
            color=discord.Color.blue()
        )
        
        if channels:
            channel_mentions = [c.mention for c in channels if c]
            embed.add_field(
                name="📺 Channels",
                value=", ".join(channel_mentions),
                inline=False
            )
        
        if roles:
            role_mentions = [r.mention for r in roles if r]
            embed.add_field(
                name="🔔 Notification Roles",
                value=", ".join(role_mentions),
                inline=False
            )
        
        if organizers:
            organizer_mentions = [o.mention for o in organizers if o]
            embed.add_field(
                name="👑 Organizers",
                value=", ".join(organizer_mentions),
                inline=False
            )
        
        embed.set_footer(text=f"Created by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)

# Usage in a cog
class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def create_event(self, ctx):
        view = ExampleView(self.bot)
        await ctx.send("Click the button to create a new event:", view=view)

async def setup(bot):
    await bot.add_cog(Events(bot))
```

## Error Handling

```python
try:
    modal = CyModals("Test Modal", fields)
    await interaction.response.send_modal(modal)
    await modal.wait()
    
    if modal.values:
        # Process the values
        pass
    else:
        # Modal was cancelled or timed out
        await interaction.followup.send("Modal cancelled.", ephemeral=True)
        
except Exception as e:
    await interaction.followup.send(f"Error: {e}", ephemeral=True)
```

## Tips and Best Practices

### 1. Always Check for Empty Values
```python
channel_ids = modal.values.get("channels", [])
if channel_ids:  # Check if any channels were selected
    channels = [interaction.guild.get_channel(int(id)) for id in channel_ids]
```

### 2. Handle Missing Objects
```python
channels = []
for id_str in channel_ids:
    channel = interaction.guild.get_channel(int(id_str))
    if channel:  # Channel might be deleted or inaccessible
        channels.append(channel)
```

### 3. Use Appropriate Max Values
- **Channels**: Usually 1-5 channels
- **Users**: 1-10 users for most use cases  
- **Roles**: 1-5 roles typically
- **Text**: Set reasonable character limits

### 4. Provide Good User Experience
```python
{
    "type": "channel",
    "custom_id": "channels",
    "label": "Select Channels",
    "description": "Choose channels where this will be posted",  # Helpful description
    "placeholder": "Click to select channels...",  # Clear placeholder
    "channel_types": [discord.ChannelType.text]  # Limit to relevant types
}
```

## Limitations

1. **Discord Modal Limits**: Discord limits modals to 5 components total
2. **Component Types**: Only text inputs and select menus are supported in modals
3. **Select Menu Limits**: Each select menu can have max 25 options selected
4. **Text Input Limits**: Discord enforces character limits (4000 max for paragraph style)

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve CyModals!

## License

This project is open source. Use it however you'd like!