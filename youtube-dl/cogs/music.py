import discord
import asyncio
import youtube_dl
import random
import ast
import os
import re
import sys
from discord.ext import commands
from discord.ext import commands
from discord.utils import get
from apiclient import discovery
from googleapiclient.errors import HttpError

import settings


queue = []
queue_shuffled = []
songPlayingNow = {}
repeat_mode = 'off'
shuffle_mode = False
song_downloaded = False
playing_now_message = None
song_download_error_message = None

youtube_api_key = settings.youtube_api_key()


class MusicCommands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def play(self, ctx, *, search):
        
        if await isUserConnectedInVoiceChannel(ctx) == False:
            return

        songs = await searchSongs(self.client, ctx, search)
        if songs:
            await addSongsToQueue(self.client, ctx, songs['items'])
            
            if songs['is_playlist']:
                embed = discord.Embed(color=ctx.guild.me.top_role.color,
                            title='**Adicionado a Fila**',
                            description=f"`{len(songs['items'])}` músicas da playlist.  [{ctx.author.mention}]")
            else:
                embed = discord.Embed(color=ctx.guild.me.top_role.color,
                            title='**Adicionado a Fila**',
                            description=f"[{songs['items'][0]['title']}]({songs['items'][0]['url']})  [{ctx.author.mention}]") 
                
            await ctx.send(embed=embed)
            await PlaySong(self.client, ctx)

    @commands.command(name='queue', aliases=['q'])
    async def _queue(self, ctx, page=1):
        global queue_shuffled, queue
        msg = ''

        print("Música atual:", songPlayingNow, "\n")

        if len(queue) > 0 or songPlayingNow:
            if page == 0:
                page = 1
            elif page < 0:
                await ctx.send("As páginas só podem ser mostradas com números positivos!")
                return

            SONGS_PER_PAGE = 10

            max_pages = len(queue) // SONGS_PER_PAGE
            if len(queue) % SONGS_PER_PAGE > 0:
                max_pages = max_pages + 1
                if page > max_pages:
                    page = max_pages
            if max_pages == 0:
                max_pages = 1
            if len(queue) == 0:
                page = 1

            if not shuffle_mode:
                queue_list = queue[SONGS_PER_PAGE * (page - 1):SONGS_PER_PAGE * page]
            else:
                queue_list = queue_shuffled[SONGS_PER_PAGE * (page - 1):SONGS_PER_PAGE * page]
                msg = 'Mostrando playlist embaralhada\n'

            if repeat_mode == 'off':
                msg = msg + '\n\n'
            elif repeat_mode == 'single':
                msg = msg + 'Repetindo a faixa atual\n\n\n'
            elif repeat_mode == 'all':
                msg = msg + 'Repetindo a fila atual\n\n\n'

            msg = msg + f'Página **{page}** de **{max_pages}**\n\n'

            voiceClient = get(self.client.voice_clients, guild=ctx.guild)

            index = SONGS_PER_PAGE * (page - 1)
            if page == 1:
                if voiceClient and voiceClient.is_paused():
                    msg = msg + f'**⏸ {songPlayingNow["title"]}** - *[@{songPlayingNow["user_name"]}]*\n'
                else:
                    msg = msg + f'**▶ {songPlayingNow["title"]}** - *[@{songPlayingNow["user_name"]}]*\n'

            for song in queue_list:
                index = index + 1
                msg = msg + f'`[{index}]` **{song["title"]}** - *[@{song["user_name"]}]*\n'

            await ctx.send(msg)

    @commands.command()
    async def pause(self, ctx):
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice:
            if voice.is_playing():
                print("Music paused")
                voice.pause()
                await ctx.send("A música foi pausada. Para despausar utilize `.resume`")
            elif voice.is_paused():
                await ctx.send("O player já está pausado")
        else:
            print("Nenhuma música está sendo tocada")
            await ctx.send("Nenhuma música está sendo tocada, falha em pausar player.")

    @commands.command(aliases=['unpause'])
    async def resume(self, ctx):
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            print("Resumed Music")
            voice.resume()
            await ctx.send("O player foi despausado, voltando a tocar.")
        else:
            if voice and voice.is_playing():
                print("Music is not paused")
                await ctx.send("A música não está pausada, falha em despausar.")
            else:
                await ctx.send("Nenhuma música está sendo tocada, falha em despausar player.")

    @commands.command()
    async def repeat(self, ctx, arg):
        global repeat_mode
        if arg == 'single':
            await ctx.send('Repetindo a faixa atual.')
            repeat_mode = 'single'
        elif arg == 'all':
            await ctx.send('Repetindo todas as faixas.')
            repeat_mode = 'all'
        elif arg == 'off':
            await ctx.send('Desligando repetição.')
            repeat_mode = False
        else:
            await ctx.send('Use `single | off` para ativar/desativar a repetição.')

    @commands.command()
    async def shuffle(self, ctx):
        global shuffle_mode
        global queue_shuffled

        if len(queue) > 0 or songPlayingNow:
            if not shuffle_mode:
                shuffle_mode = True
                queue_shuffled = random.sample(queue, len(queue))
                await ctx.send("O reprodutor agora está em modo aleatório.")
            else:
                shuffle_mode = False
                queue_shuffled.clear()
                await ctx.send("O reprodutor não está mais em modo aleatório.")
        else:
            await ctx.send("Não há músicas na fila para ser embaralhada.")

    @commands.command(aliases=['next'])
    async def _next(self, ctx):
        global song_downloaded
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice:
            song_downloaded = False
            voice.stop()
            await ctx.send("Tocando próxima música.")

    @commands.command()
    async def stop(self, ctx):
        global song_downloaded, shuffle_mode, repeat_mode
        voice = get(self.client.voice_clients, guild=ctx.guild)

        queue.clear()
        queue_shuffled.clear()
        songPlayingNow.clear()
        song_downloaded = False
        shuffle_mode = False
        repeat_mode = 'off'

        if voice:
            print("Music stopped")
            voice.stop()
            await ctx.send("O player parou de tocar.")
        else:
            print("Nenhuma música está sendo tocada.")
            await ctx.send("Nenhuma música está sendo tocada, falha em parar player.")

    @commands.command()
    async def join(self, ctx):
        top_role = ctx.guild.me.top_role
        channel = ctx.message.author.voice.channel
        voiceClient = get(self.client.voice_clients, guild=ctx.guild)

        if voiceClient and voiceClient.is_connected():
            if voiceClient.channel != channel:
                await voiceClient.move_to(channel)
        else:
            await channel.connect()

        if not voiceClient is None:
            await voiceClient.disconnect()

        voiceClient = get(self.client.voice_clients, guild=ctx.guild)
        if voiceClient and voiceClient.is_connected():
            if voiceClient.channel != channel:
                await voiceClient.move_to(channel)
        else:
            await channel.connect()

        await ctx.send(f"Conectado ao canal `{channel}`.")

    @commands.command()
    async def leave(self, ctx):
        
        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.send(f"Saiu do canal `{channel}`")
        else:
            print("O bot não está em nenhum canal.")

    @commands.command()
    async def shutdown(self, ctx):
        if ctx.message.author.id == ctx.guild.owner.id:
            print("shutdown")
            try:
                await self.client.logout()
            except:
                print("EnvironmentError")
                self.client.clear()
            else:
                await ctx.send("You do not own this bot!")

    @commands.command()
    async def playnext(self, ctx, *, search):

        if await isUserConnectedInVoiceChannel(ctx) == False:
            return

        songs = await searchSongs(self.client, ctx, search)
        if songs:
            await addSongsToQueueToPlayNext(self.client, ctx, songs['items'])
            
            if songs['is_playlist']:
                embed = discord.Embed(color=ctx.guild.me.top_role.color,
                            title='**Adicionado ao Começo da Fila**',
                            description=f"`{len(songs['items'])}` músicas da playlist.  [{ctx.author.mention}]")
            else:
                embed = discord.Embed(color=ctx.guild.me.top_role.color,
                            title='**Adicionado ao Começo da Fila**',
                            description=f"[{songs['items'][0]['title']}]({songs['items'][0]['url']})  [{ctx.author.mention}]") 
                
            await ctx.send(embed=embed)
            await PlaySong(self.client, ctx)

                
