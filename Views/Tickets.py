import discord
import datetime
import uuid
import os
from Database.Mongo import mongo_db as db

placeholders = {
    "user_id": "{user_id}", # This will be replaced with the user's ID
    "username": "{username}", # This will be replaced with the user's name
    "guild_id": "{guild_id}", # This will be replaced with the guild ID
    "channel_id": "{channel_id}", # This will be replaced with the channel ID
    "ticket_id": "{ticket_id}", # This will be replaced with the ticket ID
    "user": "{user}", # This will be replaced with the user's mention
    "ticket_name": "{ticket_name}", # This will be replaced with the ticket name
    "category_name": "{category_name}", # This will be replaced with the category name
    "created_at": "{created_at}", # This will be replaced with the ticket creation time
}

roblox_placeholders = {
    "roblox_userid": "{roblox_userid}", # This will be replaced with the Roblox user ID
    "roblox_username": "{roblox_username}", # This will be replaced with the Roblox username
    "roblox_display_name": "{roblox_display_name}", # This will be replaced with the Roblox display name
    "roblox_profile": "{roblox_profile}", # This will be replaced with the Roblox profile link
    "roblox_avatar": "{roblox_avatar}", # This will be replaced with the Roblox avatar image URL
    "roblox_created_at": "{roblox_created_at}", # This will be replaced with the Roblox account creation date
    "roblox_joined_at": "{roblox_joined_at}", # This will be replaced with the Roblox account join date
    "roblox_bio": "{roblox_bio}", # This will be replaced with the Roblox bio
    "roblox_friends_count": "{roblox_friends_count}", # This will be replaced with the number of friends on Roblox
    "roblox_followers_count": "{roblox_followers_count}", # This will be replaced with the number of followers on Roblox
}

class TicketButton(discord.ui.Button):
    def __init__(self, emoji, label, custom_id, style, guild, category_id, category, logger):
        """
        Initializes a button for creating a ticket.
        :param emoji: The emoji to display on the button.
        :param label: The label for the button.
        :param custom_id: A unique identifier for the button.
        :param style: The style of the button (e.g., primary, secondary).
        :param guild: The Discord guild (server) where the button will be used.
        :param category_id: The ID of the category for the ticket.
        :param category: The category data containing support roles and other info.
        :param logger: Logger instance for logging errors.
        """
        super().__init__(emoji=emoji, label=label, custom_id=custom_id, style=style)
        self.guild = guild
        self.category_id = category_id
        self.category = category
        self.logger = logger

    async def _check_existing_ticket(self, user_id: int) -> dict:
        """Check if user already has an open ticket in this category."""
        return db.tickets.find_one({
            "guild_id": self.guild.id,
            "user_id": user_id,
            "category_id": self.category_id,
            "status": "open"
        })

    def _create_channel_overwrites(self, user: discord.Member) -> dict:
        """Create permission overwrites for the ticket channel."""
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            self.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Add support roles
        for role_id in self.category.get("support_roles", []):
            role = self.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        return overwrites

    async def _generate_ticket_id(self) -> str:
        """Generate a unique ticket ID."""
        ticket_count = db.tickets.count_documents({"guild_id": self.guild.id})
        ticket_id = ticket_count + 1
        return str(ticket_id).zfill(3)

    async def _create_ticket_channel(self, user: discord.Member, ticket_id: str, overwrites: dict) -> discord.TextChannel:
        """Create the ticket channel."""
        channel_name = f"ticket-{ticket_id}-{user.name}"
        
        discord_category = None
        if self.category.get("discord_category"):
            discord_category = self.guild.get_channel(self.category.get("discord_category"))

        try:
            return await self.guild.create_text_channel(
                name=channel_name[:100],
                overwrites=overwrites,
                category=discord_category,
                reason=f"Ticket created by {user.name}"
            )
        except Exception as e:
            self.logger.error(f"Failed to create ticket channel: {e}")
            raise

    def _create_ticket_data(self, user: discord.Member, channel: discord.TextChannel) -> dict:
        """Create ticket data for database storage."""
        return {
            "_id": str(uuid.uuid4()),
            "guild_id": self.guild.id,
            "user_id": user.id,
            "username": user.name,
            "category_id": self.category_id,
            "category_name": self.category.get("name"),
            "channel_id": channel.id,
            "status": "open",
            "created_at": datetime.datetime.now().timestamp(),
            "claimed_by": None,
            "claimed_at": None,
            "messages": [],
            "transcript": None
        }

    def _create_welcome_embed(self, user: discord.Member, wl_embed: dict) -> discord.Embed:
        """Create welcome embed for the ticket."""
        embed = discord.Embed(
            title=f"Ticket: {self.category.get('name')}",
            description=f"Thank you for creating a ticket, {user.mention}!\n\nSupport will be with you shortly.",
            color=0x5865F2,
        )
        if wl_embed:
            embed.title = wl_embed.get("title", embed.title)
            embed.description = wl_embed.get("description", embed.description)
            embed.color = wl_embed.get("color", embed.color)
            embed.thumbnail = wl_embed.get("thumbnail", None)
            embed.image = wl_embed.get("image", None)
            embed.footer = wl_embed.get("footer", None)
            embed.timestamp = datetime.datetime.now()
        return embed

    async def callback(self, interaction: discord.Interaction):
        """Main callback for ticket creation."""
        await interaction.response.defer(ephemeral=True)
        
        existing_ticket = await self._check_existing_ticket(interaction.user.id)
        if existing_ticket:
            channel_id = existing_ticket.get("channel_id")
            channel = self.guild.get_channel(channel_id)
            if channel:
                return await interaction.followup.send(
                    f"You already have an open ticket: {channel.mention}", 
                    ephemeral=True
                )
        
        try:
            overwrites = self._create_channel_overwrites(interaction.user)
            
            ticket_id = await self._generate_ticket_id()
            
            ticket_channel = await self._create_ticket_channel(interaction.user, ticket_id, overwrites)
            
            ticket_data = self._create_ticket_data(interaction.user, ticket_channel)
            
            db.tickets.insert_one(ticket_data)
            
            welcome_embed = self._create_welcome_embed(interaction.user, self.category.get("wl_embed"))
            
            action_view = TicketActionView(ticket_data, self.guild, self.category, self.logger)
            
            await ticket_channel.send(
                f"Ticket created by {interaction.user.mention}.\n\nPlease wait for a support member to assist you.",
                embed=welcome_embed,
                view=action_view
            )
            
            await interaction.followup.send(
                f"Ticket created successfully! {ticket_channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {e}")
            await interaction.followup.send(
                "Failed to create ticket channel. Please contact an administrator.",
                ephemeral=True
            )


