from discord.ui import Button, View
from discord import Interaction, ButtonStyle
import discord
from menu import CustomModal
from utils.constants import BLANK_COLOR

class MessageQuotaManager(View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    async def interaction_check(self, interaction):
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(
        label="Create Quota",
        style=ButtonStyle.secondary,
        custom_id="create_quota_button"
    )
    async def create_quota(self, interaction: Interaction, button: Button):
        """
        Handle the Create Quota button interaction.
        """
        premium = await self.bot.premium.find_by_id(interaction.guild.id)
        quota_doc = await self.bot.message_quotas.find_by_id(interaction.guild.id)

        if not premium and quota_doc is not None and len(quota_doc) - 1 >= 3: #subtract 1 for _id field
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Quota Limit Reached",
                    description="You have reached the limit of 3 message quotas for free servers. Upgrade to premium to create more quotas.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        view = MessageQuotaHandler(self.bot, self.ctx, "", {})
        embed = discord.Embed(
            title="Create Message Quota",
            description="Please fill out the modal to create a new message quota.",
            color=BLANK_COLOR
        ).add_field(
            name="Quota Name",
            value="A unique name for this quota (e.g., 'Member Quota').",
            inline=False
        ).add_field(
            name="Role",
            value="Users with this role will be affected by the quota.",
            inline=False
        ).add_field(
            name="Quota Number",
            value="The minimum number of messages a user must send.",
            inline=False
        )
        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.defer()

    @discord.ui.button(
        label="Edit",
        style=ButtonStyle.secondary,
        custom_id="edit_quota_button"
    )
    async def edit_quota(self, interaction: Interaction, button: Button):
        """
        Handle the Edit Quota button interaction.
        """
        quota_doc = await self.bot.message_quotas.find_by_id(interaction.guild.id)
        if not quota_doc or len(quota_doc) == 1:  # Only _id field exists
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Quotas Found",
                    description="There are no message quotas to edit.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        modal = CustomModal(
            "Quota Type Name",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Quota Name",
                        placeholder="Enter the name for the quota (e.g., 'Member Quota')",
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
        
        #now check if the quota exists
        if title not in quota_doc:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Quota Not Found",
                    description=f"No quota found with the name '{title}'.",
                    color=discord.Color.red()
                ), ephemeral=True
            )
            return
        
        quota_data = quota_doc[title]
        view = MessageQuotaHandler(self.bot, self.ctx, title, quota_data, "edit")

        embed = discord.Embed(
            title="Edit Message Quota",
            description=f"Edit the message quota for {title}.",
            color=BLANK_COLOR
        )
        embed.add_field(
            name="Quota Name",
            value=f"Created quota with name: **{title}**",
            inline=False
        )
        embed.add_field(
            name="Role",
            value=f"Users with the role <@&{quota_data['role_id']}> will be affected by this quota.",
            inline=False
        )
        embed.add_field(
            name="Quota Number",
            value=f"The minimum number of messages a user must send is {quota_data['quota']}.",
            inline=False
        )
        await interaction.message.edit(embed=embed, view=view)

class RoleSelect(View):
    def __init__(self, ctx, main_message, quota_handler):
        super().__init__(timeout=60)  # Set a reasonable timeout
        self.ctx = ctx
        self.main_message = main_message
        self.quota_handler = quota_handler  # Reference to the main handler
        self.role = None

        self.role_select = discord.ui.RoleSelect(
            placeholder="Select a role Message Quota applies to",
            min_values=1,
            max_values=1,
            default_values=[discord.Object(id=self.quota_handler.quota_data.get("role_id"))] if self.quota_handler.quota_data.get("role_id") else None
        )
        self.role_select.callback = self.role_callback
        self.add_item(self.role_select)

    async def role_callback(self, interaction: Interaction):
        self.role = self.role_select.values[0]
        
        self.quota_handler.quota_data["role_id"] = self.role.id
        
        self.main_message.embeds[0].set_field_at(
            1, 
            name="Role", 
            value=f"Users with the role <@&{self.role.id}> will be affected by this quota.", 
            inline=False
        )
        await self.main_message.edit(embed=self.main_message.embeds[0])
        
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Role Selected",
                description=f"Successfully selected role <@&{self.role.id}>",
                color=discord.Color.green()
            ),
            view=None
        )
        self.stop()
        
