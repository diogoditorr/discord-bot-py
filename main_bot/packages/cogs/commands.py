import sys
import traceback

from discord import Interaction, Member, Message, app_commands
from discord.ext import menus

from ..modules.menu import TracebackPaginatorSource


class Commands(app_commands.Group):
    @app_commands.command()
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message(f'Pong! {round(interaction.client.latency * 1000)}ms {interaction.user.mention}')

    async def on_error(
        self, interaction: Interaction,
        command: app_commands.Command,
        error: app_commands.AppCommandError
    ):
        a = sys.exc_info()
        if hasattr(error, 'original'):
            content = "".join(traceback.format_exception(
                type(error.original), error.original, error.original.__traceback__))
        else:
            content = "".join(traceback.format_exception(
                type(error), error, error.__traceback__))

        entries = [content[i:i + 1990] for i in range(0, len(content), 1990)]
        source = TracebackPaginatorSource(entries=entries)
        paginator = menus.MenuPages(
            source=source, timeout=120, delete_message_after=True)

        await paginator.start(interaction)
