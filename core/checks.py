from discord.ext import commands


def check_staff():
    async def predicate(ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if await ctx.bot.staff_check(ctx.guild, ctx.author):
            return True

        raise commands.MissingPermissions(["Staff"])

    return commands.check(predicate)


def check_management():
    async def predicate(ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if await ctx.bot.management_check(ctx.guild, ctx.author):
            return True

        raise commands.MissingPermissions(["Management"])

    return commands.check(predicate)


def check_roblox_staff():
    async def predicate(ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if await ctx.bot.roblox_staff_check(ctx.guild, ctx.author):
            return True

        raise commands.MissingPermissions(["Roblox Staff"])

    return commands.check(predicate)


def check_roblox_management():
    async def predicate(ctx: commands.Context):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if await ctx.bot.roblox_management_check(ctx.guild, ctx.author):
            return True

        raise commands.MissingPermissions(["Roblox Management"])

    return commands.check(predicate)
