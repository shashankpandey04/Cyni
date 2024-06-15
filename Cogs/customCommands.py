import discord
from discord.ext import commands
from db import mycon
from cyni import on_command_error
from utils import check_permissions, check_permissions_management
class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="custom", aliases=["cc"], brief="Custom Commands", description="Custom Commands", usage="custom", help="Custom Commands")
    async def custom(self, ctx):
        pass

    @custom.command()
    async def run(self, ctx, command_name: str):
        '''Run Custom Command'''
        if await self.check_permissions(ctx, ctx.author):
            await self.run_custom_command(ctx, command_name)
            embed = discord.Embed(
                title="Custom Command Executed",
                description=f"Custom Command {command_name} executed by {ctx.author.mention}",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ You don't have permission to use this command.")

    @custom.command()
    async def list(self, ctx):
        '''List Custom Commands'''
        await self.list_custom_commands(ctx)

    @custom.command()
    async def manage(self, ctx, action: str, name: str):
        '''Manage Custom Commands (create, delete, list)'''
        guild_id = ctx.guild.id
        try:
            if await self.check_permissions_management(ctx, ctx.author):
                if action == 'create':
                    await self.create_custom_command(ctx, name)
                elif action == 'delete':
                    await self.delete_custom_command(ctx, name)
                else:
                    await ctx.send("Invalid action. Valid actions are: create, delete")
                    await ctx.channel.purge(limit=1)
            else:
                await ctx.send("❌ You don't have permission to use this command.")
        except Exception as error:
            await self.on_command_error(ctx, error)

    async def load_custom_command(self, ctx):
        try:
            guild_id = str(ctx.guild.id)
            if mycon.is_connected():
                cursor = mycon.cursor(dictionary=True)
                cursor.execute("SELECT * FROM custom_commands where guild_id = %s", (guild_id,))
                rows = cursor.fetchall()
                config = {}
                for row in rows:
                    guild_id = str(row['guild_id'])
                    command_name = row['command_name']
                    title = row['title']
                    description = row['description']
                    color = row['color']
                    image_url = row['image_url']
                    channel = row['channel']
                    role = row['role']
                    if guild_id not in config:
                        config[guild_id] = {}
                    config[guild_id][command_name] = {
                        'title': title,
                        'description': description,
                        'colour': color,
                        'image_url': image_url,
                        'channel': channel,
                        'role': role
                    }
                return config
        except Exception as e:
            print("Error while connecting to MySQL", e)
        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
        return {}

    async def list_custom_commands(self, ctx):
        config = await self.load_custom_command(ctx)
        guild_id = str(ctx.guild.id)
        custom_commands = config.get(guild_id, {})
        if not custom_commands:
            await ctx.send(embed=discord.Embed(description="No custom commands found for this server.", color=0x2F3136))
            return
        embed = discord.Embed(title="Custom Commands", color=0x2F3136)
        for name, details in custom_commands.items():
            channel = ctx.guild.get_channel(details.get('channel'))
            role_mention = f"<@&{details.get('role')}>" if details.get('role') else "N/A"
            embed.add_field(
                name=f"Command Name: {name}",
                value=f"**Channel:** {channel.mention if channel else 'N/A'}\n**Role Mention:** {role_mention}",
                inline=False
            )
        await ctx.send(embed=embed)

    async def run_custom_command(self, ctx, command_name):
        try:
            mycur = mycon.cursor()
            guild_id = str(ctx.guild.id)
            mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
            command_details = mycur.fetchone()
            if command_details:
                title = command_details[2]
                description = command_details[3]
                color = discord.Colour(int(command_details[4]))  # Convert to discord.Colour
                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=color
                )
                embed.set_footer(text="Executed By: " + ctx.author.name)
                if command_details[5]:
                    embed.set_image(url=command_details[5])
                channel_id = command_details[6]
                channel = self.bot.get_channel(channel_id)
                role_id = command_details[7]
                if role_id:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        await channel.send(f"<@&{role_id}>")
                    else:
                        await ctx.send("Role not found. Please make sure the role exists.")
                        return
                await channel.send(embed=embed)
            else:
                await ctx.send(f"Custom command '{command_name}' not found.")
        except Exception as e:
            print(f"An error occurred while running custom command: {e}")
        finally:
            mycur.close()

    async def create_custom_command(self, ctx, command_name):
        try:
            mycur = mycon.cursor()
            guild_id = str(ctx.guild.id)
            mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
            existing_command = mycur.fetchone()
            if existing_command:
                await ctx.channel.send(f"Custom command '{command_name}' already exists.")
                return
            mycur.execute("SELECT COUNT(*) FROM custom_commands WHERE guild_id = %s", (guild_id,))
            command_count = mycur.fetchone()[0]
            if command_count >= 5:
                await ctx.channel.send("Sorry, the server has reached the maximum limit of custom commands (5).")
                return
            await ctx.channel.send("Enter embed title:")
            title = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
            await ctx.channel.send("Enter embed description:")
            description = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
            await ctx.channel.send("Enter embed colour (hex format, e.g., #RRGGBB):")
            colour = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
            await ctx.channel.send("Enter image URL (enter 'none' for no image):")
            image_url_input = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
            await ctx.channel.send("Enter default channel to post message (mention the channel):")
            channel_input = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
            await ctx.channel.send("Enter role ID to ping (enter 'none' for no role):")
            role_id_input = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60)
            channel_id = int(channel_input.content[2:-1])
            role_id = int(role_id_input.content) if role_id_input.content.lower() != 'none' else None
            try:
                color_decimal = int(colour.content[1:], 16)
            except ValueError:
                await ctx.send("Invalid hex color format. Please use the format #RRGGBB.")
                return
            image_url = image_url_input.content.strip()
            image_url = None if image_url.lower() == 'none' else image_url
            channel_id_str = channel_input.content.strip('<#>')
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                await ctx.send("Invalid channel mention. Please mention a valid channel.")
                return
            mycur.execute("INSERT INTO custom_commands (guild_id, command_name, title, description, color, image_url, channel, role) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (guild_id, command_name, title.content, description.content, color_decimal, image_url, channel_id, role_id))
            mycon.commit()
            await ctx.send(f"Custom command '{command_name}' created successfully.")
        except Exception as e:
            print(f"An error occurred while creating custom command: {e}")
        finally:
            mycur.close()

    async def delete_custom_command(self, ctx, command_name):
        try:
            mycur = mycon.cursor()
            guild_id = str(ctx.guild.id)
            mycur.execute("SELECT * FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
            existing_command = mycur.fetchone()

            if not existing_command:
                await ctx.channel.send(f"Custom command '{command_name}' not found.")
                return
            mycur.execute("DELETE FROM custom_commands WHERE guild_id = %s AND command_name = %s", (guild_id, command_name))
            mycon.commit()
            await ctx.channel.send(f"Custom command '{command_name}' deleted successfully.")
        except Exception as e:
            print(f"An error occurred while deleting custom command: {e}")
        finally:
            mycur.close()

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(CustomCommands(bot))