async def PlaySong(client, ctx):
    global playing_now_message, song_downloaded

    def PlayAgain(error):
        coroutine = VerifyQueue(client, ctx)
        fut = asyncio.run_coroutine_threadsafe(coroutine, client.loop)
        try:
            fut.result()
        except:
            pass
    
    if await isUserConnectedInVoiceChannel(ctx) == False:
        return

    await connectToUserVoiceChannel(client, ctx)

    voiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient:
        if canContinue():
            if isPlayingOrPaused(voiceClient) == False:

                if repeat_mode != 'single' or song_downloaded == False:
                    selectQueueSongToPlay()
                    await downloadSong(client, ctx)

                voiceClient.play(discord.FFmpegPCMAudio('song.mp3'), after=PlayAgain)
                voiceClient.source = discord.PCMVolumeTransformer(voiceClient.source)
                voiceClient.source.volume = 0.25

                embed = discord.Embed(color=ctx.guild.me.top_role.color, title="**Playing Now**",
                                    description=f"[{songPlayingNow['title']}]({songPlayingNow['url']}) [<@{songPlayingNow['user_id']}>]")
                await deletePlayerMessages()
                await asyncio.sleep(1)
                playing_now_message = await ctx.channel.send(embed=embed)
                print("playing\n")
        else:
            await deletePlayerMessages()
            await asyncio.sleep(1)
            await ctx.send("Acabou as músicas da fila. Utilize `.play <url ou nome da musica>` para tocar mais.")
            songPlayingNow.clear()
            song_downloaded = False


