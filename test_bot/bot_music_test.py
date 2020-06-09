import discord
import asyncio
import youtube_dl
import random
import re
import os
import logging
from apiclient import discovery
from discord.ext import commands
from discord.utils import get
from googleapiclient.errors import HttpError
import settings

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# (https|http)://www\.youtube\.com/(.+)\?(v|list)=(.+)&?(list=)?(.+)?

youtube_api_key = settings.youtube_api_key()
discord_token = settings.bot_token()
prefix = settings.prefix()

client = commands.Bot(command_prefix=prefix)

queue = []
queue_shuffled = []
song = {}
repeat_mode = 'off'
shuffle_mode = False
song_downloaded = False
playing_now_message = None
song_download_error_message = None


# queue_shuffled = random.shuffle(queue)


@client.event
async def on_ready():
    print('Bot online')


async def PlaySong(ctx):
    global playing_now_message, song_download_error_message
    global song_downloaded, song
    global queue, queue_shuffled

    async def VerifyQueue(ctx):
        # Coloca a música no final da fila caso esteja repetindo todas as músicas.
        if repeat_mode == 'all' and song:
            queue.append(song)
            if shuffle_mode:
                queue_shuffled.append(song)
        await PlaySong(ctx)

    # Passa o 'ctx' para 'context' para quando for tocar novamente.
    context = ctx

    def PlayAgain(error):
        nonlocal context
        coro = VerifyQueue(context)
        fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
        try:
            fut.result()
        except:
            pass

    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice is not None:
        if voice.channel != channel:
            await voice.move_to(channel)

    try:
        await channel.connect()
    except:
        pass

    voice = get(client.voice_clients, guild=ctx.guild)

    if voice:
        if not len(queue) == 0 or repeat_mode == 'single' or repeat_mode == 'all':
            if not (voice.is_playing() or voice.is_paused()):

                if not repeat_mode == 'single' or not song_downloaded:
                    if not shuffle_mode:
                        song = queue.pop(0)
                    else:
                        song = queue_shuffled.pop(0)
                        try:
                            queue.remove(song)
                        except ValueError:
                            pass

                    # Define as opções de músicas
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    }

                    # Faz o download da música
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        print("Downloading song now\n")
                        try:
                            ydl.download([song['url']])
                        except Exception as error:
                            print(error)
                            song_download_error_message = await ctx.send(
                                            f"Ocorreu um problema na tentativa de tocar **{song['title']}**\n"
                                            "*Tocando próxima música.*")
                            await PlaySong(ctx)

                    # Remove a música antiga
                    old_song = os.path.isfile("song.mp3")
                    if old_song:
                        os.remove("song.mp3")

                    # Renomeia o nome do arquivo .mp3
                    for file in os.listdir("./"):
                        if file.endswith('.mp3'):
                            name = file
                            print(f'Renamed File: {file}\n')
                            os.rename(file, "song.mp3")

                    song_downloaded = True

                # Toca a música utilizando o bot no discord
                voice.play(discord.FFmpegPCMAudio('song.mp3'), after=PlayAgain)
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.25

                embed = discord.Embed(color=ctx.guild.me.top_role.color, title="**Playing Now**",
                                      description=f"[{song['title']}]({song['url']}) [{song['user'].mention}]")
                try:
                    await playing_now_message.delete()
                except:
                    pass

                try:
                    await song_download_error_message.delete()
                except:
                    pass

                await asyncio.sleep(1)
                playing_now_message = await ctx.channel.send(embed=embed)
                print("playing\n")
        else:
            try:
                await playing_now_message.delete()
            except:
                pass
            await asyncio.sleep(1)
            await ctx.send("Acabou as músicas da fila. Utilize `.play <url ou nome da musica>` para tocar mais.")


def GetIdAndTitle(url):
    get_title_id = os.popen(f'youtube-dl --default-search "ytsearch" --skip-download --get-title --get-id "{url}"') \
        .read().split(sep='\n')
    return get_title_id