class TicketActionView(discord.ui.View):
    """View containing claim and close buttons for tickets."""
    
    def __init__(self, ticket_data: dict, guild: discord.Guild, category: dict, logger):
        super().__init__(timeout=None)
        self.ticket_data = ticket_data
        self.guild = guild
        self.category = category
        self.logger = logger

        close_button = discord.ui.Button(
            style=discord.ButtonStyle.danger, 
            label="Close Ticket", 
            custom_id=f"close_ticket:{ticket_data['_id']}"
        )
        close_button.callback = self._close_callback
        self.add_item(close_button)

        claim_button = discord.ui.Button(
            style=discord.ButtonStyle.primary, 
            label="Claim Ticket",
            custom_id=f"claim_ticket:{ticket_data['_id']}"
        )
        claim_button.callback = self._claim_callback
        self.add_item(claim_button)

    def _has_support_role(self, user: discord.Member) -> bool:
        """Check if user has any support role."""
        for role_id in self.category.get("support_roles", []):
            role = self.guild.get_role(role_id)
            if role and role in user.roles:
                return True
        return False

    async def _claim_callback(self, interaction: discord.Interaction):
        """Handle ticket claiming."""
        if interaction.user.id == self.ticket_data["user_id"]:
            return await interaction.response.send_message(
                "You cannot claim your own ticket.",
                ephemeral=True
            )
        
        if self.ticket_data["claimed_by"]:
            return await interaction.response.send_message(
                "This ticket is already claimed by someone else.",
                ephemeral=True
            )
        
        # Update database
        db.tickets.update_one(
            {"_id": self.ticket_data["_id"]},
            {"$set": {"claimed_by": interaction.user.id, "claimed_at": datetime.datetime.now().timestamp()}}
        )
        
        # Update local data
        self.ticket_data["claimed_by"] = interaction.user.id
        self.ticket_data["claimed_at"] = datetime.datetime.now().timestamp()
        
        await interaction.response.send_message(
            f"You have claimed the ticket. {interaction.user.mention}",
            ephemeral=True
        )
        
        # Notify in ticket channel
        ticket_channel = self.guild.get_channel(self.ticket_data["channel_id"])
        if ticket_channel:
            await ticket_channel.send(f"{interaction.user.mention} has claimed this ticket.")
        else:
            self.logger.error(f"Ticket channel {self.ticket_data['channel_id']} not found.")

    async def _close_callback(self, interaction: discord.Interaction):
        """Handle ticket closing."""
        is_creator = interaction.user.id == self.ticket_data["user_id"]
        has_support_role = self._has_support_role(interaction.user)

        if not has_support_role and not is_creator:
            return await interaction.response.send_message(
                "You don't have permission to close this ticket.",
                ephemeral=True
            )
        
        db.tickets.update_one(
            {"_id": self.ticket_data["_id"]},
            {"$set": {"status": "closed"}}
        )

        closing_embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket has been closed by {interaction.user.mention}.",
            color=0xED4245,
            timestamp=datetime.datetime.now()
        )
 
        delete_view = TicketDeleteView(self.ticket_data, self.guild, self.category, self.logger, has_support_role)
        
        await interaction.response.send_message(embed=closing_embed, view=delete_view)


