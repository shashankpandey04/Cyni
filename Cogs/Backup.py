import discord
from discord.ext import commands

from discord import app_commands
from utils.constants import RED_COLOR, BLANK_COLOR, GREEN_COLOR
from utils.utils import log_command_usage
from utils.utils import create_full_backup
from cyni import is_premium

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="backup",
        extras={
            "category": "Backup"
        }
    )
    async def backup(self, ctx):
        pass

    @backup.command(
        name="create",
        extras={
            "category": "Backup"
        }
    )
    @commands.is_owner()
    @commands.guild_only()
    @commands.DisabledCommand(message="This command is under development.")
    @is_premium()
    async def create(self, ctx):
        """
        Create a backup of the Server Template.
        """
        if isinstance(ctx,commands.Context):
            await log_command_usage(self.bot,ctx.guild,ctx.author,"Backup Create")
        backup_info = await create_full_backup(ctx.guild,self.bot)
        await ctx.send(
            embed=discord.Embed(
                title="Backup Created",
                description=f"Backup created successfully. {backup_info['_id']}",
                color=GREEN_COLOR
            )
        )


 
async def setup(bot):
    await bot.add_cog(Backup(bot))