async def VerifyQueue(client, ctx):
    if repeat_mode == 'all' and songPlayingNow:
        queue.append(songPlayingNow)
        if shuffle_mode:
            queue_shuffled.append(songPlayingNow)
    await PlaySong(client, ctx)


async def isUserConnectedInVoiceChannel(ctx):
    try:
        if ctx.message.author.voice.channel:
            return True
    except AttributeError as error:
        print(error)
        await ctx.send("Você não está conectado em nenhum canal de voz.")
        return False


async def connectToUserVoiceChannel(client, ctx):
    userChannel = ctx.message.author.voice.channel
    voiceClient = get(client.voice_clients, guild=ctx.guild)

    if voiceClient != None and voiceClient.channel != userChannel:
        await voiceClient.move_to(userChannel)

    try:
        await userChannel.connect()
    except:
        pass


def canContinue():
    if len(queue) != 0 or repeat_mode == 'single' or repeat_mode == 'all':
        return True
    else:
        return False


def isPlayingOrPaused(voiceClient):
    if voiceClient.is_playing() or voiceClient.is_paused():
        return True
    else:
        return False


def selectQueueSongToPlay():
    global songPlayingNow, shuffle_mode, queue, queue_shuffled
    if not shuffle_mode:
        songPlayingNow = queue.pop(0)
    else:
        songPlayingNow = queue_shuffled.pop(0)
        try:
            queue.remove(songPlayingNow)
        except ValueError:
            pass


async def downloadSong(client, ctx):
    global song_download_error_message, song_downloaded

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        print("Downloading song now\n")
        try:
            ydl.download([songPlayingNow['url']])
            song_downloaded = True
        except Exception as error:
            print(error)
            song_download_error_message = await ctx.send(
                            f"Ocorreu um problema na tentativa de tocar **{songPlayingNow['title']}**\n"
                            "*Tocando próxima música.*")
            await PlaySong(client, ctx)

    RemoveOldSong()
    RenameNewSong()


def RemoveOldSong():
    old_song = os.path.isfile("song.mp3")
    if old_song:
        os.remove("song.mp3")


