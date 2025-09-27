import discord
from datetime import datetime
from utils.utils import time_converter
from menu import CustomModal

class CustomExecutionButton(discord.ui.Button):
    def __init__(self, user_id: int, func, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.func = func

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Permitted",
                    description="You cannot use this button.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
        if self.func:
            await self.func(interaction, self)


class ShiftManagerContainer(discord.ui.Container):
    def __init__(self, bot, ctx, status, shift_type, shift_data, past_shifts, break_count):
        super().__init__(id=1)
        self.bot = bot
        self.ctx = ctx
        self.status = status
        self.shift_type = shift_type
        self.shift_data = shift_data
        self.past_shifts = past_shifts
        self.break_count = break_count

        # Create the main section content based on status
        section_content = self._get_section_content()

        # Create main section with thumbnail
        main_section = discord.ui.Section(
            accessory=discord.ui.Thumbnail(
                media=ctx.author.display_avatar.url
            )
        ).add_item(section_content)

        self.add_item(main_section)

        # Create action buttons
        self._add_action_buttons()

    def _get_section_content(self):
        """Generate section content based on current status"""
        if self.status == "onbreak":
            breaks = self.shift_data.get("breaks", [])
            last_break = breaks[-1] if breaks else None
            break_start_time = "N/A"
            
            if last_break:
                if isinstance(last_break, dict):
                    break_start_time = f"<t:{int(last_break.get('start_epoch', 0))}:F>"
                elif isinstance(last_break, list) and len(last_break) > 0:
                    break_start_time = f"<t:{int(last_break[0])}:F>"

            total_duration_seconds = sum(shift.get('duration', 0) for shift in self.past_shifts) if self.past_shifts else 0
            removed_time = sum(shift.get("removed_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds -= removed_time
            added_time = sum(shift.get("added_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds = max(0, total_duration_seconds + added_time - removed_time)

            days, remainder = divmod(total_duration_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days > 0:
                total_duration = f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                total_duration = f"{hours}h {minutes}m {seconds}s"
            else:
                total_duration = f"{minutes}m {seconds}s" if total_duration_seconds > 0 else "0"

            return f"## {self.bot.emoji.get('shiftbreak')} On-Break\n### Current Statistics\n> **Shift Type:** {self.shift_type.capitalize()}\n> **Shift Start:** <t:{int(self.shift_data['start_epoch'])}:F>\n> **Break Started:** {break_start_time}\n\n### Overall Statistics\n> **Total Shifts:** {len(self.past_shifts)}\n> **Total Duration:** {total_duration}"

        elif self.status == "onduty":
            total_duration_seconds = sum(shift.get('duration', 0) for shift in self.past_shifts) if self.past_shifts else 0
            removed_time = sum(shift.get("removed_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds -= removed_time
            added_time = sum(shift.get("added_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds = max(0, total_duration_seconds + added_time - removed_time)

            days, remainder = divmod(total_duration_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days > 0:
                total_duration = f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                total_duration = f"{hours}h {minutes}m {seconds}s"
            else:
                total_duration = f"{minutes}m {seconds}s" if total_duration_seconds > 0 else "Not Applicable"

            return f"## {self.bot.emoji.get('onshift')} On-Duty\n### Current Statistics\n> **Shift Type:** {self.shift_type.capitalize()}\n> **Shift Start:** <t:{int(self.shift_data['start_epoch'])}:F>\n> **Breaks:** {self.break_count} Break(s)\n\n### Overall Statistics\n> **Total Shifts:** {len(self.past_shifts)}\n> **Total Duration:** {total_duration}"

        else:  # offduty
            total_duration_seconds = sum(shift.get('duration', 0) for shift in self.past_shifts) if self.past_shifts else 0
            removed_time = sum(shift.get("removed_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds -= removed_time
            added_time = sum(shift.get("added_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds = max(0, total_duration_seconds + added_time - removed_time)

            days, remainder = divmod(total_duration_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days > 0:
                total_duration = f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                total_duration = f"{hours}h {minutes}m {seconds}s"
            else:
                total_duration = f"{minutes}m {seconds}s" if total_duration_seconds > 0 else "Not Applicable"

            return f"## {self.bot.emoji.get('offshift')} Off-Duty\n### Current Statistics\n> **Shift Type:** {self.shift_type.capitalize()}\n> **Total Shifts:** {len(self.past_shifts)}\n> **Total Duration:** {total_duration}"

    def _add_action_buttons(self):
        """Add action buttons based on current status"""
        start_button_label = "Start Shift" if self.status == "offduty" else "Resume Shift" if self.status == "onbreak" else "On Shift"
        start_button_disabled = self.status == "onduty"
        break_button_disabled = self.status == "offduty" or self.status == "onbreak"
        end_button_disabled = self.status == "offduty"

        # Create action row with buttons
        shift_actions = discord.ui.ActionRow(
            CustomExecutionButton(
                self.ctx.author.id, 
                label=start_button_label, 
                style=discord.ButtonStyle.green, 
                disabled=start_button_disabled,
                func=self.start_shift_callback
            ),
            CustomExecutionButton(
                self.ctx.author.id, 
                label="Toggle Break", 
                style=discord.ButtonStyle.secondary, 
                disabled=break_button_disabled,
                func=self.toggle_break_callback
            ),
            CustomExecutionButton(
                self.ctx.author.id, 
                label="End Shift", 
                style=discord.ButtonStyle.red, 
                disabled=end_button_disabled,
                func=self.end_shift_callback
            ),
        )

        self.add_item(shift_actions)

    async def start_shift_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        timestamp = int(datetime.now().timestamp())
        
        if self.status == "onbreak":
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": interaction.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        f"breaks.{len(self.shift_data.get('breaks', [])) - 1}.end_epoch": timestamp
                    }
                }
            )
            oid = await self.bot.shift_logs.find_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": interaction.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                }
            )
            self.bot.dispatch("shift_break", oid["_id"], "end", timestamp)
            success_message = "Break ended! You are now back on duty."
        else:
            sett = await self.bot.settings.find_by_id(interaction.guild.id)
            erlc_linked  = await self.bot.erlc.find_by_id(interaction.guild.id)
            if erlc_linked:
                if sett and sett.get("roblox", {}).get("shift_module", {}).get("require_staff_ingame", False):
                    in_game = await self.bot.prc_api._is_user_in_game(interaction.guild.id, interaction.user.id)
                    if isinstance(in_game, tuple) and not in_game[1]:
                        return await interaction.response.send_message(
                            embed=in_game[0],
                            ephemeral=True
                        )
                    await self.bot.prc_api._permission_sync(interaction.user, sett, interaction.guild, "start")
            elif not erlc_linked and sett and sett.get("roblox", {}).get("shift_module", {}).get("require_staff_ingame", False):
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="HyperSync AI - Server Not Linked",
                        description=(
                            f"**CYNI HyperSync AI** has detected that this server requires mandatory staff in-game presence,\n"
                            "but it is not linked to a PRC server. Please link your server using `/erlc link` command."
                        ),
                        color=discord.Color.red()
                    ).set_footer(
                        text="Powered by CYNI HyperSync AI"
                    ),
                    ephemeral=True
                )
        
            doc = {
                "guild_id": interaction.guild.id,
                "user_id": interaction.user.id,
                "username": interaction.user.name,
                "nickname": interaction.user.nick if interaction.user.nick else interaction.user.name,
                "type": self.shift_type.lower(),
                "start_epoch": timestamp,
                "end_epoch": 0,
                "breaks": [],
                "added_time": 0,
                "removed_time": 0,
                "moderations": [],
                "duration": 0
            }
            await self.bot.shift_logs.insert_one(doc)
            success_message = "Shift started successfully!"
            doc_id = await self.bot.shift_logs.find_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": interaction.user.id,
                    "type": self.shift_type.lower(),
                    "start_epoch": timestamp
                }
            )
            self.bot.dispatch("shift_start", doc_id["_id"])

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('onshift')} Shift Action",
                description=success_message,
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

        await self.refresh_view(interaction)

    async def toggle_break_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        timestamp = int(datetime.now().timestamp())
        
        new_break = {
            "start_epoch": timestamp,
            "end_epoch": 0
        }

        try:
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": interaction.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$push": {"breaks": new_break}
                }
            )
            oid = await self.bot.shift_logs.find_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": interaction.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                }
            )
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('error')} Error",
                    description="There was an error starting your break.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        self.bot.dispatch("shift_break", oid["_id"], "start", timestamp)
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('shiftbreak')} Break Started",
                description="You are now on break.",
                color=discord.Color.from_rgb(255, 255, 0),
            ),
            ephemeral=True,
        )

        # Refresh the view
        await self.refresh_view(interaction)

    async def end_shift_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        timestamp = int(datetime.now().timestamp())
        
        if self.status == "onbreak":
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": interaction.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        f"breaks.{len(self.shift_data.get('breaks', [])) - 1}.end_epoch": timestamp
                    }
                }
            )

            self.shift_data = await self.bot.shift_logs.find_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": interaction.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                }
            )

        start_time = self.shift_data.get('start_epoch', timestamp) if self.shift_data else timestamp
        end_time = timestamp

        # Calculate total shift duration
        total_duration = end_time - start_time

        # Calculate total break time
        total_break_time = 0
        if self.shift_data and "breaks" in self.shift_data:
            for b in self.shift_data["breaks"]:
                if isinstance(b, dict):
                    break_start = b.get("start_epoch")
                    break_end = b.get("end_epoch")
                    
                    # Only process breaks that have both start and end times
                    if break_start is not None and break_end is not None:
                        # Clip break to shift boundaries
                        effective_start = max(start_time, break_start)
                        effective_end = min(end_time, break_end)
                        
                        # Only subtract if the break actually overlaps with the shift
                        if effective_end > effective_start:
                            total_break_time += (effective_end - effective_start)

        duration = max(total_duration - total_break_time, 0)
        
        #print(f"Total shift: {total_duration}s, Break time: {total_break_time}s, Working time: {duration}s")
        
        days = duration // 86400
        hours = (duration % 86400) // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60

        await self.bot.shift_logs.update_one(
            {
                "guild_id": interaction.guild.id,
                "user_id": interaction.user.id,
                "type": self.shift_type.lower(),
                "end_epoch": 0,
            },
            {
                "$set": {
                    "end_epoch": timestamp,
                    "duration": duration
                }
            }
        )
        
        doc_id = await self.bot.shift_logs.find_one(
            {
                "guild_id": interaction.guild.id,
                "user_id": interaction.user.id,
                "type": self.shift_type.lower(),
                "end_epoch": timestamp
            }
        )
        
        print(doc_id["duration"])
        self.bot.dispatch("shift_end", doc_id["_id"])
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('offshift')} Shift Ended",
                description=f"Your shift has been ended. Duration: {days}d {hours}h {minutes}m {seconds}s",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )
        
        sett = await self.bot.settings.find_by_id(interaction.guild.id)
        if sett and sett.get("roblox", {}).get("shift_module", {}).get("require_staff_ingame", False):
            await self.bot.prc_api._permission_sync(interaction.user, sett, interaction.guild, "end")

        await self.refresh_view(interaction)

    async def refresh_view(self, interaction):
        """Refresh the entire view with updated data"""
        updated_active_shift = await self.bot.shift_logs.find(
            {
                "guild_id": interaction.guild.id,
                "user_id": interaction.user.id,
                "type": self.shift_type.lower(),
                "end_epoch": 0
            }
        )
        
        updated_past_shifts = await self.bot.shift_logs.find(
            {
                "guild_id": interaction.guild.id,
                "user_id": interaction.user.id,
                "type": self.shift_type.lower(),
                "end_epoch": {"$ne": 0}
            }
        )

        new_status = "offduty"
        new_break_count = 0
        new_shift_data = None
        
        if updated_active_shift:
            new_shift_data = updated_active_shift[0] if len(updated_active_shift) > 0 else {}
            
            if new_shift_data:
                new_status = "onduty"
                breaks = new_shift_data.get("breaks", [])
                new_break_count = len(breaks)

                if breaks:
                    for b in breaks:
                        if isinstance(b, dict):
                            if b.get("end_epoch", 0) == 0:
                                new_status = "onbreak"
                                break
                        elif isinstance(b, list) and len(b) > 1:
                            if len(b) < 2 or b[1] == 0:
                                new_status = "onbreak"
                                break
        
        new_view = ShiftManagerView(self.bot, self.ctx, self.shift_type, updated_active_shift, updated_past_shifts)

        try:
            await interaction.edit_original_response(view=new_view)
        except:
            await interaction.message.edit(view=new_view)


