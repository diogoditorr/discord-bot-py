import re
import random
from typing import Dict, Iterator, Optional, Union, Tuple, List
import typing

import discord
from discord.ext import commands, menus
from discord.ext.commands import Context
from discord.utils import get
from jishaku import Jishaku, JishakuBase
import lavalink

from ..modules.menu import QueuePaginatorSource, SelectSong
from ..modules.decorators import (has_dj_permission, has_user_permission)
from ..modules.handler import Query, Result
from ..database.exceptions import PlayerPermissionError


URL_RX = re.compile(r'https?://(?:www\.)?.+')


def is_shuffled(player: lavalink.DefaultPlayer) -> bool:
    return hasattr(player, 'original_queue')


class MusicCommands(commands.Cog):
    DEFAULT_VOLUME = 15

    def __init__(self, client: commands.Bot):
        self.client = client

        if not hasattr(self, 'lavalink'):
            self.lavalink = lavalink.Client(self.client.user.id)
            self.lavalink.add_node(
                host='localhost',
                port=3434,
                password='testing',
                region='brazil',
                name='default-node'
            )
            self.client.add_listener(
                self.lavalink.voice_update_handler, 'on_socket_response')

            # Add an instance method in lavalink.DefaultPlayer class
            lavalink.DefaultPlayer.is_shuffled = is_shuffled

        self.lavalink.add_event_hook(self.track_hook)

    async def track_hook(self, event: lavalink.Event):
        if isinstance(event, lavalink.TrackEndEvent):
            repeat_single = event.player.fetch('repeat_single')

            if repeat_single and event.reason == 'FINISHED':
                event.player.add(
                    track=event.player.current,
                    requester=event.player.current.requester,
                    index=0
                )

                if event.player.is_shuffled():
                    event.player.original_queue.insert(0, event.player.current)

            if event.player.repeat and event.player.is_shuffled():
                event.player.original_queue.append(event.player.current)

        if isinstance(event, lavalink.TrackStartEvent):
            if event.player.is_shuffled():
                event.player.original_queue = self._remove_queue_track(
                    event.player.original_queue, event.track)

            try:
                await event.player.fetch('playing_now_message').delete()
            except Exception:
                pass

            channel_text = event.player.fetch('channel')
            guild = get(self.client.guilds, id=int(event.player.guild_id))

            if channel_text and guild:
                embed = self._build_playing_now(
                    guild, event.track)
                playing_now_message = await channel_text.send(embed=embed)

                event.player.store('playing_now_message', playing_now_message)

        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)

    async def connect_to(self, guild_id: int, channel_id: Union[str, None]):
        """ Connects to the given voicechannel ID. A channel_id of `None` means disconnect. """
        websocket = self.client._connection._get_websocket(guild_id)
        await websocket.voice_state(str(guild_id), channel_id)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.lavalink._event_hooks.clear()

    # Local error_handler() will be executed instead
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        ctx.author = await ctx.guild.fetch_member(ctx.author.id) or ctx.author

        if guild_check:
            await self._ensure_voice(ctx)

        return guild_check

    async def _ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """

        def author_not_connected(ctx):
            return not ctx.author.voice or not ctx.author.voice.channel

        def is_author_in_different_channel(ctx, player) -> bool:
            return int(player.channel_id) != ctx.author.voice.channel.id

        def check_channel_permissions(ctx):
            permissions = ctx.author.voice.channel.permissions_for(ctx.me)
            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError(
                    'I need the `CONNECT` and `SPEAK` permissions.')

        async def connect_to_user_voice_channel(ctx, player):
            if author_not_connected(ctx):
                raise commands.CommandInvokeError('Join a voicechannel first.')

            check_channel_permissions(ctx)

            player.store('channel', ctx.channel)
            await self.connect_to(ctx.guild.id, ctx.author.voice.channel.id)

        if (player := self._get_player(ctx)) is None:
            player: lavalink.DefaultPlayer = self.lavalink.player_manager.create(
                ctx.guild.id, endpoint=str(ctx.guild.region))
            await player.set_volume(MusicCommands.DEFAULT_VOLUME)

        bot_should_be_connected_command = ctx.command.name in ('queue', 'pause', 'resume', 'repeat',
                                                               'shuffle', 'next', 'skip', 'volume', 'stop')
        bot_should_connect_command = ctx.command.name in ('play', 'playnext')
        same_channel_command = not ctx.command.name in ('queue',)
        is_a_connection_command = ctx.command.name == 'join'

        if is_a_connection_command:
            if author_not_connected(ctx):
                raise commands.CommandInvokeError('Join a voicechannel first.')

            check_channel_permissions(ctx)

        if player.is_connected:
            if bot_should_be_connected_command and not same_channel_command:
                # queue
                pass

            elif bot_should_be_connected_command and is_author_in_different_channel(ctx, player) \
                    and same_channel_command:
                raise commands.CommandInvokeError(
                    'You need to be in my voicechannel.')

            elif bot_should_connect_command:
                await connect_to_user_voice_channel(ctx, player)

        else:
            if bot_should_connect_command:
                await connect_to_user_voice_channel(ctx, player)

            elif not is_a_connection_command:
                raise commands.CommandInvokeError('Not connected.')

        # Connect to the channel and execute command (play, playnext)
        # Execute command without entering the same channel and must not be connected (join, leave)
        # Except: Execute command that must be in the same channel (pause, resume, repeat, shuffle, etc...)
        # Execute command without entering the same channel but must be connected (queue)

    @commands.command(aliases=['p'])
    @has_user_permission()
    async def play(self, ctx, *, search: Query):
        player = self._get_player(ctx)

        if not (result := await self._search_tracks(search.query, player)):
            return await ctx.send('Desculpe, mas não achei nenhum resultado. Tente novamente.')

        tracks, embed = await Result.parse(ctx, search, result)

        if tracks:
            self._add_tracks(ctx, tracks, player)

            await ctx.send(embed=embed)

            if not player.is_playing:
                await player.play()

    @commands.command()
    @has_user_permission()
    async def playnext(self, ctx, *, search: Query):
        player = self._get_player(ctx)

        if not (result := await self._search_tracks(search.query, player)):
            return await ctx.send('Desculpe, mas não achei nenhum resultado. Tente novamente.')

        tracks, embed = await Result.parse(ctx, search, result, queue_first=True)

        # tracks = await result_query.get_tracks()
        # embed = result_query.get_embed(tracks)

        # tracks, embed = await self._convert_result(ctx, search, result, queue_first=True)

        if tracks:
            self._add_tracks(ctx, tracks, player, start_at=0)

            await ctx.send(embed=embed)

            if not player.is_playing:
                await player.play()

    @commands.command(name='queue', aliases=['q'])
    @has_user_permission()
    async def _queue(self, ctx, page=1):
        player = self._get_player(ctx)

        if not player.is_connected:
            return

        if not player.queue and not player.current:
            return await ctx.send("Nenhuma música está sendo tocada.")

        entries = player.queue

        pages = QueuePaginatorSource(entries=entries, player=player)
        paginator = menus.MenuPages(
            source=pages, timeout=120, delete_message_after=True)

        await paginator.start(ctx)

    @commands.command()
    @has_dj_permission()
    async def pause(self, ctx):
        player = self._get_player(ctx)

        if player.paused:
            await ctx.send("O player já está pausado.")
        else:
            await player.set_pause(True)
            await ctx.send("A música foi pausada. Para voltar, utilize `.resume`")

    @commands.command(aliases=['unpause'])
    @has_dj_permission()
    async def resume(self, ctx):
        player = self._get_player(ctx)

        if not player.paused:
            await ctx.send("O player já está tocando.")
        else:
            await player.set_pause(False)
            await ctx.send("Voltando a tocar...")

    @commands.command()
    @has_dj_permission()
    async def repeat(self, ctx, repeat_mode):
        player = self._get_player(ctx)

        if repeat_mode == 'single':
            player.repeat = False  # Do not append the current song to the queue
            player.store('repeat_single', 'True')
            await ctx.send('Repetindo a faixa atual.')

        elif repeat_mode == 'all':
            player.repeat = True
            player.delete('repeat_single')
            await ctx.send('Repetindo todas as faixas.')

        elif repeat_mode == 'off':
            player.repeat = False
            player.delete('repeat_single')
            await ctx.send('Desligando repetição.')

        else:
            await ctx.send(f'Use `{await self.client.get_prefix(ctx)}single | all | off` para ativar/desativar a repetição.')

    @commands.command()
    @has_dj_permission()
    async def shuffle(self, ctx):
        player = self._get_player(ctx)

        if not player.queue:
            return await ctx.send("Não há nenhuma música para embaralhar.")

        if player.is_shuffled():
            player.queue = player.original_queue
            delattr(player, 'original_queue')
            await ctx.send("O reprodutor não está mais em modo aleatório.")

        else:
            player.original_queue = player.queue
            player.queue = random.sample(player.queue, len(player.queue))
            await ctx.send("O reprodutor agora está em modo aleatório.")

    @commands.command(name='next')
    @has_user_permission()
    async def _next(self, ctx):
        player = self._get_player(ctx)

        if not player.is_connected:
            return await ctx.send("Não estou conectado.")

        if ctx.author.voice is None or \
                (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send("Você não está no mesmo canal de voz que eu!")

        if not player.queue and not player.current:
            return await ctx.send("Não há nenhuma música na fila.")

        await ctx.send("Tocando próxima música...", delete_after=3)
        await player.skip()

    @commands.command()
    @has_dj_permission()
    async def volume(self, ctx, volume: Optional[int]):
        # TODO: 'volume' shows the volume. 'volume <volume_number>' set volume (only with DJ permission)
        player = self._get_player(ctx)

        if volume:
            volume = max(min(volume, 1000), 0)
            await player.set_volume(volume)

            await ctx.send(f"O volume foi do player alterado para `{volume}`")
        else:
            await ctx.send(f"O volume atual é `{player.volume}`")

    @commands.command()
    @has_dj_permission()
    async def stop(self, ctx):
        player = self._get_player(ctx)

        if player.is_connected:
            player.queue.clear()
            await player.stop()
            await self.connect_to(ctx.guild.id, None)

        await ctx.send("O player parou.")

    @commands.command(aliases=['connect'])
    @has_user_permission()
    async def join(self, ctx):
        player = self._get_player(ctx)
        user_channel = ctx.message.author.voice.channel.id

        if user_channel:
            await self.connect_to(ctx.guild.id, user_channel)
            await ctx.send(f"Conectado ao canal `{ctx.author.voice.channel.name}`")
            player.store('channel', ctx.channel)
        else:
            await ctx.send("Você não está conectado a nenhum canal.")

    @commands.command(aliases=['disconnect'])
    @has_user_permission()
    async def leave(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        channel = ctx.message.author.voice.channel
        player = self._get_player(ctx)

        if not player.is_connected:
            return await ctx.send("Não estou conectado.")

        if ctx.author.voice is None or \
                (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send("Você não está no mesmo canal de voz que eu!")

        player.queue.clear()
        await player.stop()

        await self.connect_to(ctx.guild.id, None)
        if channel:
            await ctx.send(f"Desconectado do canal `{channel.name}`")

    # @commands.command()
    # async def playtwo(self, ctx):
    #     player = self._get_player(ctx)
    #     with open(os.path.dirname(os.path.abspath(__file__))+'\\musics.json', 'w') as file:
    #         json_file = [{
    #             'author': track.author,
    #             'duration': track.duration,
    #             'extra': track.extra,
    #             'identifier': track.identifier,
    #             'is_seekable': track.is_seekable,
    #             'requester': track.requester,
    #             'stream': track.stream,
    #             'title': track.title,
    #             'track': track.track,
    #             'uri': track.uri
    #         } for track in player.queue]
    #         json.dump(json_file, file, indent=2)

    def _get_player(self, ctx: Context) -> lavalink.DefaultPlayer:
        return self.lavalink.player_manager.get(ctx.guild.id)

    async def _search_tracks(self, query: str, player: lavalink.DefaultPlayer):
        result = await player.node.get_tracks(query)

        if not result or not result['tracks']:
            return None

        return result

    def _add_tracks(self, ctx: Context, tracks: list, player: lavalink.DefaultPlayer, start_at: int = None):
        if len(tracks) > 1 and start_at is not None:
            tracks = reversed(tracks)

        for track in tracks:
            track = lavalink.AudioTrack(
                track, requester=ctx.author.id, requester_name=ctx.author.name)

            player.add(
                requester=ctx.author.id,
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

    @join.error
    @leave.error
    @_next.error
    @pause.error
    @play.error
    @playnext.error
    @_queue.error
    @repeat.error
    @resume.error
    @shuffle.error
    @stop.error
    @volume.error
    @JishakuBase.jsk_su.error
    async def error_handler(self, ctx, error):
        prefix = await self.bot.get_prefix(ctx) if isinstance(self, Jishaku) \
            else await self.client.get_prefix(ctx)

        if isinstance(error, PlayerPermissionError):
            await ctx.send(f"Você precisa ter a permissão de **{error.permission}** para isso.\n"
                           f"Veja a lista utilizando `{prefix}{error.permission.lower()} list`")

        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
            raise error

        else:
            await ctx.send(error)
            raise error


def setup(client):
    client.add_cog(MusicCommands(client))
