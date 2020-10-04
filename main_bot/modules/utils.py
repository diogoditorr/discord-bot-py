import discord


async def get_member(ctx):
    return await ctx.guild.fetch_member(ctx.author.id) if isinstance(ctx.author, discord.User) else ctx.author