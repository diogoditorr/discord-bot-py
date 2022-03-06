import re
import sys
import traceback
from typing import List

import discord
from discord.ext import commands, menus
from discord.ext.commands import Context

from ..modules.menu import TracebackPaginatorSource


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
        if hasattr(error, 'original'):
            content = "".join(traceback.format_exception(type(error.original), error.original, error.original.__traceback__))
        else:
            content = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        entries = [content[i:i + 1990] for i in range(0, len(content), 1990)]
        source = TracebackPaginatorSource(entries=entries)
        paginator = menus.MenuPages(
            source=source, timeout=120, delete_message_after=True)

        await paginator.start(ctx)
       

def setup(client):
    client.add_cog(Events(client))
