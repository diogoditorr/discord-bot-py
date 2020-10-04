import sys

import discord
from discord.ext import commands


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f'{member} has joined a server.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f'{member} has left a server.')

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.content.startswith('a'):
            print("O usuário pediu algum comando")
            print(sys.path)
        else:
            # print(msg.content)
            pass


def setup(client):
    client.add_cog(Events(client))
