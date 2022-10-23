from __future__ import annotations

import os
import random
import re
import typing
from pathlib import Path
from typing import (TYPE_CHECKING, Dict, Iterator, List, Literal, Optional,
                    Tuple, Union)

import discord
import lavalink
import yaml
from discord import Interaction, app_commands
from discord.app_commands import AppCommandError, Command
from discord.ext import commands, menus
from discord.ext.commands import Context
from discord.utils import get
from jishaku import Jishaku
from lavalink import Client as LavalinkClient

from ..database.exceptions import PlayerPermissionError
from ..modules.constants import LAVALINK_SERVER_CONFIG
from ..modules.decorators import has_dj_permission, has_user_permission
from ..modules.handler import Query, QueryTransformer, Result
from ..modules.menu import QueuePaginatorSource

if TYPE_CHECKING:
    from packages.bot_client import BotClient


class Player(lavalink.DefaultPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_queue: list | None = None
        self.repeat_mode: Literal['off', 'single', 'all'] = 'off'

    def is_shuffled(self) -> bool:
        return self.original_queue is not None

    def shuffle(self):
        if self.queue is None:
            return

        if not self.is_shuffled():
            self.original_queue = self.queue
            self.queue = random.sample(self.queue, len(self.queue))
        else:
            self.queue = self.original_queue
            self.original_queue = None


class LavalinkVoiceClient(discord.VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """
    lavalink: LavalinkClient

    def __init__(self, client: BotClient, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(
                user_id=client.user.id,
                player=Player
            )
            self.client.lavalink.add_node(
                host=LAVALINK_SERVER_CONFIG['server']['address'],
                port=LAVALINK_SERVER_CONFIG['server']['port'],
                password=LAVALINK_SERVER_CONFIG['lavalink']['server']['password'],
                region='brazil',
                name='default-node')
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(
            guild_id=self.channel.guild.id,
            region='brazil',
        )
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player: Player | None = self.lavalink.player_manager.get(
            self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the
        # disconnect
        player.channel_id = None
        self.cleanup()


class MusicCommands(app_commands.Group):
    DEFAULT_VOLUME = 15

    def __init__(self, client: BotClient):
        super().__init__(
            name='music',
            description='Music related commands.',
        )
        self.client = client

        lavalink.add_event_hook(self.track_hook)

    def create_lavalink_node(self):
        if not hasattr(self.client, 'lavalink'):
            self.client.lavalink = lavalink.Client(
                user_id=self.client.user.id,
                player=Player
            )
            self.client.lavalink.add_node(
                host=LAVALINK_SERVER_CONFIG['server']['address'],
                port=LAVALINK_SERVER_CONFIG['server']['port'],
                password=LAVALINK_SERVER_CONFIG['lavalink']['server']['password'],
                region='brazil',
                name='default-node'
            )

    async def track_hook(self, event):
        # Declare event.player as a Player object
        if isinstance(event, lavalink.TrackEndEvent):
            player: Player = event.player

            if player.repeat_mode == 'single' and event.reason == 'FINISHED':
                player.add(
                    track=player.current,
                    requester=player.current.requester,
                    index=0
                )

                if player.is_shuffled():
                    player.original_queue.insert(0, player.current)

            if player.repeat and player.is_shuffled():
                player.original_queue.append(player.current)

        if isinstance(event, lavalink.TrackStartEvent):
            player: Player = event.player

            if player.is_shuffled():
                player.original_queue = self._remove_queue_track(
                    player.original_queue, event.track)

            try:
                await player.fetch('playing_now_message').delete()
            except Exception:
                pass

            channel_text = player.fetch('channel')
            guild = get(self.client.guilds, id=int(player.guild_id))

            if channel_text and guild:
                embed = self._build_playing_now(
                    guild, event.track)
                playing_now_message = await channel_text.send(embed=embed)

                player.store('playing_now_message', playing_now_message)

        if isinstance(event, lavalink.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            guild_id = int(event.player.guild_id)
            guild = self.client.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)

    async def ensure_voice(self, interaction: Interaction):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        def user_not_connected(interaction: Interaction):
            return not user_voice or not user_voice.channel

        def is_user_in_different_channel(interaction: Interaction, player: Player) -> bool:
            return int(player.channel_id) != user_voice.channel.id

        def check_channel_permissions(interaction: Interaction):
            permissions = user_voice.channel.permissions_for(
                interaction.guild.me)
            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError(
                    'I need the `CONNECT` and `SPEAK` permissions.')

        async def connect_to_user_voice_channel(interaction: Interaction, player: Player):
            if user_not_connected(interaction):
                raise commands.CommandInvokeError('Join a voicechannel first.')

            check_channel_permissions(interaction)

            player.store('channel', interaction.channel)
            await user_voice.channel.connect(cls=LavalinkVoiceClient)

        user_voice = interaction.user.voice

        if (player := self._get_player(interaction)) is None:
            lavalink: LavalinkClient = self.client.lavalink
            player: Player = lavalink.player_manager.create(
                interaction.guild.id, region='brazil'
            )
            await player.set_volume(MusicCommands.DEFAULT_VOLUME)

        bot_should_be_connected_command = interaction.command.name in ('queue', 'pause', 'resume', 'repeat',
                                                                       'shuffle', 'next', 'skip', 'volume', 'stop')
        bot_should_connect_command = interaction.command.name in (
            'play', 'playnext')
        same_channel_command = not interaction.command.name in ('queue',)
        is_a_connection_command = interaction.command.name == 'join'

        if is_a_connection_command:
            if user_not_connected(interaction):
                raise commands.CommandInvokeError('Join a voicechannel first.')

            check_channel_permissions(interaction)

        if player.is_connected:
            if bot_should_be_connected_command and not same_channel_command:
                # queue
                pass

            elif bot_should_be_connected_command and \
                    is_user_in_different_channel(interaction, player) and \
                    same_channel_command:
                raise commands.CommandInvokeError(
                    'You need to be in my voicechannel.')

            elif bot_should_connect_command and is_user_in_different_channel(interaction, player):
                await connect_to_user_voice_channel(interaction, player)

        else:
            if bot_should_connect_command:
                await connect_to_user_voice_channel(interaction, player)

            elif not is_a_connection_command:
                raise commands.CommandInvokeError('Not connected.')

        # Connect to the channel and execute command (play, playnext)
        # Execute command without entering the same channel and must not be connected (join, leave)
        # Except: Execute command that must be in the same channel (pause, resume, repeat, shuffle, etc...)
        # Execute command without entering the same channel but must be connected (queue)

    @app_commands.command()
    @has_user_permission()
    async def play(
        self,
        interaction: Interaction,
        *, search: app_commands.Transform[Query, QueryTransformer]
    ):
        await self.ensure_voice(interaction)
        player = self._get_player(interaction)

        if not (result := await self._search_tracks(search.query, player)):
            return await interaction.response.send_message('Desculpe, mas não achei nenhum resultado. Tente novamente.')

        tracks, embed = await Result.parse(interaction, search, result)

        if tracks:
            self._add_tracks(interaction, tracks, player)

            await interaction.response.send_message(embed=embed)

            if not player.is_playing:
                await player.play()

    @app_commands.command()
    @has_user_permission()
    async def playnext(
        self,
        interaction: Interaction,
        *, search: app_commands.Transform[Query, QueryTransformer]
    ):
        await self.ensure_voice(interaction)
        player = self._get_player(interaction)

        if not (result := await self._search_tracks(search.query, player)):
            return await interaction.response.send_message('Desculpe, mas não achei nenhum resultado. Tente novamente.')

        tracks, embed = await Result.parse(interaction, search, result, queue_first=True)

        if tracks:
            self._add_tracks(interaction, tracks, player, start_at=0)

            await interaction.response.send_message(embed=embed)

            if not player.is_playing:
                await player.play()

    @app_commands.command(name='queue')
    @has_user_permission()
    async def _queue(self, interaction: Interaction, page: int = 1):
        player = self._get_player(interaction)

        if not player.is_connected:
            return

        if not player.queue:
            return

        if not player.current:
            return await interaction.response.send_message("Nenhuma música está sendo tocada.")

        entries = player.queue
        source = QueuePaginatorSource(entries=entries, player=player)
        paginator = menus.MenuPages(
            source=source, timeout=120, delete_message_after=True)

        await paginator.start(interaction)

    @app_commands.command()
    @has_dj_permission()
    async def pause(self, interaction: Interaction):
        player = self._get_player(interaction)

        if player.paused:
            await interaction.response.send_message("O player já está pausado.")
        else:
            await player.set_pause(True)
            await interaction.response.send_message("A música foi pausada. Para voltar, utilize `.resume`")

    @app_commands.command()
    @has_dj_permission()
    async def resume(self, interaction: Interaction):
        player = self._get_player(interaction)

        if not player.paused:
            await interaction.response.send_message("O player já está tocando.")
        else:
            await player.set_pause(False)
            await interaction.response.send_message("Voltando a tocar...")

    @app_commands.command()
    @has_dj_permission()
    async def repeat(self, interaction: Interaction, repeat_mode: Literal['single', 'all', 'off']):
        player = self._get_player(interaction)

        if repeat_mode == 'single':
            player.repeat = False  # Do not append the current song to the queue
            player.repeat_mode = 'single'
            await interaction.response.send_message('Repetindo a faixa atual.')

        elif repeat_mode == 'all':
            player.repeat = True
            player.repeat_mode = 'all'
            await interaction.response.send_message('Repetindo todas as faixas.')

        elif repeat_mode == 'off':
            player.repeat = False
            player.repeat_mode = 'off'
            await interaction.response.send_message('Desligando repetição.')

        else:
            await interaction.response.send_message(f'Use `single | all | off` para ativar/desativar a repetição.')

    @app_commands.command()
    @has_dj_permission()
    async def shuffle(self, interaction: Interaction):
        player = self._get_player(interaction)

        if not player.queue:
            return await interaction.response.send_message("Não há nenhuma música para embaralhar.")

        if player.is_shuffled():
            player.queue = player.original_queue
            delattr(player, 'original_queue')
            await interaction.response.send_message("O reprodutor não está mais em modo aleatório.")

        else:
            player.original_queue = player.queue
            player.queue = random.sample(player.queue, len(player.queue))
            await interaction.response.send_message("O reprodutor agora está em modo aleatório.")

    @app_commands.command(name='next')
    @has_user_permission()
    async def _next(self, interaction: Interaction):
        player = self._get_player(interaction)

        if not player.is_connected:
            return await interaction.response.send_message("Não estou conectado.")

        if interaction.user.voice is None or \
                (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
            return await interaction.response.send_message("Você não está no mesmo canal de voz que eu!")

        if not player.queue and not player.current:
            return await interaction.response.send_message("Não há nenhuma música na fila.")

        await interaction.response.send_message("Tocando próxima música...")
        await player.skip()

    @app_commands.command()
    @has_dj_permission()
    async def volume(self, interaction: Interaction, volume: Optional[int]):
        # TODO: 'volume' shows the volume. 'volume <volume_number>' set volume (only with DJ permission)
        await self.ensure_voice(interaction)
        player = self._get_player(interaction)

        if volume:
            volume = max(min(volume, 1000), 0)
            await player.set_volume(volume)

            await interaction.response.send_message(f"O volume foi do player alterado para `{volume}`")
        else:
            await interaction.response.send_message(f"O volume atual é `{player.volume}`")

    @app_commands.command()
    @has_dj_permission()
    async def stop(self, interaction: Interaction):
        await self.ensure_voice(interaction)
        player = self._get_player(interaction)

        if player.is_connected:
            player.queue.clear()
            await player.stop()
            await interaction.guild.voice_client.disconnect(force=True)

        await interaction.response.send_message("O player parou.")

    @app_commands.command()
    @has_user_permission()
    async def join(self, interaction: Interaction):
        await self.ensure_voice(interaction)

        player = self._get_player(interaction)
        user_channel = interaction.user.voice.channel

        if not user_channel:
            await interaction.response.send_message("Você não está conectado a nenhum canal.")
            return

        if not player.is_connected:
            await user_channel.connect(cls=LavalinkVoiceClient)
            await interaction.response.send_message(f"Conectado ao canal `{user_channel.name}`")
            player.store('channel', interaction.channel)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Já estou conectado a um canal.")
            return

        if interaction.guild.voice_client.channel.id == user_channel.id:
            await interaction.response.send_message("Já estou conectado a este canal.")
            return

        await interaction.guild.voice_client.disconnect(force=True)
        await user_channel.connect(cls=LavalinkVoiceClient)
        player.store('channel', interaction.channel)
        await interaction.response.send_message(f"Conectado ao canal `{user_channel.name}`")

    @app_commands.command()
    @has_user_permission()
    async def leave(self, interaction: Interaction):
        """ Disconnects the player from the voice channel and clears its queue. """
        user_voice = interaction.user.voice
        player = self._get_player(interaction)

        if not player.is_connected:
            return await interaction.response.send_message("Não estou conectado.")

        if not interaction.user.guild_permissions.administrator and (
            user_voice is None or
            (player.is_connected and user_voice.channel.id != int(player.channel_id))
        ):
            return await interaction.response.send_message("Você não está no mesmo canal de voz que eu!")

        player.queue.clear()
        await player.stop()

        await interaction.guild.voice_client.disconnect(force=True)
        if user_voice:
            await interaction.response.send_message(f"Desconectado do canal `{user_voice.channel.name}`")

    def _get_player(self, interaction: Interaction) -> Player:
        return self.client.lavalink.player_manager.get(interaction.guild.id)
        

    async def _search_tracks(self, query: str, player: Player):
        result = await player.node.get_tracks(query)

        if not result or not result['tracks']:
            return None

        return result

    def _add_tracks(self, interaction: Interaction, tracks: list, player: Player, start_at: int = None):
        if len(tracks) > 1 and start_at is not None:
            tracks = reversed(tracks)

        for track in tracks:
            track = lavalink.AudioTrack(
                track, requester=interaction.user.id, requester_name=interaction.user.name)

            player.add(
                requester=interaction.user.id,
                track=track,
                index=start_at,
            )

            if player.is_shuffled():
                if start_at is not None:
                    player.original_queue.insert(start_at, track)
                else:
                    player.original_queue.append(track)

    def _build_playing_now(self, guild: discord.Guild, track: lavalink.AudioTrack):
        embed = discord.Embed(color=guild.me.top_role.color, title="**Playing Now**",
                              description=f"[{track.title}]({track.uri})  [<@{track.requester}>]")

        return embed

    def _remove_queue_track(self, queue: list, track: lavalink.AudioTrack):
        matched_track = get(queue, title=track.title)
        if matched_track:
            queue.remove(matched_track)
        return queue

    async def on_error(
        self,
        interaction: Interaction,
        command: Command,
        error: AppCommandError
    ):
        if isinstance(error, PlayerPermissionError):
            await interaction.response.send_message(f"Você precisa ter a permissão de **{error.permission}** para isso.\n"
                                                    f"Veja a lista utilizando `/{error.permission.lower()} list`")

        elif isinstance(error, commands.CommandInvokeError):
            await interaction.response.send_message(error.original)
            raise error

        else:
            await interaction.response.send_message(error)
            raise error
