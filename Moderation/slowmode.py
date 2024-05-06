import discord
from discord.ext import commands
from cyni import on_command_error
from utils import check_permissions
class SlowMode(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="slowmode", aliases=["slow"])
    async def slowmode(self, ctx, duration: str):
        '''Sets slowmode in channel'''
        time_units = {'s': 1, 'm': 60, 'h': 3600}
        try:
            if await check_permissions(ctx, ctx.author):
                try:
                    amount = int(duration[:-1])
                    unit = duration[-1]
                    if unit not in time_units:
                        raise ValueError
                except (ValueError, IndexError):
                    await ctx.send('Invalid duration format. Please use a number followed by "s" for seconds, "m" for minutes, or "h" for hours.',ephemeral=True)
                    return
                total_seconds = amount * time_units[unit]
                if total_seconds == 0:
                    await ctx.send("Slow mode disabled from the channel.")
                elif total_seconds > 21600:
                    await ctx.send('Slow mode duration cannot exceed 6 hours (21600 seconds).')
                    return
                else:
                    await ctx.channel.edit(slowmode_delay=total_seconds)
                    await ctx.send(f'Slow mode set to {amount} {unit} in this channel.',ephemeral=True)
            else:
                await ctx.send("❌ You don't have permission to use this command.")
        except Exception as error:
                await on_command_error(ctx, error)

async def setup(bot):
   await bot.add_cog(SlowMode(bot))