import discord

async def get_member(ctx):
    return await ctx.guild.fetch_member(ctx.author.id) if isinstance(ctx.author, discord.User) else ctx.author


def convert_duration(duration: int) -> str:
    duration = duration // 1000

    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)

    return f'{hours:02d}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes:02d}:{seconds:02d}'