def RenameNewSong():
    for file in os.listdir("./"):
        if file.endswith('.mp3'):
            name = file
            print(f'Renamed File: {file}\n')
            os.rename(file, "song.mp3")


async def deletePlayerMessages():
    try:
        await playing_now_message.delete()
    except:
        pass

    try:
        await song_download_error_message.delete()
    except:
        pass


async def searchSongs(client, ctx, search):
    if search.startswith('https://'):
        songs = await searchSongsUsingURL(ctx, search)
    else:
        songs = await searchSongsUsingKeyWord(client, ctx, search)

    return songs


async def searchSongsUsingURL(ctx, search):
    results = {'is_playlist': False, 'items': []}

    link = re.match(r"^https://www\.youtube\.com/(?P<state>watch|playlist)\?(v|list)=(?P<id>[0-9A-Za-z_-]+).*$", search)
    if link != None:
        link = link.groupdict()

        print("\n", link, "\n")
        if link['state'] == 'watch':
            results['items'].append(GetVideoTitleAndURL(link['id']))

        elif link['state'] == 'playlist':
            results['is_playlist'] = True
            playlistItems = await searchSongsThroughPlaylistItems(ctx, link['id'])
            
            if playlistItems:
                for item in playlistItems:
                    results['items'].append(item)
        else:
            await ctx.send("Esse link não é válido. Tente novamente.")

    else:
        # outra opção como youtube.be\id-música
        return False

    if len(results['items']) > 0:
        return results
    else:
        return False


def GetVideoTitleAndURL(id):
    get_video_title = os.popen(f'youtube-dl --default-search "ytsearch" --skip-download --get-title "/{id}"') \
        .read().split(sep='\n')

    youtube_video_title = get_video_title[0]
    youtube_video_url = f'https://www.youtube.com/watch?v={id}'
    return {'title': youtube_video_title, 'url': youtube_video_url}


async def searchSongsThroughPlaylistItems(ctx, id):
    playlistItems = []
    loading = await ctx.send("Baixando dados da playlist.")

    try:
        youtube = discovery.build('youtube', 'v3', developerKey=youtube_api_key)

        playlistitems_list_request = youtube.playlistItems().list(
            playlistId=id,
            part='snippet',
            maxResults=50)

        while playlistitems_list_request:
            await asyncio.sleep(1.5)
            playlistitems_list_response = playlistitems_list_request.execute()

            # Print information about each video.
            for song in playlistitems_list_response['items']:
                youtube_video_url = f"https://www.youtube.com/watch?v={song['snippet']['resourceId']['videoId']}"
                youtube_video_title = song['snippet']['title']
                playlistItems.append({'title': youtube_video_title, 'url': youtube_video_url})

            # Faz uma próxima request da próxima página da playlist. Retorna None caso não tenha.
            playlistitems_list_request = youtube.playlistItems().list_next(
                playlistitems_list_request,
                previous_response=playlistitems_list_response)

        await loading.delete()
        return playlistItems
    except:
        await loading.delete()
        await ctx.send("Algum problema ocorreu enquanto tentei pegar as músicas.\n"
                    "Verifique se a URL está correta ou se existe algum vídeo indisponível "
                    "dentro da playlist.")
        return False


async def searchSongsUsingKeyWord(client, ctx, search):
    results = {'is_playlist': False, 'items': []}

    try:
        youtube = discovery.build('youtube', 'v3', developerKey=youtube_api_key)

        youtube_api_request = youtube.search().list(q=search, part='snippet', type='video', maxResults=5)
        foundSongs = youtube_api_request.execute()

        searchingTerm_message = await ctx.send(f'Mostrando músicas com o termo `{search}`\n\n')
        select_song_message = await constructSearchingSongMessage(ctx, foundSongs, youtube)

        song = await selectSearchingSongToPlay(client, ctx, foundSongs, select_song_message, searchingTerm_message)
        if song:
            results['items'].append(song)
    except HttpError:
        await ctx.send("O limite de requisições foi atingido. Não é possível procurar por uma música usando Youtube"
                    "Data API.")
    
    if len(results['items']) > 0:
        return results
    else:
        return False


