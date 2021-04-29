import sys
import re
import traceback
from typing import List

import discord
from discord.ext import commands
from discord.ext.commands import Context


class Events(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f'{member} has joined a server.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f'{member} has left a server.')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.content.startswith('a'):
            print("O usuário pediu algum comando")
            print(sys.path)
        elif re.match(r'^<@(!?)({})>$'.format(self.client.user.id), msg.content) is not None:
            # print(msg.content)
            ctx = await self.client.get_context(msg)
            cmd = self.client.get_command("prefix")
            await cmd(ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error):
        a = sys.exc_info()
        content = "".join(traceback.format_exception(type(error.original), error.original, error.original.__traceback__)) if \
            hasattr(error, 'original') else "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await ctx.send(f"""```py\n{content}```""")
       

def setup(client):
    client.add_cog(Events(client))