class TicketDeleteView(discord.ui.View):
    """View for deleting closed tickets."""
    
    def __init__(self, ticket_data: dict, guild: discord.Guild, category: dict, logger, has_support_role: bool):
        super().__init__(timeout=None)
        self.ticket_data = ticket_data
        self.guild = guild
        self.category = category
        self.logger = logger
        self.has_support_role = has_support_role
        
        delete_button = discord.ui.Button(
            style=discord.ButtonStyle.danger, 
            label="Delete Ticket", 
            custom_id=f"delete_ticket:{ticket_data['_id']}"
        )
        delete_button.callback = self._delete_callback
        self.add_item(delete_button)

    async def _collect_messages(self, channel: discord.TextChannel) -> list:
        """Collect all messages from the ticket channel."""
        messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            if message.content or message.embeds:
                messages.append({
                    "author_id": message.author.id,
                    "author_name": message.author.name,
                    "content": message.content,
                    "created_at": message.created_at.timestamp(),
                    "attachments": [
                        {"url": attachment.url, "filename": attachment.filename} 
                        for attachment in message.attachments
                    ]
                })
        return messages

    async def _create_transcript(self, messages: list, closed_by: discord.Member) -> str:
        """Create and save transcript to database."""
        transcript_id = str(uuid.uuid4())
        transcript_data = {
            "_id": transcript_id,
            "ticket_id": self.ticket_data["_id"],
            "guild_id": self.guild.id,
            "user_id": self.ticket_data["user_id"],
            "username": self.ticket_data["username"],
            "category_name": self.category.get("name"),
            "messages": messages,
            "closed_by": closed_by.id,
            "closed_by_name": closed_by.name,
            "created_at": datetime.datetime.now().timestamp()
        }
        
        db.ticket_transcripts.insert_one(transcript_data)
        return transcript_id

    async def _send_transcript_notification(self, transcript_id: str, closed_by: discord.Member):
        """Send transcript notification to designated channel."""
        transcript_channel_id = self.category.get("transcript_channel")
        if not transcript_channel_id:
            return
            
        transcript_channel = self.guild.get_channel(int(transcript_channel_id))
        if not transcript_channel:
            return
        
        base_url = os.getenv("BASE_URL", "https://cyni.quprdigital.tk")
        transcript_url = f"{base_url}/transcripts/{transcript_id}"
        
        transcript_embed = discord.Embed(
            title=f"Ticket Transcript: {self.category.get('name')}",
            description=f"Ticket from {self.ticket_data['username']} has been closed and archived.",
            color=0x5865F2,
            timestamp=datetime.datetime.now()
        )
        transcript_embed.add_field(name="Ticket ID", value=self.ticket_data["_id"], inline=True)
        transcript_embed.add_field(name="Closed By", value=closed_by.name, inline=True)
        transcript_embed.add_field(name="View Transcript", value=f"[Click Here]({transcript_url})", inline=False)
        
        await transcript_channel.send(embed=transcript_embed)

    async def _delete_callback(self, interaction: discord.Interaction):
        """Handle ticket deletion."""
        if not self.has_support_role:
            return await interaction.response.send_message(
                "Only staff can delete tickets.",
                ephemeral=True
            )
        
        ticket_channel = self.guild.get_channel(self.ticket_data["channel_id"])
        if not ticket_channel:
            return await interaction.response.send_message(
                "Ticket channel not found.",
                ephemeral=True
            )
        
        try:
            messages = await self._collect_messages(ticket_channel)
    
            transcript_id = await self._create_transcript(messages, interaction.user)

            await self._send_transcript_notification(transcript_id, interaction.user)

            base_url = os.getenv("BASE_URL", "https://cyni.quprdigital.tk")
            transcript_url = f"{base_url}/transcripts/{transcript_id}"
            
            final_embed = discord.Embed(
                title="Ticket Closed",
                description=f"This ticket has been closed by {interaction.user.mention}.",
                color=0xED4245,
                timestamp=datetime.datetime.now()
            )
            final_embed.add_field(
                name="Transcript", 
                value=f"[Click here to view the ticket transcript]({transcript_url})",
                inline=False
            )
            
            await interaction.response.send_message(embed=final_embed)
            
            await ticket_channel.delete(reason=f"Ticket deleted by {interaction.user.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to delete ticket channel: {e}")
            await interaction.response.send_message(
                "Failed to delete ticket. Please contact an administrator.",
                ephemeral=True
            )


class TicketView(discord.ui.View):
    def __init__(self, guild, category_id, category, logger):
        super().__init__(timeout=None)
        self.add_item(TicketButton(
            emoji=category.get("emoji", "🎫"),
            label=f"Create {category.get('name')}",
            custom_id=f"create_ticket:{category_id}",
            style=discord.ButtonStyle.secondary,
            guild=guild,
            category_id=category_id,
            category=category,
            logger=logger
        ))