class ShiftManagerView(discord.ui.LayoutView):
    def __init__(self, bot, ctx, shift_type, active_shift, past_shifts):
        super().__init__(timeout=None)
        
        status = "offduty"
        break_count = 0
        shift_data = None
        
        if active_shift:
            shift_data = active_shift[0] if len(active_shift) > 0 else {}
            
            if shift_data:
                status = "onduty"
                breaks = shift_data.get("breaks", [])
                break_count = len(breaks)

                if breaks:
                    for b in breaks:
                        if isinstance(b, dict):
                            if b.get("end_epoch", 0) == 0:
                                status = "onbreak"
                                break
                        elif isinstance(b, list) and len(b) > 1:
                            if len(b) < 2 or b[1] == 0:
                                status = "onbreak"
                                break

        self.container = ShiftManagerContainer(bot, ctx, status, shift_type, shift_data, past_shifts, break_count)
        self.add_item(self.container)

class ShiftDeleteConfirm(discord.ui.View):
    def __init__(self, bot, ctx, shift_type):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.shift_type = shift_type

        self.confirm_button = discord.ui.Button(
            label="Confirm",
            style=discord.ButtonStyle.danger
        )
        self.add_item(self.confirm_button)
        self.confirm_button.callback = self.confirm_button_callback

    async def confirm_button_callback(self, interaction: discord.Interaction):
        deleted_shifts = await self.bot.shift_logs.find(
            {"guild_id": interaction.guild.id, "type": self.shift_type}
        )
        if deleted_shifts:
            await self.bot.deleted_shifts.insert_many(deleted_shifts)
        await self.bot.shift_logs.delete_many({"guild_id": interaction.guild.id, "type": self.shift_type})
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Shift Deleted",
                description=f"The shift of type `{self.shift_type}` has been deleted.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class ShiftLeaderBoardMenu(discord.ui.View):
    def __init__(self, bot, ctx, shift_type: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.shift_type = shift_type

        self.reset_leaderboard_button = discord.ui.Button(
            label="Reset Leaderboard",
            style=discord.ButtonStyle.danger
        )
        self.add_item(self.reset_leaderboard_button)
        self.reset_leaderboard_button.callback = self.reset_leaderboard

    async def reset_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Are you sure you want to reset the leaderboard?",
                description="This action cannot be undone.",
                color=discord.Color.red()
            ),
            ephemeral=True,
            view=ShiftDeleteConfirm(self.bot, self.ctx, self.shift_type)
        )

