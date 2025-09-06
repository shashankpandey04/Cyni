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

            hours, remainder = divmod(total_duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            total_duration = f"{hours}h {minutes}m {seconds}s" if total_duration_seconds > 0 else "Not Applicable"

            return f"## {self.bot.emoji.get('shiftbreak')} On-Break\n### Current Statistics\n> **Shift Type:** {self.shift_type.capitalize()}\n> **Shift Start:** <t:{int(self.shift_data['start_epoch'])}:F>\n> **Break Started:** {break_start_time}\n\n### Overall Statistics\n> **Total Shifts:** {len(self.past_shifts)}\n> **Total Duration:** {total_duration}"

        elif self.status == "onduty":
            total_duration_seconds = sum(shift.get('duration', 0) for shift in self.past_shifts) if self.past_shifts else 0
            removed_time = sum(shift.get("removed_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds -= removed_time
            added_time = sum(shift.get("added_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds = max(0, total_duration_seconds + added_time - removed_time)

            hours, remainder = divmod(total_duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            total_duration = f"{hours}h {minutes}m {seconds}s" if total_duration_seconds > 0 else "Not Applicable"

            return f"## {self.bot.emoji.get('onshift')} On-Duty\n### Current Statistics\n> **Shift Type:** {self.shift_type.capitalize()}\n> **Shift Start:** <t:{int(self.shift_data['start_epoch'])}:F>\n> **Breaks:** {self.break_count} Break(s)\n\n### Overall Statistics\n> **Total Shifts:** {len(self.past_shifts)}\n> **Total Duration:** {total_duration}"

        else:  # offduty
            total_duration_seconds = sum(shift.get('duration', 0) for shift in self.past_shifts) if self.past_shifts else 0
            removed_time = sum(shift.get("removed_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds -= removed_time
            added_time = sum(shift.get("added_time", 0) for shift in self.past_shifts) if self.past_shifts else 0
            total_duration_seconds = max(0, total_duration_seconds + added_time - removed_time)
            hours, remainder = divmod(total_duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            total_duration = f"{hours}h {minutes}m {seconds}s" if total_duration_seconds > 0 else "Not Applicable"

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
        
        hours = duration // 3600
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
                description=f"Your shift has been ended. Duration: {hours}h {minutes}m {seconds}s",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

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

        # Determine new status
        new_status = "offduty"
        new_break_count = 0
        new_shift_data = None
        
        if updated_active_shift:
            new_shift_data = updated_active_shift[0] if len(updated_active_shift) > 0 else {}
            
            if new_shift_data:
                new_status = "onduty"
                breaks = new_shift_data.get("breaks", [])
                new_break_count = len(breaks)

                # Check if any break is currently active
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
        
        # Create new view with updated data
        new_view = ShiftManagerView(self.bot, self.ctx, self.shift_type, updated_active_shift, updated_past_shifts)
        
        # Update the message with new view
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

                # Check if any break is currently active
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

        # Create and add the container
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
        # Take all shift_logs and add into deleted_shifts
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
            disabled=self.status == "onbreak" or self.status == "offduty",
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
    
    async def _refresh(self, components):
        return super()._refresh(components)
    
    async def start_shift_callback(self, interaction: discord.Interaction):
        timestamp = int(datetime.now().timestamp())
        
        if self.status == "onbreak":
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        f"breaks.{len(self.active_shift[0].get('breaks', [])) - 1}.end_epoch": timestamp
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
            success_message = f"Break ended for <@{self.active_shift[0]['user_id']}>! They are now back on duty."
        else:
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
            success_message = f"Shift started successfully for <@{self.active_shift[0]['user_id']}>!"
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

        await self.refresh_view(interaction)

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
                description=f"<@{self.active_shift[0]['user_id']}> is now on break.",
                color=discord.Color.from_rgb(255, 255, 0),
            ),
            ephemeral=True,
        )

        # Refresh the view
        await self.refresh_view(interaction)

    async def end_shift_callback(self, interaction: discord.Interaction):
        timestamp = int(datetime.now().timestamp())
        
        if self.status == "onbreak":
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        f"breaks.{len(self.active_shift[0].get('breaks', [])) - 1}.end_epoch": timestamp
                    }
                }
            )

            self.active_shift = await self.bot.shift_logs.find_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                }
            )

        start_time = self.active_shift.get('start_epoch', timestamp) if self.active_shift else timestamp
        end_time = timestamp

        # Calculate total shift duration
        total_duration = end_time - start_time

        # Calculate total break time
        total_break_time = 0
        if self.active_shift and "breaks" in self.active_shift:
            for b in self.active_shift["breaks"]:
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

                elif isinstance(b, list) and len(b) > 1:
                    break_start = b[0]
                    break_end = b[1]
                    
                    # Only process breaks that have both start and end times
                    if break_start is not None and break_end is not None:
                        # Clip break to shift boundaries
                        effective_start = max(start_time, break_start)
                        effective_end = min(end_time, break_end)
                        
                        # Only subtract if the break actually overlaps with the shift
                        if effective_end > effective_start:
                            total_break_time += (effective_end - effective_start)

        duration = max(total_duration - total_break_time, 0)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
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
                description=f"<@{self.active_shift[0]['user_id']}>'s shift has been ended. Duration: {hours}h {minutes}m {seconds}s",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )
        await self.refresh_view(interaction)

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
        if self.active_shift is None or len(self.active_shift) == 0:
            last_shift_cursor = await self.bot.shift_logs.find(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": {"$ne": 0}
                }
            )
            last_shift = last_shift_cursor[0]
            if last_shift is None or len(last_shift) == 0:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{self.bot.emoji.get('error')} Error",
                        description="No active or past shifts found to add time to.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": last_shift["end_epoch"]
                },
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
                        "added_time": self.active_shift.get("added_time", 0) + seconds
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
        await self.refresh_view(interaction)

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
        if self.active_shift is None or len(self.active_shift) == 0:
            last_shift_cursor = await self.bot.shift_logs.find(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": {"$ne": 0}
                }
            )
            last_shift = last_shift_cursor[0]
            if last_shift is None or len(last_shift) == 0:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{self.bot.emoji.get('error')} Error",
                        description="No active or past shifts found to remove time from.",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            await self.bot.shift_logs.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "user_id": self.user.id,
                    "type": self.shift_type.lower(),
                    "end_epoch": last_shift["end_epoch"]
                },
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
                    "user_id": self.active_shift[0]["user_id"],
                    "type": self.shift_type.lower(),
                    "end_epoch": 0
                },
                {
                    "$set": {
                        "removed_time": self.active_shift[0].get("removed_time", 0) + seconds
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
        await self.refresh_view(interaction)