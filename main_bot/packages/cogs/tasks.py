import discord
from discord.ext import commands, tasks
from itertools import cycle

status = cycle(['Made by: Diego', '.help For Information'])


class Tasks(commands.Cog):

    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=10)
    async def change_status(self):
        await self.client.change_presence(activity=discord.Game(next(status)))


def setup(client):
    client.add_cog(Tasks(client))