@client.command()
async def play(ctx, *, search: str):
    video = {'items': []}
    playlist = False

    if search.startswith('https://'):
        link = re.match(r"^https://www\.youtube\.com/(watch|playlist)\?(v|list)=([0-9A-Za-z_-]+).*$", search)
        if link is not None:
            link = list(link.groups())

            if link[0] == 'watch':
                video = GetIdAndTitle(link[2])
                youtube_video_title = video[0]
                youtube_video_url = f'https://www.youtube.com/watch?v={video[1]}'

            elif link[0] == 'playlist':
                playlist = True
                loading = await ctx.send("Baixando dados da playlist.")

                try:
                    youtube = discovery.build('youtube', 'v3', developerKey=youtube_api_key)

                    playlistitems_list_request = youtube.playlistItems().list(
                        playlistId=link[2],
                        part='snippet',
                        maxResults=50)

                    while playlistitems_list_request:
                        await asyncio.sleep(1.5)
                        playlistitems_list_response = playlistitems_list_request.execute()

                        # Print information about each video.
                        for song in playlistitems_list_response['items']:
                            video['items'].append(song)

                        # Faz uma próxima request da próxima página da playlist. Retorna None caso não tenha.
                        playlistitems_list_request = youtube.playlistItems().list_next(
                            playlistitems_list_request,
                            previous_response=playlistitems_list_response)

                    await loading.delete()
                except:
                    await loading.delete()
                    await ctx.send("Algum problema ocorreu enquanto tentei pegar as músicas.\n"
                                   "Verifique se a URL está correta ou se existe algum vídeo indisponível "
                                   "dentro da playlist.")
                    return
            else:
                await ctx.send("Esse link não é válido. Tente novamente.")
                return

        else:
            # outra opção como youtube.be\id-música
            return
    else:
        try:
            youtube = discovery.build('youtube', 'v3', developerKey=youtube_api_key)

            request = youtube.search().list(q=search, part='snippet', type='video', maxResults=5)
            response = request.execute()

            msg = '**Selecione uma faixa clicando no emoji correspondente.**\n'

            show_information = await ctx.send(f'Mostrando músicas com o termo `{search}`\n\n')
            for x in range(0, len(response['items'])):

                # Pega a 'duração' do vídeo
                video = youtube.videos().list(id=response['items'][x]['id']['videoId'], part='contentDetails').execute()
                duration = list(
                    re.match(r'^PT(\d+H)?(\d+M)?(\d+S)?$', video['items'][0]['contentDetails']['duration']).groups())

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

                video_duration = duration[0] + duration[1] + duration[2]
                video_title = response['items'][x]['snippet']['title']

                msg = msg + f"**{(x + 1)})** {video_title} - ({video_duration})\n"

            message = await ctx.send(msg)
            emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
            await message.add_reaction(emoji[0])
            await message.add_reaction(emoji[1])
            await message.add_reaction(emoji[2])
            await message.add_reaction(emoji[3])
            await message.add_reaction(emoji[4])

            def check(reaction, user):
                return user == ctx.author and (str(reaction.emoji) == emoji[0]
                                               or str(reaction.emoji) == emoji[1]
                                               or str(reaction.emoji) == emoji[2]
                                               or str(reaction.emoji) == emoji[3]
                                               or str(reaction.emoji) == emoji[4])

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60, check=check)
                await show_information.delete()
                await message.delete()
                for x in range(0, len(emoji)):
                    if str(reaction.emoji) == emoji[x]:
                        youtube_video_title = response['items'][x]['snippet']['title']
                        youtube_video_url = f'https://www.youtube.com/watch?v={response["items"][x]["id"]["videoId"]}'
                        break

            except asyncio.TimeoutError:
                error = await ctx.send("Você demorou muito.")

                await error.delete(delay=5)
                await show_information.delete()
                return
        except HttpError:
            await ctx.send("O limite de requisições foi atingido. Não é possível procurar por uma música usando Youtube"
                           "Data API.")
            return

    # try:
    #     get_title_id = os.popen(f'youtube-dl --default-search "ytsearch" --skip-download --get-title --get-id "{search}"') \
    #         .read().split(sep='\n')
    #
    #     youtube_video_title = get_title_id[0]
    #     youtube_video_url = f'https://www.youtube.com/watch?v={get_title_id[1]}'
    # except:
    #     await ctx.send(f"Não foi possível achar a música com o nome: `{search}`")
    #     return

    # get all the information from the video using the url
    # video = youtube_dl.YoutubeDL({}).extract_info(youtube_video_url, download=False)

    if not playlist:
        queue.append({'title': youtube_video_title, 'url': youtube_video_url, 'user': ctx.author})
        embed = discord.Embed(color=ctx.guild.me.top_role.color,
                              title='**Adicionado a Fila**',
                              description=f"[{youtube_video_title}]({youtube_video_url})  [{ctx.author.mention}]")
    else:
        for song in video['items']:
            youtube_video_url = f"https://www.youtube.com/watch?v={song['snippet']['resourceId']['videoId']}"
            youtube_video_title = song['snippet']['title']
            queue.append({'title': youtube_video_title, 'url': youtube_video_url, 'user': ctx.author})
        embed = discord.Embed(color=ctx.guild.me.top_role.color,
                              title='**Adicionado a Fila**',
                              description=f"`{len(video['items'])}` músicas da playlist.  [{ctx.author.mention}]")

    await ctx.send(embed=embed)
    print("Added to queue\n")

    await PlaySong(ctx)


