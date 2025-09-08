from discord.ui import Button, View
from discord import Interaction, ButtonStyle
import discord
from menu import CustomModal
from utils.constants import BLANK_COLOR

class CustomCommandManager(View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx

    @discord.ui.button(
        label="Create Command",
        style=ButtonStyle.secondary,
        custom_id="create_command_button"
    )
    async def create_command(self, interaction: Interaction, button: Button):
        doc = await self.bot.custom_commands.find_by_id(interaction.guild.id)
        premium = await self.bot.premium.find_by_id(interaction.guild.id)
        if not premium and len(doc) - 1 >= 5: #subtract 1 for _id field
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Command Limit Reached",
                    description="You have reached the limit of 5 custom commands. Upgrade to premium to create more.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        view = MessageHandler(self.bot, self.ctx)
        embed = discord.Embed(
            title="Custom Command Creation",
            description="Use the buttons below to create your custom command.",
            color=BLANK_COLOR
        )
        await interaction.response.send_message(embed=embed, view=view)
    
    @discord.ui.button(
        label="Edit Command",
        style=ButtonStyle.secondary,
        custom_id="edit_command_button"
    )
    async def edit_command(self, interaction: Interaction, button: Button):
        modal = CustomModal(
            "Edit Command",
            [
                (
                    "alias",
                    discord.ui.TextInput(
                        label="Command Alias",
                        placeholder="Enter the alias of the command to edit",
                        required=True,
                        max_length=256
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return
        
        alias = modal.values.get("alias")
        if not alias:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Alias Provided",
                    description="You must provide an alias to edit a command.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        guild_doc = await self.bot.custom_commands.find_by_id(interaction.guild.id) or {"_id": interaction.guild.id}
        command_data = guild_doc.get(alias)
        if not command_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Command Not Found",
                    description=f"No command found with the alias '{alias}'.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        
        view = MessageHandler(self.bot, self.ctx, command_data)
        #we will generate an embed from command_data and include everything else
        # "title": None,
        # "message": None,
        # "description": None,
        # "image": None,
        # "thumbnail": None,
        # "timestamp": None,
        # "fields": [],
        # "footer": None,
        # "color": discord.Color.blue().value,
        embed = discord.Embed(
            title=command_data.get("title") or "No Title",
            description=command_data.get("description") or "No Description",
            color=command_data.get("color", BLANK_COLOR)
        )
        if command_data.get("image"):
            embed.set_image(url=command_data["image"])
        if command_data.get("thumbnail"):
            embed.set_thumbnail(url=command_data["thumbnail"])
        if command_data.get("alias"):
            embed.set_footer(text=f"Alias: {command_data['alias']}")
        for field in command_data.get("fields", []):
            embed.add_field(name=field["name"], value=field["value"], inline=False)
        #self edit the embed and view
        await interaction.message.edit(embed=embed, view=view)

    @discord.ui.button(
        label="Delete Command",
        style=ButtonStyle.danger,
        custom_id="delete_command_button"
    )
    async def delete_command(self, interaction: Interaction, button: Button):
        modal = CustomModal(
            "Delete Command",
            [
                (
                    "alias",
                    discord.ui.TextInput(
                        label="Command Alias",
                        placeholder="Enter the alias of the command to delete",
                        required=True,
                        max_length=256
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        alias = modal.values.get("alias")
        if not alias:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Alias Provided",
                    description="You must provide an alias to delete a command.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        guild_doc = self.bot.custom_commands.find_by_id(interaction.guild.id) or {"_id": interaction.guild.id}
        command_data = guild_doc.get(alias)
        if not command_data:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Command Not Found",
                    description=f"No command found with the alias '{alias}'.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        self.bot.custom_commands.delete_command(interaction.guild.id, alias)
        await interaction.followup.send(
            embed=discord.Embed(
                title="Command Deleted",
                description=f"The command with the alias '{alias}' has been deleted.",
                color=BLANK_COLOR
            ), ephemeral=True
        )

class MessageHandler(View):
    def __init__(self, bot, ctx, doc:dict = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.doc = doc or {
            "title": None,
            "message": None,
            "description": None,
            "image": None,
            "thumbnail": None,
            "timestamp": None,
            "fields": [],
            "footer": None,
            "color": discord.Color.blue().value,
            "created_by": ctx.author.id,
            "alias": None,
        }

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(
        label="Set Title",
        style=ButtonStyle.secondary,
        custom_id="set_title_button",
        row=0
    )
    async def set_title(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        modal = CustomModal(
            "Embed Title",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Title",
                        placeholder="Enter the title for the embed",
                        required=True,
                        max_length=256,
                        default=self.doc.get("title") or ""
                    )
                )
            ],
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return
        
        title = modal.values.get("value")
        if not title:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Title Provided",
                    description="You must provide a title.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["title"] = title
        embed = interaction.message.embeds[0]
        embed.title = title
        await interaction.message.edit(embed=embed)

    @discord.ui.button(
        label="Set Description",
        style=ButtonStyle.secondary,
        custom_id="set_description_button",
        row=0
    )
    async def set_description(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        modal = CustomModal(
            "Embed Description",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Description",
                        placeholder="Enter the description for the embed",
                        required=True,
                        max_length=3096,
                        style=discord.TextStyle.paragraph,
                        default=self.doc.get("description") or ""
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        description = modal.values.get("value")
        if not description:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Description Provided",
                    description="You must provide a description.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["description"] = description
        embed = interaction.message.embeds[0]
        embed.description = description
        await interaction.message.edit(embed=embed)
    
    @discord.ui.button(
        label="Alias",
        style=ButtonStyle.secondary,
        custom_id="set_alias_button",
        row=0
    )
    async def set_alias(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        modal = CustomModal(
            "Embed Alias",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Alias",
                        placeholder="Enter the alias for the embed",
                        required=True,
                        max_length=256,
                        default=self.doc.get("alias") or ""
                    )
                )
            ],
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        alias = modal.values.get("value")
        if not alias:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Alias Provided",
                    description="You must provide an alias.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["alias"] = alias
        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"Alias: {alias}")
        await interaction.message.edit(embed=embed)

    @discord.ui.button(
        label="Set Image",
        style=ButtonStyle.secondary,
        custom_id="set_image_button",
        row=0
    )
    async def set_image(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        modal = CustomModal(
            "Embed Image",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Image URL",
                        placeholder="Enter the image URL for the embed",
                        required=True,
                        max_length=1024,
                        default=self.doc.get("image") or ""
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        image_url = modal.values.get("value")
        if not image_url:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Image URL Provided",
                    description="You must provide an image URL.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["image"] = image_url
        embed = interaction.message.embeds[0]
        embed.set_image(url=image_url)
        await interaction.message.edit(embed=embed)

    @discord.ui.button(
        label="Set Thumbnail",
        style=ButtonStyle.secondary,
        custom_id="set_thumbnail_button",
        row=0
    )
    async def set_thumbnail(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        modal = CustomModal(
            "Embed Thumbnail",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Thumbnail URL",
                        placeholder="Enter the thumbnail URL for the embed",
                        required=True,
                        max_length=1024,
                        default=self.doc.get("thumbnail") or ""
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        thumbnail_url = modal.values.get("value")
        if not thumbnail_url:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Thumbnail URL Provided",
                    description="You must provide a thumbnail URL.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["thumbnail"] = thumbnail_url
        embed = interaction.message.embeds[0]
        embed.set_thumbnail(url=thumbnail_url)
        await interaction.message.edit(embed=embed)

    @discord.ui.button(
        label="Add Field",
        style=ButtonStyle.secondary,
        row=1,
        custom_id="add_field_button"
    )
    async def add_field(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        modal = CustomModal(
            "Add Field",
            [
                (
                    "name",
                    discord.ui.TextInput(
                        label="Field Name",
                        placeholder="Enter the field name",
                        required=True,
                        max_length=256,
                        style=discord.TextStyle.short,
                    )
                ),
                (
                    "value",
                    discord.ui.TextInput(
                        label="Field Value",
                        placeholder="Enter the field value",
                        required=True,
                        max_length=1024,
                        style=discord.TextStyle.paragraph
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        field_name = modal.values.get("name")
        field_value = modal.values.get("value")
        if not field_name or not field_value:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Missing Field Information",
                    description="You must provide both a field name and a field value.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["fields"].append({"name": field_name, "value": field_value})
        embed = interaction.message.embeds[0]
        embed.add_field(name=field_name, value=field_value, inline=False)
        await interaction.message.edit(embed=embed)

    @discord.ui.button(
        label="Remove Last Field",
        style=ButtonStyle.secondary,
        row=1,
        custom_id="remove_last_field_button"
    )
    async def remove_last_field(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        if not self.doc["fields"]:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Fields to Remove",
                    description="There are no fields to remove.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["fields"].pop()
        embed = interaction.message.embeds[0]
        embed.remove_field(len(embed.fields) - 1)
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Field Removed",
                description="The last field has been removed.",
                color=BLANK_COLOR
            ), ephemeral=True
        )

    @discord.ui.button(
        label="Set Color",
        style=ButtonStyle.secondary,
        row=1,
        custom_id="set_color_button"
    )
    async def set_color(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        modal = CustomModal(
            "Set Color",
            [
                (
                    "color",
                    discord.ui.TextInput(
                        label="Color Hex Code",
                        placeholder="Enter the hex code for the embed color",
                        required=True,
                        max_length=7,
                        default=self.doc.get("color") and f"#{discord.Color(self.doc['color']).value:06x}" or "#0000FF"
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        color_hex = modal.values.get("color")
        if not color_hex:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Color Provided",
                    description="You must provide a color hex code.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["color"] = color_hex
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.from_str(color_hex)
        self.doc["color"] = embed.color.value
        await interaction.message.edit(embed=embed)
        await interaction.followup.send(
            embed=discord.Embed(
                title="Color Set",
                description=f"Embed color set to {color_hex}.",
                color=BLANK_COLOR
            ), ephemeral=True
        )

    @discord.ui.button(
        label="Set Message",
        style=ButtonStyle.secondary,
        row=1,
        custom_id="set_message_button"
    )
    async def set_message(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        modal = CustomModal(
            "Set Message",
            [
                (
                    "message",
                    discord.ui.TextInput(
                        label="Message Content",
                        placeholder="Enter the message content",
                        required=True,
                        max_length=2048,
                        style=discord.TextStyle.paragraph,
                        default=self.doc.get("message") or ""
                    )
                )
            ]
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        message_content = modal.values.get("message")
        if not message_content:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Message Content Provided",
                    description="You must provide message content.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["message"] = message_content
        message = interaction.message
        await message.edit(content=message_content)

    @discord.ui.button(
        label="Finish",
        style=ButtonStyle.success,
        row=1,
        custom_id="finish_button"
    )
    async def finish(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not allowed to use this button.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        missing_fields = []
        #if embed is missing title, description then we consider it incomplete
        if not self.doc.get("alias"):
            missing_fields.append("Alias")
        if not self.doc.get("title") and self.doc.get("description"):
            missing_fields.append("Title")
        if not self.doc.get("description") and self.doc.get("title"):
            missing_fields.append("Description")
        if missing_fields:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Required Fields",
                    description=f"The following required fields are missing: {', '.join(missing_fields)}",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["created_at"] = int(discord.utils.utcnow().timestamp())
        # {
        #     "_id": guild.id,
        #     "alias_1": {}, #custom command data
        #     "alias_2": {},
        #     ...
        # }
        guild_doc = await self.bot.custom_commands.find_by_id(interaction.guild.id) or {"_id": interaction.guild.id}
        if self.doc["alias"] in guild_doc:
            guild_doc[self.doc["alias"]].update(self.doc)
        else:
            guild_doc[self.doc["alias"]] = self.doc
        await self.bot.custom_commands.update_one(
            {"_id": interaction.guild.id}, 
            {"$set": guild_doc}, 
            upsert=True
        )
        embed = discord.Embed(
            title="Command Saved",
            description=f"The command with the alias '{self.doc['alias']}' has been saved.",
            color=BLANK_COLOR
        )
        message = interaction.message
        await message.edit(content=None, embed=embed, view=None)