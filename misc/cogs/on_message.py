import discord
from discord.ext import commands


class OnMessage(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.id == self.client.user.id:
            return

        print(f'Usuário {msg.author}: "{msg.content}"')


# Function to initialize the class
def setup(client):
    client.add_cog(OnMessage(client))