async def constructSearchingSongMessage(ctx, foundSongs, youtube):
    msg = '**Selecione uma faixa clicando no emoji correspondente.**\n'
    
    for x in range(0, len(foundSongs['items'])):
        video = youtube.videos().list(id=foundSongs['items'][x]['id']['videoId'], part='contentDetails').execute()
        duration = list(
            re.match(r'^PT(\d+H)?(\d+M)?(\d+S)?$', video['items'][0]['contentDetails']['duration']).groups())

        video_duration = transformVideoDuration(duration)
        video_title = foundSongs['items'][x]['snippet']['title']

        msg = msg + f"**{(x + 1)})** {video_title} - ({video_duration})\n"
    
    return msg


def transformVideoDuration(duration):
    # Transforma: PT#H#M#S em H:M:S, por exemplo: PT4M2S -> 00:04:02
    if duration[0] is None:
        duration[0] = ''
    else:
        duration[0] = duration[0].replace('H', ':')
        if len(duration[0]) < 3:
            duration[0] = '0' + duration[0]

    if duration[1] is None:
        duration[1] = '00:'
    else:
        duration[1] = duration[1].replace('M', ':')
        if len(duration[1]) < 3:
            duration[1] = '0' + duration[1]

    if duration[2] is None:
        duration[2] = '00'
    else:
        duration[2] = duration[2].replace('S', '')
        if len(duration[2]) < 2:
            duration[2] = '0' + duration[2]
    
    return duration[0] + duration[1] + duration[2]


async def selectSearchingSongToPlay(client, ctx, foundSongs, select_song_message, searchingTerm_message):
    select_song_message = await ctx.send(select_song_message)
    emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
    await select_song_message.add_reaction(emoji[0])
    await select_song_message.add_reaction(emoji[1])
    await select_song_message.add_reaction(emoji[2])
    await select_song_message.add_reaction(emoji[3])
    await select_song_message.add_reaction(emoji[4])

    def check(reaction, user):
        return reaction.message.id == select_song_message.id \
            and user == ctx.author \
            and (str(reaction.emoji) == emoji[0]
            or str(reaction.emoji) == emoji[1]
            or str(reaction.emoji) == emoji[2]
            or str(reaction.emoji) == emoji[3]
            or str(reaction.emoji) == emoji[4])

    try:
        reaction, user = await client.wait_for('reaction_add', timeout=60, check=check)
        await searchingTerm_message.delete()
        await select_song_message.delete()
        for x in range(0, len(emoji)):
            if str(reaction.emoji) == emoji[x]:
                youtube_video_title = foundSongs['items'][x]['snippet']['title']
                youtube_video_url = f'https://www.youtube.com/watch?v={foundSongs["items"][x]["id"]["videoId"]}'
                return {'title': youtube_video_title, 'url': youtube_video_url}

    except asyncio.TimeoutError:
        error = await ctx.send("Você demorou muito.")
        await error.delete(delay=5)
        await searchingTerm_message.delete()
        return False


async def addSongsToQueue(client, ctx, songs):
    for song in songs:
        queue.append({'title': song['title'], 'url': song['url'], 'user_name': ctx.author.name, 'user_id': ctx.author.id})
        if shuffle_mode:
            queue_shuffled.append({'title': song['title'], 'url': song['url'], 'user_name': ctx.author.name, 'user_id': ctx.author.id})

    print("Added to queue\n")
    return


async def addSongsToQueueToPlayNext(client, ctx, songs):
    for song in reversed(songs):
        queue.insert(0, {'title': song['title'], 'url': song['url'], 'user_name': ctx.author.name, 'user_id': ctx.author.id})
        if shuffle_mode:
            queue_shuffled.insert(0, {'title': song['title'], 'url': song['url'], 'user_name': ctx.author.name, 'user_id': ctx.author.id})

    print("Added to queue")
    return


def setup(client):
    client.add_cog(MusicCommands(client))