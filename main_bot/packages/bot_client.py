import re
import sys

import discord
from discord import Interaction, Member, Message, app_commands
from discord.ext import commands, menus
from lavalink import Client as LavalinkClient

from .cogs.commands import Commands
from .cogs.music import MusicCommands
from .cogs.permission import PermissionCommands
from .cogs.tasks import Tasks
from .database.database import Database


class BotClient(discord.Client):
    TEST_GUILD = discord.Object(690604622045511700)
    lavalink: LavalinkClient

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
    
        self.setup_tree_commands()
        self.tree.copy_global_to(guild=self.TEST_GUILD)

    def setup_tree_commands(self):
        self.music_commands = MusicCommands(self)

        self.tree.add_command(Commands())
        self.tree.add_command(PermissionCommands())
        self.tree.add_command(self.music_commands)

        @self.tree.command()
        async def shutdown(interaction: Interaction):
            if interaction.user.id != interaction.guild.owner.id:
                return

            print("shutdown")

            try:
                await self.close()
            except:
                print("EnvironmentError")
                self.clear()
            else:
                await interaction.response.send_message("You do not own this bot!")

        @self.tree.context_menu()
        async def react(interaction: Interaction, message: Message):
            await interaction.response.send_message('Very cool message!', ephemeral=True)

        @self.tree.context_menu()
        async def ban(interaction: Interaction, user: Member):
            await interaction.response.send_message(f'Should I actually ban {user}...', ephemeral=True)

    async def on_ready(self):
        print(f'Bot {self.user} is ready (ID: {self.user.id})')
        print(10 * '-')

        self.music_commands.create_lavalink_node()

        await self.change_presence(
            status=discord.Status.online, 
            activity=discord.Game("Made by: Diego")
        )

        # Tasks.change_status.start()

        await self.tree.sync(guild=self.TEST_GUILD)
        await Database.create()

    async def on_member_join(self, member: Member):
        print(f'{member} has joined a server.')

    async def on_member_remove(self, member: Member):
        print(f'{member} has left a server.')

    async def on_message(self, msg: discord.Message):
        if msg.content.startswith('a'):
            print("O usuário pediu algum comando")
            print(sys.path)
        elif re.match(r'^<@(!?)({})>$'.format(self.user.id), msg.content) is not None:
            print(msg.content)