class ShiftAdminView(discord.ui.View):
    def __init__(self, bot, ctx, user: discord.User, shift_type, active_shift, past_shifts, status):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.user = user
        self.shift_type = shift_type
        self.active_shift = active_shift
        self.past_shifts = past_shifts
        self.status = status
        
        # Initialize buttons with proper states
        self._setup_buttons()

    def _setup_buttons(self):
        """Setup buttons with proper states based on current status"""
        # Clear existing items to avoid duplicates
        self.clear_items()
        
        self.start_shift_button = discord.ui.Button(
            label="Start Shift",
            style=discord.ButtonStyle.green,
            disabled=self.status == "onduty",
            row=0
        )
        self.start_shift_button.callback = self.start_shift_callback
        self.add_item(self.start_shift_button)

        self.toggle_break_button = discord.ui.Button(
            label="Toggle Break",
            style=discord.ButtonStyle.secondary,
            disabled=self.status == "offduty",
            row=0
        )
        self.toggle_break_button.callback = self.toggle_break_callback
        self.add_item(self.toggle_break_button)

        self.end_shift_button = discord.ui.Button(
            label="End Shift",
            style=discord.ButtonStyle.red,
            disabled=self.status == "offduty",
            row=0
        )
        self.end_shift_button.callback = self.end_shift_callback
        self.add_item(self.end_shift_button)

        self.add_time_button = discord.ui.Button(
            label="Add Time",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        self.add_time_button.callback = self.add_time_callback
        self.add_item(self.add_time_button)

        self.remove_time_button = discord.ui.Button(
            label="Remove Time",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        self.remove_time_button.callback = self.remove_time_callback
        self.add_item(self.remove_time_button)

    def _get_active_shift_data(self):
        """Helper method to get active shift data consistently"""
        if not self.active_shift:
            return None
        if isinstance(self.active_shift, list):
            return self.active_shift[0] if len(self.active_shift) > 0 else None
        return self.active_shift
    
    async def start_shift_callback(self, interaction: discord.Interaction):
        timestamp = int(datetime.now().timestamp())
        
        if self.status == "onbreak":
            # End the current break
            active_data = self._get_active_shift_data()
            if active_data:
                breaks = active_data.get('breaks', [])
                if breaks:
                    await self.bot.shift_logs.update_one(
                        {
                            "guild_id": interaction.guild.id,
                            "user_id": self.user.id,
                            "type": self.shift_type.lower(),
                            "end_epoch": 0
                        },
                        {
                            "$set": {
                                f"breaks.{len(breaks) - 1}.end_epoch": timestamp
                            }
                        }
                    )
                    oid = await self.bot.shift_logs.find_one(
                        {
                            "guild_id": interaction.guild.id,
                            "user_id": self.user.id,
                            "type": self.shift_type.lower(),
                            "end_epoch": 0
                        }
                    )
                    self.bot.dispatch("shift_break", oid["_id"], "end", timestamp)
            success_message = f"Break ended for <@{self.user.id}>! They are now back on duty."
        else:
            # Start new shift
            doc = {
                "guild_id": interaction.guild.id,
                "user_id": self.user.id,
                "username": self.user.name,
                "nickname": self.user.nick if self.user.nick else self.user.name,
                "type": self.shift_type.lower(),
                "start_epoch": timestamp,
                "end_epoch": 0,
                "breaks": [],
                "added_time": 0,
                "removed_time": 0,
                "moderations": [],
                "duration": 0
            }
            await self.bot.shift_logs.insert_one(doc)
            success_message = f"Shift started successfully for <@{self.user.id}>!"
            doc_id = await self.bot.shift_logs.find_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "start_epoch": timestamp
                }
            )
            self.bot.dispatch("shift_start", doc_id["_id"])

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('onshift')} Shift Action",
                description=success_message,
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

        await self.refresh_view(self.user, interaction)

    async def toggle_break_callback(self, interaction: discord.Interaction):
        timestamp = int(datetime.now().timestamp())
        
        new_break = {
            "start_epoch": timestamp,
            "end_epoch": 0
        }

        try:
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$push": {"breaks": new_break}
                }
            )
            oid = await self.bot.shift_logs.find_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                }
            )
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('error')} Error",
                    description="There was an error starting the break.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        
        self.bot.dispatch("shift_break", oid["_id"], "start", timestamp)
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('shiftbreak')} Break Started",
                description=f"<@{self.user.id}> is now on break.",
                color=discord.Color.from_rgb(255, 255, 0),
            ),
            ephemeral=True,
        )

        # Refresh the view
        await self.refresh_view(self.user, interaction)

    async def end_shift_callback(self, interaction: discord.Interaction):
        timestamp = int(datetime.now().timestamp())
        active_data = self._get_active_shift_data()
        
        if self.status == "onbreak" and active_data:
            # End current break first
            breaks = active_data.get('breaks', [])
            if breaks:
                await self.bot.shift_logs.update_one(
                    {
                        "guild_id": interaction.guild.id,
                        "user_id": self.user.id,
                        "type": self.shift_type.lower(),
                        "end_epoch": 0
                    },
                    {
                        "$set": {
                            f"breaks.{len(breaks) - 1}.end_epoch": timestamp
                        }
                    }
                )

                # Refresh active shift data
                active_data = await self.bot.shift_logs.find_one(
                    {
                        "guild_id": interaction.guild.id,
                        "user_id": self.user.id,
                        "type": self.shift_type.lower(),
                        "end_epoch": 0
                    }
                )

        if not active_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('error')} Error",
                    description="No active shift found to end.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return

        start_time = active_data.get('start_epoch', timestamp)
        end_time = timestamp

        # Calculate total shift duration
        total_duration = end_time - start_time

        # Calculate total break time
        total_break_time = 0
        if "breaks" in active_data:
            for b in active_data["breaks"]:
                if isinstance(b, dict):
                    break_start = b.get("start_epoch")
                    break_end = b.get("end_epoch")
                    
                    if break_start is not None and break_end is not None:
                        effective_start = max(start_time, break_start)
                        effective_end = min(end_time, break_end)
                        
                        if effective_end > effective_start:
                            total_break_time += (effective_end - effective_start)

                elif isinstance(b, list) and len(b) > 1:
                    break_start = b[0]
                    break_end = b[1]
                    
                    if break_start is not None and break_end is not None:
                        effective_start = max(start_time, break_start)
                        effective_end = min(end_time, break_end)
                        
                        if effective_end > effective_start:
                            total_break_time += (effective_end - effective_start)

        duration = max(total_duration - total_break_time, 0)
        days, remainder = divmod(duration, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            total_duration_str = f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            total_duration_str = f"{hours}h {minutes}m {seconds}s"
        else:
            total_duration_str = f"{minutes}m {seconds}s" if duration > 0 else "0"

        await self.bot.shift_logs.update_one(
            {
                "guild_id": interaction.guild.id,
                "user_id": self.user.id,
                "type": self.shift_type.lower(),
                "end_epoch": 0,
            },
            {
                "$set": {
                    "end_epoch": timestamp,
                    "duration": duration
                }
            }
        )
        
        doc_id = await self.bot.shift_logs.find_one(
            {
                "guild_id": interaction.guild.id,
                "user_id": self.user.id,
                "type": self.shift_type.lower(),
                "end_epoch": timestamp
            }
        )
        
        self.bot.dispatch("shift_end", doc_id["_id"])
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{self.bot.emoji.get('offshift')} Shift Ended",
                description=f"<@{self.user.id}>'s shift has been ended. Duration: {total_duration_str}",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )
        await self.refresh_view(self.user, interaction)

    async def add_time_callback(self, interaction: discord.Interaction):
        modal = CustomModal(
            "Add Time to Shift",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Time to Add (minutes)",
                        placeholder="Enter time in minutes",
                        required=True,
                        max_length=500
                    )
                )
            ],
        )

        await interaction.response.send_modal(modal)

        if await modal.wait():
            return

        added_time = modal.values.get("value", "")
        seconds = time_converter(added_time)
        if seconds is None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('error')} Error",
                    description="Invalid time format. Please enter a valid time (e.g., '30m' for 30 minutes).",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        active_data = self._get_active_shift_data()
        if not active_data:
            # Find last shift
            last_shift_list = await self.bot.shift_logs.find(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": {"$ne": 0}
                }
            ).sort("end_epoch", -1).limit(1)
            
            if not last_shift_list:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{self.bot.emoji.get('error')} Error",
                        description="No active or past shifts found to add time to.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            
            last_shift = last_shift_list[0]
            await self.bot.shift_logs.update_one(
                {"_id": last_shift["_id"]},
                {
                    "$set": {
                        "added_time": last_shift.get("added_time", 0) + seconds
                    },
                }
            )
        else:
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        "added_time": active_data.get("added_time", 0) + seconds
                    },
                }
            )
            
        await interaction.followup.send(
            embed=discord.Embed(
                title="Time Added",
                description=f"Successfully added `{added_time}` to <@{self.user.id}>'s shift.",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )
        await self.refresh_view(self.user, interaction)

    async def remove_time_callback(self, interaction: discord.Interaction):
        modal = CustomModal(
            "Remove Time from Shift",
            [
                (
                    "value",
                    discord.ui.TextInput(
                        label="Time to Remove (minutes)",
                        placeholder="Enter time in minutes",
                        required=True,
                        max_length=500
                    )
                )
            ],
        )

        await interaction.response.send_modal(modal)

        if await modal.wait():
            return

        removed_time = modal.values.get("value", "")
        seconds = time_converter(removed_time)
        if seconds is None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{self.bot.emoji.get('error')} Error",
                    description="Invalid time format. Please enter a valid time (e.g., '30m' for 30 minutes).",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        active_data = self._get_active_shift_data()
        if not active_data:
            # Find last shift
            last_shift_list = await self.bot.shift_logs.find(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": {"$ne": 0}
                }
            ).sort("end_epoch", -1).limit(1)
            
            if not last_shift_list:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{self.bot.emoji.get('error')} Error",
                        description="No active or past shifts found to remove time from.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            
            last_shift = last_shift_list[0]
            await self.bot.shift_logs.update_one(
                {"_id": last_shift["_id"]},
                {
                    "$set": {
                        "removed_time": last_shift.get("removed_time", 0) + seconds
                    },
                }
            )
        else:
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        "removed_time": active_data.get("removed_time", 0) + seconds
                    },
                }
            )
            
        await interaction.followup.send(
            embed=discord.Embed(
                title="Time Removed",
                description=f"Successfully removed `{removed_time}` from <@{self.user.id}>'s shift.",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )
        await self.refresh_view(self.user, interaction)

    async def refresh_view(self, user: discord.User, interaction: discord.Interaction):
        """Refresh the entire view with updated data"""
        try:
            # Get updated active shift data
            updated_active_shift = await self.bot.shift_logs.find(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                }
            )
            
            # Get updated past shifts data
            updated_past_shifts = await self.bot.shift_logs.find(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": {"$ne": 0}
                }
            )

            # Determine new status
            new_status = "offduty"
            
            if updated_active_shift and len(updated_active_shift) > 0:
                shift_data = updated_active_shift[0]
                new_status = "onduty"
                
                breaks = shift_data.get("breaks", [])
                if breaks:
                    for b in breaks:
                        if isinstance(b, dict):
                            if b.get("end_epoch", 0) == 0:
                                new_status = "onbreak"
                                break
                        elif isinstance(b, list) and len(b) >= 2:
                            if b[1] == 0:
                                new_status = "onbreak"
                                break

            self.active_shift = updated_active_shift
            self.past_shifts = updated_past_shifts
            self.status = new_status
            
            self._setup_buttons()

            updated_embed = await self._create_shift_embed(user, interaction.guild.id)

            await interaction.message.edit(embed=updated_embed, view=self)
                
        except Exception as e:
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(view=self)
                else:
                    await interaction.message.edit(view=self)
            except:
                pass

    async def _create_shift_embed(self, user: discord.User, guild_id: int):
        """Create the shift status embed"""
        if self.status == "onduty":
            status_emoji = self.bot.emoji.get('onshift')
            status_text = "On Duty"
            status_color = discord.Color.green()
        elif self.status == "onbreak":
            status_emoji = self.bot.emoji.get('shiftbreak')
            status_text = "On Break"
            status_color = discord.Color.from_rgb(255, 255, 0)
        else:
            status_emoji = self.bot.emoji.get('offshift')
            status_text = "Off Duty"
            status_color = discord.Color.red()

        embed = discord.Embed(
            title=f"{status_emoji} {status_text}",
            color=status_color
        )

        embed.add_field(
            name="Staff Information",
            value=(
                f"**User:** {user.mention} (`{user.id}`)\n"
                f"**Shift Type:** {self.shift_type.title()}\n"
                f"**Past Shifts:** {len(self.past_shifts) if self.past_shifts else 0}\n"
                f"**Total Past Duration:** {self._calculate_total_past_duration()}"
            ),
            inline=False
        )
        if self.active_shift and len(self.active_shift) > 0:
            shift_data = self.active_shift[0]
            start_time = shift_data.get('start_epoch', 0)
            current_time = int(datetime.now().timestamp())
            
            if start_time:
                duration = current_time - start_time
                breaks = shift_data.get('breaks', [])
                
                total_break_time = 0
                for b in breaks:
                    if isinstance(b, dict):
                        break_start = b.get("start_epoch", 0)
                        break_end = b.get("end_epoch", current_time if b.get("end_epoch", 0) == 0 else b.get("end_epoch", 0))
                        if break_start and break_end:
                            total_break_time += (break_end - break_start)
                
                active_duration = duration - total_break_time
                embed.add_field(
                    name="Active Shift",
                    value=(
                        f"**Started:** <t:{start_time}:R>\n"
                        f"**Duration:** {self._format_duration(active_duration)}\n"
                        f"**Breaks:** {len(breaks)}"
                    ),
                    inline=False
                )

        embed.add_field(
            name="Management",
            value=f"Managing shifts for {user.mention} | User ID: {user.id}",
            inline=False
        )

        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        return embed

    def _calculate_total_past_duration(self):
        """Calculate total duration of all past shifts"""
        if not self.past_shifts:
            return "0s"
        
        total_seconds = 0
        for shift in self.past_shifts:
            duration = shift.get('duration', 0)
            added_time = shift.get('added_time', 0)
            removed_time = shift.get('removed_time', 0)
            total_seconds += duration + added_time - removed_time
        
        return self._format_duration(total_seconds)

    def _format_duration(self, seconds):
        """Format duration in seconds to readable string"""
        if seconds <= 0:
            return "0s"
        
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        else:
            return f"{minutes}m {secs}s"