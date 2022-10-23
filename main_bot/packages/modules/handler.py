import re
from typing import List, Tuple, Union

import discord
from discord import app_commands
from discord import Embed, Interaction
from discord.ext.commands import Context
from packages.modules.menu import SelectSong


class Query:
    _URL_RX = re.compile(r'https?://(?:www\.)?.+')

    def __init__(self, content, youtube_mode=True):

        arguments = content.split()
        if arguments[0] == '-f':
            self.first_song = True
            self.query = " ".join(arguments[1:])
        else:
            self.first_song = False
            self.query = " ".join(arguments)

        self.query = self.query.strip('<>')

        if Query._URL_RX.match(self.query):
            self.first_song = True
        else:
            if youtube_mode:
                self.query = f'ytsearch:{self.query}'

    def __repr__(self):
        return '<Query content="{}">'.format(self.query)


class QueryTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: Interaction, value: str) -> Query:
        return Query(value)


class Result():

    def __init__(self, interaction: Interaction, query: Query, data: dict, queue_first=False):
        self.interaction = interaction
        self.query = query

        self.load_type = data['loadType']
        self.playlist_info = data['playlistInfo']
        self.tracks = data['tracks']

        self.queue_first = queue_first

    @classmethod
    async def parse(
        cls,
        interaction: Interaction,
        query: Query,
        data: dict,
        queue_first=False
    ) -> Tuple[List[dict], Union[Embed, None]]:
        obj = cls(interaction, query, data, queue_first)

        tracks = await obj.get_tracks()
        embed = obj.get_embed(tracks)

        return (tracks, embed)

    async def get_tracks(self):
        tracks: List[dict] = list()

        if self.load_type == 'SEARCH_RESULT':
            if self.query.first_song:
                track = self.tracks[0]
                tracks.append(track)

            else:
                if (track := await self.get_selected_track()):
                    tracks.append(track)
                else:
                    await self.interaction.response.send_message("Nenhuma música foi selecionada!", delete_after=3)

        elif self.load_type == 'TRACK_LOADED':
            track = self.tracks[0]
            tracks.append(track)

        elif self.load_type == 'PLAYLIST_LOADED':
            for track in self.tracks:
                tracks.append(track)

        return tracks

    def get_embed(self, tracks: list):
        embed: Union[discord.Embed, None] = None

        if self.load_type == 'SEARCH_RESULT':
            embed = self._build_queued_message(tracks[0])

        elif self.load_type == 'TRACK_LOADED':
            embed = self._build_queued_message(tracks[0])

        elif self.load_type == 'PLAYLIST_LOADED':
            embed = self._build_queued_playlist_message(tracks)

        return embed

    async def get_selected_track(self):
        return await SelectSong(self.tracks).prompt(self.interaction)

    def _build_queued_message(self, track: dict) -> discord.Embed:
        return discord.Embed(
            color=self.interaction.guild.me.top_role.color,
            description=f"{'Queued First' if self.queue_first else 'Queued'}: "
                        f"[{track['info']['title']}]({track['info']['uri']})  "
                        f"[{self.interaction.user.mention}]"
        )

    def _build_queued_playlist_message(self, tracks) -> discord.Embed:
        return discord.Embed(
            color=self.interaction.guild.me.top_role.color,
            description=f"{'Queued First' if self.queue_first else 'Queued'}: "
                        f"`{len(tracks)}` músicas da playlist **{self.playlist_info['name']}**.  "
                        f"[{self.interaction.user.mention}]"
        )