class MessageQuotaHandler(View):
    def __init__(self, bot, ctx, quota_name: str, quota_data: dict, mode: str="create"):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.quota_name = quota_name
        self.quota_data = quota_data
        self.mode = mode

        # quota_data structure is like this:
        # {
        #     "role_id": int,
        #     "quota": int 
        # }

        # the doc structure is like this:
        # {
        #     "_id": guild_id,
        #     "quota_name_1": {
        #         "role_id": int,
        #         "quota": int 
        #     },
        #     "quota_name_2": {
        #         "role_id": int,
        #         "quota": int
        #     }
        #     ...
        # }


    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id
    
    @discord.ui.button(
        label="Quota Name",
        style=ButtonStyle.secondary,
        custom_id="quota_name_button",
    )
    async def quota_name(self, interaction: Interaction, button: Button):
        """
        Handle the Quota Name button interaction.
        """
        if self.mode == "edit":
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You can't modify existing quota type names!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
        modal = CustomModal(
            "Quota Type Name",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Quota Name",
                        placeholder="Enter the name for the quota (e.g., 'Member Quota')",
                        required=True,
                        max_length=256,
                        default=self.quota_name
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
        self.quota_name = title
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Quota Name", value=f"Created quota with name: **{self.quota_name}**", inline=False)
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Select Role",
        style=ButtonStyle.secondary,
        custom_id="role_select"
    )
    async def role_select(self, interaction: Interaction, button: Button):
        """
        Handle the Role Select button interaction.
        """
        role_view = RoleSelect(self.ctx, interaction.message, self)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Select Role",
                description="Please select a role from the dropdown below.",
                color=BLANK_COLOR
            ),
            view=role_view,
            ephemeral=True
        )

    @discord.ui.button(
        label="Set Quota Number",
        style=ButtonStyle.secondary,
        custom_id="set_quota_number_button",
        row=1
    )
    async def set_quota_number(self, interaction: Interaction, button: Button):
        """
        Handle the Set Quota Number button interaction.
        """
        modal = CustomModal(
            "Set Quota Number",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Quota Number",
                        placeholder="Enter the quota number (e.g., '5')",
                        required=True,
                        max_length=3,
                        default=str(self.quota_data.get("quota", 0))
                    )
                )
            ],
        )
        await interaction.response.send_modal(modal)
        if await modal.wait():
            return

        quota_number = modal.values.get("value")
        if not quota_number:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="No Quota Number Provided",
                    description="You must provide a quota number.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        
        # Validate quota_number is an integer and positive
        if not quota_number.isdigit() or int(quota_number) <= 0:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="Invalid Quota Number",
                    description="Quota number must be a positive integer.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
        

        self.quota_data["quota"] = int(quota_number)
        embed = interaction.message.embeds[0]
        embed.set_field_at(2, name="Quota Number", value=f"The minimum number of messages a user must send is {self.quota_data['quota']}.", inline=False)
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Save Quota",
        style=ButtonStyle.success,
        custom_id="save_quota_button",
        row=1
    )
    async def save_quota(self, interaction: Interaction, button: Button):
        """
        Handle the Save Quota button interaction.
        """
        #self.bot.logger.info(f"Saving quota: {self.quota_name} with data: {self.quota_data}")
        
        if not self.quota_name:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Quota Name Missing",
                    description="You must set a quota name before saving.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
            
        if not self.quota_data.get("role_id"):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Role Not Selected",
                    description="You must select a role before saving.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return
            
        if "quota" not in self.quota_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Quota Number Not Set",
                    description="You must set a quota number before saving.",
                    color=BLANK_COLOR
                ), ephemeral=True
            )
            return

        # Get existing document or create new one
        quota_doc = await self.bot.message_quotas.find_by_id(interaction.guild.id) or {"_id": interaction.guild.id}
        
        # Update or add the new quota (fix the logic here)
        quota_doc[self.quota_name] = self.quota_data
        
        # Save to database
        await self.bot.message_quotas.update_one(
            {"_id": interaction.guild.id},
            {"$set": quota_doc},
            upsert=True
        )
        embed = discord.Embed(
            title="Quota Saved",
            description=f"Successfully saved quota **{self.quota_name}**.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)