@client.command(name='queue', aliases=['q'])
async def _queue(ctx, page=1):
    global queue_shuffled, queue, song
    msg = ''

    if len(queue) > 0 or song:
        if page == 0:
            page = 1
        elif page < 0:
            await ctx.send("As páginas só podem ser mostradas com números positivos!")
            return

        tracks_number = 10  # Quantas músicas aparecerão por página

        max_pages = len(queue) // tracks_number
        if len(queue) % tracks_number > 0:
            max_pages = max_pages + 1
            if page > max_pages:
                page = max_pages
        if max_pages == 0:
            max_pages = 1
        if len(queue) == 0:
            page = 1

        if not shuffle_mode:
            queue_list = queue[tracks_number * (page - 1):tracks_number * page]
        else:
            queue_list = queue_shuffled[tracks_number * (page - 1):tracks_number * page]
            msg = 'Mostrando playlist embaralhada\n'

        if repeat_mode == 'off':
            msg = msg + '\n\n'
        elif repeat_mode == 'single':
            msg = msg + 'Repetindo a faixa atual\n\n\n'
        elif repeat_mode == 'all':
            msg = msg + 'Repetindo a fila atual\n\n\n'

        msg = msg + f'Página **{page}** de **{max_pages}**\n\n'

        voice = get(client.voice_clients, guild=ctx.guild)

        i = tracks_number * (page - 1)
        if page == 1:
            if voice and voice.is_paused():
                msg = msg + f'**⏸ {song["title"]}** - *[@{song["user"].name}]*\n'
            else:
                msg = msg + f'**▶ {song["title"]}** - *[@{song["user"].name}]*\n'

        for track in queue_list:
            i = i + 1
            msg = msg + f'`[{i}]` **{track["title"]}** - *[@{track["user"].name}]*\n'

        await ctx.send(msg)


@client.command()
async def pause(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print("Music paused")
        voice.pause()
        await ctx.send("A música foi pausada.")
    else:
        if voice and voice.is_paused():
            await ctx.send("O player já está pausado")
        else:
            print("Nenhuma música está sendo tocada")
            await ctx.send("Nenhuma música está sendo tocada, falha em pausar player.")


@client.command(aliases=['unpause'])
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)

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


@client.command()
async def repeat(ctx, arg):
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


@client.command()
async def shuffle(ctx):
    global shuffle_mode
    global queue_shuffled

    if len(queue) > 0 or song:
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

@client.command(aliases=['next'])
async def _next(ctx):
    global song_downloaded
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice:
        song_downloaded = False
        voice.stop()
        await ctx.send("Tocando próxima música.")


@client.command()
async def stop(ctx):
    global song_downloaded, shuffle_mode, repeat_mode
    voice = get(client.voice_clients, guild=ctx.guild)

    queue.clear()
    queue_shuffled.clear()
    song.clear()
    song_downloaded = False
    shuffle_mode = False
    repeat_mode = 'off'

    # Feature Incomplete: Parar a música mesmo quando pausar
    if voice:
        print("Music stopped")
        voice.stop()
        await ctx.send("O player parou de tocar.")
    else:
        print("Nenhuma música está sendo tocada.")
        await ctx.send("Nenhuma música está sendo tocada, falha em parar player.")


@client.command()
async def join(ctx):
    top_role = ctx.guild.me.top_role
    channel = ctx.message.author.voice.channel
    # await discord.VoiceChannel.connect(channel)
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        if voice.channel != channel:
            await voice.move_to(channel)
    else:
        await channel.connect()

    if not voice is None:
        await voice.disconnect()

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        if voice.channel != channel:
            await voice.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"Conectado ao canal `{channel}`.")


@client.command()
async def apo(ctx):
    await ctx.send("Oi")


@client.command()
async def leave(ctx):
    # print(client.voice_clients[0].guild)
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    # server = ctx.message.guild.voice_client
    # server = client.voice_clients[0]
    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send(f"Saiu do canal `{channel}`")
    else:
        print("O bot não está em nenhum canal.")


@client.command()
async def shutdown(ctx):
    if ctx.message.author.id == ctx.guild.owner.id:  # replace OWNERID with your user id
        print("shutdown")
        try:
            await client.logout()
        except:
            print("EnvironmentError")
            client.clear()
        else:
            await ctx.send("You do not own this bot!")


client.run(discord_token)
