import discord
import time
import random
from discord.ext import commands

from ..database.database import Database

def permsVerify(context):
    perm = ['Admins']
    roles = [x.name for x in context.author.roles]
    print(roles)

    for x in range(0, len(perm)):
        if roles.__contains__(perm[x]):
            return True

    return False


class Commands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def prefix(self, ctx, *args):
        database = await Database.connect()

        if not args:
            await ctx.send(f"O prefixo para esse servidor é `{await database.prefix.get(ctx.guild)}`")
        else:
            prefix = " ".join(args)

            await database.prefix.update(ctx.guild, prefix)
            await ctx.send("O prefixo do servidor mudou!\n"
                          f"Utilize qualquer comando agora com o prefixo:  `{prefix}`")


    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(self.client.latency * 1000)}ms {ctx.author.mention}')

def setup(client):
    client.add_cog(Commands(client))
