import discord
from discord.ext import commands, menus

class PaginatorSource(menus.ListPageSource):

    def __init__(self, entries, player, per_page=10):
        super().__init__(entries, per_page=per_page)
        self.player = player

    async def format_page(self, menu: menus.Menu, page):
        msg = ''

        if self.player.is_shuffled():
            msg += 'Mostrando playlist embaralhada\n'

        repeat_single = self.player.fetch('repeat_single')
        if not repeat_single and not self.player.repeat:
            msg += '\n'
        elif repeat_single and not self.player.repeat:
            msg += 'Repetindo a faixa atual\n\n'
        elif self.player.repeat:
            msg += 'Repetindo a fila atual\n\n'

        msg += f'Página **{menu.current_page+1}** de **{self._max_pages}**\n\n'

        if menu.current_page == 0:
            if self.player.paused:
                msg += f'**⏸ {self.player.current.title}** - *[@{self.player.current.extra["requester_name"]}]*\n'
            else:
                msg += f'**▶ {self.player.current.title}** - *[@{self.player.current.extra["requester_name"]}]*\n'

        index = self.per_page * menu.current_page
        for track in page:
            index = index + 1
            msg = msg + f'`[{index}]` **{track.title}** - *[@{track.extra["requester_name"]}]*\n'
        
        return msg

    def is_paginating(self):
        return True