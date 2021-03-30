import sys
import re

import discord
from discord.ext import commands


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
       


def setup(client):
    client.add_cog(Events(client))
