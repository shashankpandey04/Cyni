from discord.ui import Button, View
from discord import Interaction, ButtonStyle
import discord
from menu import CustomModal
from utils.constants import BLANK_COLOR, RED_COLOR


# "_id": f"{ctx.guild.id}_{partnership_id}",
# "logged_by": ctx.author.id,
# "title": title,
# "description": description,
# "representative": representative.id,
# "image": image,
# "timestamp": time.time()

class RepresentativeSelect(View):
    def __init__(self, ctx, main_message, partnership_doc):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.main_message = main_message
        self.partnership_doc = partnership_doc
        self.representative = None
        self.other_representatives = []

        self.main_representative_select = discord.ui.UserSelect(
            placeholder="Select a representative for the partnership",
            min_values=1,
            max_values=1
        )
        self.main_representative_select.callback = self.main_representative_callback
        self.add_item(self.main_representative_select)

        self.other_representatives_select = discord.ui.UserSelect(
            placeholder="Select other representatives (optional)",
            min_values=0,
            max_values=5
        )
        self.other_representatives_select.callback = self.other_representatives_callback
        self.add_item(self.other_representatives_select)

        self.finish_button = Button(
            label="Finish",
            style=ButtonStyle.primary
        )
        self.finish_button.callback = self.finish_callback
        self.add_item(self.finish_button)

    async def main_representative_callback(self, interaction: Interaction):
        self.representative = self.main_representative_select.values[0]
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Main Representative Set",
                description=f"Main representative set to {self.representative.mention}",
                color=BLANK_COLOR
            ), ephemeral=True
        )
        self.partnership_doc['representative'] = self.representative.id

    async def other_representatives_callback(self, interaction: Interaction):
        self.other_representatives = self.other_representatives_select.values
        mentions = [user.mention for user in self.other_representatives]
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Other Representatives Set",
                description=f"Other representatives set to {', '.join(mentions) if mentions else 'None'}",
                color=BLANK_COLOR
            ), ephemeral=True
        )
        self.partnership_doc['other_representatives'] = [user.id for user in self.other_representatives]

    async def finish_callback(self, interaction: Interaction):
        if not self.representative:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Main Representative",
                    description="You must select a main representative before finishing.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        
        embed=discord.Embed(
            title="Representatives Set",
            description=f"Main Representative: {self.representative.mention}\n"
                        f"Other Representatives: {', '.join([user.mention for user in self.other_representatives if user]) if self.other_representatives else 'None'}",
            color=BLANK_COLOR
        )
        await interaction.response.edit_message(embed=embed, view=None)
        embed = self.main_message.embeds[0]
        embed.set_footer(text=f"Represented by: {self.representative.name} `(ID: {self.representative.id})`")
        await self.main_message.edit(embed=embed)
        return {
            "representative": self.representative,
            "other_representatives": self.other_representatives
        }
        

class PartnershipLogView(View):
    def __init__(self, bot, ctx, partnership_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.partnership_id = partnership_id
        self.doc = {
            "_id": f"{ctx.guild.id}_{partnership_id}",
            "logged_by": ctx.author.id,
            "title": None,
            "message": None,
            "description": None,
            "representative": None,
            "other_representatives": [],
            "image": None,
            "thumbnail": None,
            "timestamp": None,
            "fields": [],
            "footer": None,
            "color": discord.Color.blue().value
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        
        modal = CustomModal(
            "Partnership Embed Title",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Title",
                        placeholder="Enter the title for the partnership embed",
                        required=True,
                        max_length=256,
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        modal = CustomModal(
            "Partnership Embed Description",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Description",
                        placeholder="Enter the description for the partnership embed",
                        required=True,
                        max_length=3096,
                        style=discord.TextStyle.paragraph
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
        label="Set Representative",
        style=ButtonStyle.secondary,
        custom_id="set_representative_button",
        row=0
    )
    async def set_representative(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        view = RepresentativeSelect(self.ctx, interaction.message, self.doc)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Select Representatives",
                description="Select the main and other representatives for the partnership.",
                color=BLANK_COLOR
            ), view=view
        )
        result = await view.wait()
        if not result:
            return

    @discord.ui.button(
        label="Set Image",
        style=ButtonStyle.secondary,
        custom_id="set_image_button",
        row=0
    )
    async def set_image(self, interaction: Interaction, button: Button):
        if not await self.interaction_check(interaction):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        
        modal = CustomModal(
            "Partnership Embed Image",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Image URL",
                        placeholder="Enter the image URL for the partnership embed",
                        required=True,
                        max_length=1024,
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


        if not (image_url.startswith("http://") or image_url.startswith("https://")):
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid URL",
                    description="The image URL must start with http:// or https://",
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        modal = CustomModal(
            "Partnership Embed Thumbnail",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Thumbnail URL",
                        placeholder="Enter the thumbnail URL for the partnership embed",
                        required=True,
                        max_length=1024,
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
        
        if not (thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://")):
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid URL",
                    description="The thumbnail URL must start with http:// or https://",
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        if not self.doc["fields"]:
            await interaction.followup.send(
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
        await interaction.followup.send(
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        modal = CustomModal(
            "Set Message",
            [
                (
                    "message",
                    discord.ui.TextInput(
                        label="Message Content",
                        placeholder="Enter the message content for the partnership embed",
                        required=True,
                        max_length=2048,
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
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Unauthorized",
                    description="You are not authorized to use this button.",
                    color=RED_COLOR
                ), ephemeral=True
            )
        missing_fields = []
        if not self.doc["title"]:
            missing_fields.append("Title")
        if not self.doc["description"]:
            missing_fields.append("Description")
        if not self.doc["representative"]:
            missing_fields.append("Representative")
        if missing_fields:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Missing Required Fields",
                    description=f"The following required fields are missing: {', '.join(missing_fields)}",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        self.doc["timestamp"] = int(discord.utils.utcnow().timestamp())
        await self.bot.partnership.insert_one(self.doc)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Partnership Log Created",
                description="The partnership log has been successfully created and saved.",
                color=BLANK_COLOR
            ), ephemeral=True
        )

        sett = await self.bot.settings.find_by_id(self.ctx.guild.id)
        channel_id = sett.get("partnership_module", {}).get("partnership_channel")
        partner_role = sett.get("partnership_module", {}).get("partner_role")
        if channel_id:
            channel = self.ctx.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title=self.doc["title"],
                    description=self.doc["description"],
                    color=discord.Color(self.doc["color"])
                )
                if self.doc["image"]:
                    embed.set_image(url=self.doc["image"])
                if self.doc["thumbnail"]:
                    embed.set_thumbnail(url=self.doc["thumbnail"])
                for field in self.doc["fields"]:
                    embed.add_field(name=field["name"], value=field["value"], inline=False)
                embed.set_footer(text=f"Represented by: {self.ctx.guild.get_member(self.doc['representative']).name} `Partnership ID: {self.partnership_id}`")
                msg_content = self.doc["message"] if self.doc["message"] else None
                await channel.send(content=msg_content, embed=embed)
        if partner_role:
            role = self.ctx.guild.get_role(partner_role)
            if role:
                member = self.ctx.guild.get_member(self.doc["representative"])
                if member and role not in member.roles:
                    try:
                        await member.add_roles(role, reason="Granted partner role for partnership log.")
                    except Exception as e:
                        print(f"Failed to add partner role: {e}")
        await interaction.message.edit(view=None)