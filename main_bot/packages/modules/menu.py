from typing import Union
import discord
from discord.ext import commands, menus
from lavalink import DefaultPlayer

from .utils import convert_duration


class QueuePaginatorSource(menus.ListPageSource):

    def __init__(self, entries: list, player: DefaultPlayer, per_page=10):
        super().__init__(entries, per_page=per_page)
        self.player = player

    async def format_page(self, menu: menus.MenuPages, page: list) -> str:
        msg = ''
        max_pages = "1" if self.get_max_pages() == 0 else self.get_max_pages()

        if self.player.is_shuffled():
            msg += 'Mostrando playlist embaralhada\n'

        repeat_single = self.player.fetch('repeat_single')
        if not repeat_single and not self.player.repeat:
            msg += '\n'
        elif repeat_single and not self.player.repeat:
            msg += 'Repetindo a faixa atual\n\n'
        elif self.player.repeat:
            msg += 'Repetindo a fila atual\n\n'

        msg += f'Página **{menu.current_page+1}** de **{max_pages}**\n\n'

        if menu.current_page == 0:
            if self.player.paused:
                msg += f'**⏸ {self.player.current.title}** - *[@{self.player.current.extra["requester_name"]}]*\n'
            else:
                msg += f'**▶ {self.player.current.title}** - *[@{self.player.current.extra["requester_name"]}]*\n'

        index = self.per_page * menu.current_page
        for track in page:
            index += 1
            msg = msg + f'`[{index}]` **{track.title}** - *[@{track.extra["requester_name"]}]*\n'
        
        return msg

    def is_paginating(self):
        return True


class SelectSong(menus.Menu):
    def __init__(self, tracks):
        super().__init__(timeout=30.0, delete_message_after=True)
        self.tracks = tracks
        self.result = None

    async def send_initial_message(self, ctx, channel):
        msg = '**_Selecione uma faixa clicando no emoji correspondente._**\n'
    
        for index in range(0, 5):
            track = self.tracks[index]['info']
            msg = msg + f"**{(index + 1)})** {track['title']} **- ({convert_duration(track['length'])})**\n"
        
        return await channel.send(msg)
        
    @menus.button('1️⃣')
    async def first(self, payload):
        self.result = self.tracks[0]
        self.stop()

    @menus.button('2️⃣')
    async def second(self, payload):
        self.result = self.tracks[1]
        self.stop()

    @menus.button('3️⃣')
    async def third(self, payload):
        self.result = self.tracks[2]
        self.stop()

    @menus.button('4️⃣')
    async def fourth(self, payload):
        self.result = self.tracks[3]
        self.stop()

    @menus.button('5️⃣')
    async def fifth(self, payload):
        self.result = self.tracks[4]
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result

class TracebackPaginatorSource(menus.ListPageSource):
    def __init__(self, entries: list, per_page=1):
        super().__init__(entries=entries, per_page=per_page)

    async def format_page(self, menu: menus.MenuPages, page: Union[list, str]) -> str:
        return f'```py\n{page}```'

    def is_paginating(self):
        return True