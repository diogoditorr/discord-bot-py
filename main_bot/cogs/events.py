import discord
import sys
from discord.ext import commands
from cogs.tasks import Tasks


class Events(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot is ready')
        game = discord.Game("Made by: Diego")
        await self.client.change_presence(status=discord.Status.online, activity=game)
        Tasks.change_status.start(self)

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
