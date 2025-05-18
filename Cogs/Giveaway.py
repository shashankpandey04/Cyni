import discord
from discord.ext import commands
from cyni import is_management
from utils.constants import BLANK_COLOR
from datetime import datetime, timedelta
import random
from utils.utils import log_command_usage, parse_duration
import collections.abc
import re
from discord import app_commands
import traceback
import sys

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="giveaway",
        extras={
            "category": "Giveaway"
        }
    )
    async def giveaway(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please use a subcommand like `create`, `list`, or `roll`.")

    async def fallback_handler(self, ctx, title, description, duration, total_winner, host):
        """Fallback handler for when hybrid commands fail"""
        try:
            # Log command usage (for non-interaction context)
            if isinstance(ctx, commands.Context):
                await log_command_usage(self.bot, ctx.guild, ctx.author, f"Giveaway Create for {title}")
            
            # Process the duration
            duration_seconds = parse_duration(duration)
            if duration_seconds is None:
                await ctx.send("Invalid duration format. Please use formats like '2d', '1w', '3h', '45m', '30s'.")
                return
            
            # Calculate end time
            end_time = datetime.now() + timedelta(seconds=duration_seconds)
            end_time_epoch = int(end_time.timestamp())
            description = re.sub(r'\\n', '\n', description)
            formatted_description = (
                f"{description}\n\n"
                f"Ends At: <t:{end_time_epoch}:F>\n"
                f"Total Winner: {total_winner}\n"
                f"Host: {host.mention}"
            )

            # Create embed
            embed = discord.Embed(
                title=f"<:giveaway:1268849874233725000> {title}",
                description=formatted_description,
                color=BLANK_COLOR
            )
            
            # Send initial message
            msg = await ctx.send(embed=embed)
            message_id = msg.id
            channel_id = msg.channel.id
            
            # Create view with button
            view = discord.ui.View()
            embed.set_footer(text=f"Giveaway ID: {message_id}")
            button = discord.ui.Button(
                label="View Giveaway",
                style=discord.ButtonStyle.link,
                url=f"https://cyni.quprdigital.tk/giveaway/{message_id}",
                emoji="🎉"
            )
            view.add_item(button)
            
            # Update message with view
            await msg.edit(embed=embed, view=view)
            await msg.add_reaction("🎉")
            
            # Store in database
            await self.bot.giveaways.insert_one({
                "message_id": message_id,
                "channel_id": channel_id,
                "guild_id": ctx.guild.id,
                "title": title,
                "description": description,
                "duration_epoch": end_time_epoch,
                "total_winner": total_winner,
                "host": host.id,
                "participants": []
            })
            
            return True
        except Exception as e:
            error_text = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
            print(error_text)
            try:
                await ctx.send(f"An error occurred: {str(e)}")
            except:
                pass
            return False

    @giveaway.command(
        name="create",
        extras={
            "category": "Giveaway"
        }
    )
    @is_management()
    @app_commands.describe(title = "Giveaway Embed Title")
    @app_commands.describe(description = "Write the description & for new line use \\n\\n")
    @app_commands.describe(duration = "Duration of the giveaway")
    @app_commands.describe(total_winner = "Total winner of the giveaway")
    @app_commands.describe(host = "Host of the giveaway")
    async def create(self, ctx, title: str, description: str, duration: str, total_winner: int, host: discord.Member):
        """
        Create a giveaway.
        """
        try:
            # Try to use the normal hybrid command flow
            if isinstance(ctx, commands.Context):
                await log_command_usage(self.bot, ctx.guild, ctx.author, f"Giveaway Create for {title}")
            
            duration_seconds = parse_duration(duration)
            if duration_seconds is None:
                await ctx.send("Invalid duration format. Please use formats like '2d', '1w', '3h', '45m', '30s'.")
                return
            
            end_time = datetime.now() + timedelta(seconds=duration_seconds)
            end_time_epoch = int(end_time.timestamp())
            description = re.sub(r'\\n', '\n', description)
            formatted_description = (
                f"{description}\n\n"
                f"Ends At: <t:{end_time_epoch}:F>\n"
                f"Total Winner: {total_winner}\n"
                f"Host: {host.mention}"
            )

            view = discord.ui.View()
            embed = discord.Embed(
                title=f"<:giveaway:1268849874233725000> {title}",
                description=formatted_description,
                color=BLANK_COLOR
            )
            
            msg = await ctx.send(embed=embed)
            message_id = msg.id
            channel_id = msg.channel.id

            embed.set_footer(text=f"Giveaway ID: {message_id}")
            button = discord.ui.Button(
                label="View Giveaway",
                style=discord.ButtonStyle.link,
                url=f"https://cyni.quprdigital.tk/giveaway/{message_id}",
                emoji="🎉"
            )
            view.add_item(button)
            
            await msg.edit(embed=embed, view=view)
            await msg.add_reaction("🎉")
            
            # Store in database
            await self.bot.giveaways.insert_one({
                "message_id": message_id,
                "channel_id": channel_id,
                "guild_id": ctx.guild.id,
                "title": title,
                "description": description,
                "duration_epoch": end_time_epoch,
                "total_winner": total_winner,
                "host": host.id,
                "participants": []
            })
        except Exception as e:
            error_text = f"Error in hybrid command: {str(e)}\n{traceback.format_exc()}"
            print(error_text)
            
            # Fall back to a simpler implementation if the hybrid command fails
            success = await self.fallback_handler(ctx, title, description, duration, total_winner, host)
            if not success:
                await ctx.send("Command failed. Try using the regular command prefix instead.")

    @giveaway.command(
        name="roll",
        extras={
            "category": "Giveaway"
        }
    )
    @is_management()
    async def roll(self, ctx, message_id: str):
        """
        Roll a giveaway.
        """
        message_id = int(message_id)
        giveaway = await self.bot.giveaways.find_one({"message_id": message_id})
        if giveaway is None:
            await ctx.send("<:declined:1268849944455024671> Giveaway not found.")
            return
        if datetime.now().timestamp() < giveaway["duration_epoch"]:
            await ctx.send("<:giveaway:1268849874233725000> Giveaway is still active.")
            return
        participants = giveaway["participants"]
        if len(participants) < giveaway["total_winner"]:
            await ctx.send("<:declined:1268849944455024671>  Not enough participants.")
            return
        winners = random.sample(participants, giveaway["total_winner"])
        await ctx.send(f"<:giveaway:1268849874233725000> Congratulations to {', '.join([f'<@{winner}>' for winner in winners])} for winning the {giveaway['title']} giveaway!\nHosted by <@{giveaway['host']}>")
        msg = await ctx.fetch_message(message_id)
        embed = msg.embeds[0]
        embed.description += f"\n\nWinner(s): {', '.join([f'<@{winner}>' for winner in winners])}"
        await msg.edit(embed=embed)

    @giveaway.command(
        name="list",
        extras={
            "category": "Giveaway"
        }
    )
    @is_management()
    async def list(self, ctx):
        """
        List all active giveaways.
        """
        giveaways = await self.bot.giveaways.find({"guild_id": ctx.guild.id})
        
        if not giveaways:
            await ctx.send("No active giveaways.")
            return
        active_giveaways = [giveaway for giveaway in giveaways if datetime.now().timestamp() < giveaway["duration_epoch"]]

        if not active_giveaways:
            await ctx.send("No active giveaways.")
            return
        embed = discord.Embed(
            title="Active Giveaways",
            color=BLANK_COLOR
        )
        for giveaway in active_giveaways:
            embed.add_field(
                name=f"{giveaway['title']} - {giveaway['message_id']}",
                value=f"Hosted by <@{giveaway['host']}>\nEnds at <t:{giveaway['duration_epoch']}:F>",
                inline=False
            )
        await ctx.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        Adds a user to the participants list when they react with 🎉.
        """
        if user.bot:
            return
        
        if str(reaction.emoji) != "🎉":
            return

        message_id = reaction.message.id
        giveaway = await self.bot.giveaways.find_one({"message_id": message_id})
        if giveaway is None:
            return

        if user.id not in giveaway["participants"]:
            participants = giveaway["participants"]
            participants.append(user.id)
            
            # Use update_one instead of update
            await self.bot.giveaways.update_one(
                {"message_id": message_id}, 
                {"participants": participants}
            )
            
            await reaction.message.channel.send(f"{user.mention} has entered the giveaway!", delete_after=2)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """
        Removes a user from the participants list when they remove their reaction.
        """
        if user.bot:
            return
        
        if str(reaction.emoji) != "🎉":
            return

        message_id = reaction.message.id
        giveaway = await self.bot.giveaways.find_one({"message_id": message_id})
        if giveaway is None:
            return

        if user.id in giveaway["participants"]:
            participants = giveaway["participants"]
            participants.remove(user.id)
            
            # Use update_one instead of update
            await self.bot.giveaways.update_one(
                {"message_id": message_id}, 
                {"participants": participants}
            )
            
            await reaction.message.channel.send(f"{user.mention} has left the giveaway!", delete_after=2)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
