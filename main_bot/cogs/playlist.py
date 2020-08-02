import discord
import asyncio
import re
import ast
from .music import songPlayingNow, queue
from .music import searchSongs, addSongsToQueue, PlaySong, isUserConnectedInVoiceChannel
from main_bot.databaseClass import PlaylistDatabase
from main_bot.playlistClass import Playlist
from discord.ext import commands

playlistQuery = PlaylistDatabase('guilds_database.db')

SONGS_PER_PAGE = 15

class PlaylistCommands(commands.Cog):

    def __init__(self, client):
        self.client = client

    # createplaylist [privacy: private|public] <playlist-name>
    @commands.command()
    async def createplaylist(self, ctx, *args):
        if len(args) > 0:
            if args[0] == 'private' or args[0] == 'public':
                privacy = args[0]
                playlist_name = " ".join(args[1:len(args)])
            else:
                privacy = 'public'
                playlist_name = " ".join(args)
            
            try:
                if PlaylistExists(ctx.guild.id, ctx.author.id, playlist_name) == False:
                    
                    playlistQuery.create(ctx.guild.id, ctx.guild.name, ctx.author.id, playlist_name, f'{ctx.author.name}#{ctx.author.discriminator}', privacy)
                    
                    await ctx.send("Playlist criada com sucesso!\n"
                    f"\n> _Nome:_ `{playlist_name}`" 
                    f"\n> _Propriedade:_ **{'Pública' if privacy == 'public' else 'Privado'}**"
                    "\n\n_Você pode alterar a propriedade utilizando o comando `updateplaylist`._")
                else:
                    await ctx.send("Já existe uma playlist sua com esse nome.")
            except Exception as error:
                print(error)
                await ctx.send("Não foi possível criar uma playlist.")
        else:
            await ctx.send("Você não informou o nome da playlist.")

    # updateplaylist [public|private] <playlist-name>
    @commands.command()
    async def updateplaylist(self, ctx, *args):

        if len(args) > 0:
            if args[0] == 'private' or args[0] == 'public':
                privacy = args[0]
                playlist_name = " ".join(args[1:len(args)])
            else:
                privacy = 'public'
                playlist_name = " ".join(args)

            try:
                if (playlist := Playlist.returnPlaylist(ctx.guild.id, ctx.author.id, playlist_name)):
                    
                    playlistQuery.updatePlaylistPrivacy(playlist, privacy)
                    
                    await ctx.send("Playlist atualizada com sucesso!\n"
                        f"\n> _Nome:_ `{playlist.name}`" 
                        f"\n> _Propriedade:_ **{'Pública' if privacy == 'public' else 'Privado'}**")
                else:
                    await ctx.send("Não existe uma playlist sua com esse nome.")
            except Exception as error:
                print(error)
                await ctx.send("Não foi possível atualizar sua playlist.")
        else:
            await ctx.send("Você não informou o nome da playlist.")

    # addtoplaylist <playlist-name> - <url or keyword>
    @commands.command()
    async def addtoplaylist(self, ctx, *args):
        for x in args:
            hyphen = re.match(r"^-$", x)
            if hyphen != None:
                playlist_name = " ".join(args[0:(args.index(x))])
                if playlist_name.strip() == '':
                    await ctx.send("Não foi informado nenhuma playlist.")
                    return

                search = " ".join(args[args.index(x)+1:])
                if search.strip() == '':
                    await ctx.send("Não foi informado nenhuma palavra de pesquisa ou link.")
                    return
                break
            elif args.index(x) == len(args)-1:
                await ctx.send('Comando inválido. Não esqueça do `-`, exemplo:\n'
                            '\n`.addtoplaylist Favorite Songs - Imagine Dragons Believer`')
                return

        if (playlist := Playlist.returnPlaylist(ctx.guild.id, ctx.author.id, playlist_name)):
            if (songs := await searchSongs(self.client, ctx, search)):
                playlistQuery.addSongs(playlist, songs['items'])
                
                if songs['is_playlist']:
                    embed = discord.Embed(color=ctx.guild.me.top_role.color,
                                    title='**Adicionado a Playlist**',
                                    description=f"`{len(songs['items'])}` músicas em *{playlist.name}*.  [{ctx.author.mention}]")
                else:
                    embed = discord.Embed(color=ctx.guild.me.top_role.color,
                                    title='**Adicionado a Playlist**',
                                    description=f'[{songs["items"][0]["title"]}]({songs["items"][0]["url"]}) em  *{playlist.name}*.  [{ctx.author.mention}]')
                    
                await ctx.send(embed=embed)
            else:
                await ctx.send("Não foi achado nenhuma música ou playlist.")
        else:
            await ctx.send("Não existe uma playlist sua com esse nome.")

    # savequeuetoplaylist <add|new> [public|private] <playlist-name>
    @commands.command()
    async def savequeuetoplaylist(self, ctx, *, args):

        if (regex := re.match(r'^(add|new) ((public|private) )?(.+)$', args)):
            if songPlayingNow:
                privacy = regex.group(3)
                playlist_name = regex.group(4)

                if regex.group(1) == 'new':
                    await saveQueueToNewPlaylist(ctx, privacy, playlist_name)
                elif regex.group(1) == 'add':
                    await saveQueueToExistencePlaylist(ctx, playlist_name)
            else:
                await ctx.send("Não existe nenhuma música na fila de reprodução.")
        else:
            await ctx.send("Argumento inválido. Use: \n\n"
                           "`.savequeuetoplaylist <add|new> [public|private] <playlist-name>`")

    # includeplaylist <playlist-name> - <id-user> <playlist-name-user> [songs-interval]
    @commands.command()
    async def includeplaylist(self, ctx, *, args):
        index = None
        regex = r"^(?P<author_playlist_name>.+) - <?@?(?:[!&]?)(?P<userID>[0-9]+)>? (?P<user_playlist_name>(?:.(?!\d+-\d+))+) ?(?:(?P<start>\d+)-(?P<end>\d+))?$"

        if (matches := re.match(regex, args)):
            command = matches.groupdict()

            if command['start'] and command['end']:
                index = {
                    'start': int(command['start']),
                    'end': int(command['end'])
                }

                if validateIndex(index) == False:
                    return

            user_playlist = Playlist.returnPlaylist(
                ctx.guild.id, 
                int(command['userID']), 
                command['user_playlist_name'] 
            )

            author_playlist = Playlist.returnPlaylist(
                ctx.guild.id,
                ctx.author.id, 
                command['author_playlist_name']
            )

            if author_playlist and user_playlist and isPlaylistPublic(ctx, user_playlist):
                if index:
                    new_songs = user_playlist.songs[index['start']-1 : index['end']]
                else:
                    new_songs = user_playlist.songs

                playlistQuery.addSongs(author_playlist, new_songs)

                embed=discord.Embed(title="Playlist Importada com Sucesso!", color=ctx.guild.me.top_role.color)
                embed.add_field(name=":arrow_right:  Origem:", value=f" {user_playlist.name} \n [{user_playlist.owner}]\n{'-' * 15}", inline=True)
                embed.add_field(name=":arrow_right:  Destino:", value=f" {author_playlist.name} \n [{author_playlist.owner}]\n{'-' * 15}", inline=True)
                embed.add_field(name=":musical_note:  Adicionada:", value=f" **{len(new_songs)}** {'músicas' if len(new_songs) > 1 else 'música'}.", inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send("Não foi possível importar uma playlist para outra. Isso pode ter\n"
                               "acontecido pelos seguintes motivos:\n"
                               " **-** O nome da sua playlist não existe;\n"
                               " **-** O nome da playlist do usuário não existe;\n"
                               " **-** A playlist do usuário é _privada_.")
        else:
            await ctx.send("Argumento inválido. Use: `includeplaylist <playlist-name> - <id-user> <playlist-name-user> [songs interval]`")

    # removefromplaylist <playlist-name> - <[start:end] or keyword name>
    @commands.command()
    async def removefromplaylist(self, ctx, *, args):
        if (matchedCommand := re.match(r'^(.+) (index|keyword) (.+)$', args)):
            playlist_name = matchedCommand.group(1)
            method = matchedCommand.group(2)
            IndexOrKeyword = matchedCommand.group(3)

            if (playlist := Playlist.returnPlaylist(ctx.guild.id, ctx.author.id, playlist_name)):
                if method == 'index':
                    await removeSongsFromIndex(ctx, playlist, IndexOrKeyword)
                elif method == 'keyword':
                    await removeSongFromKeyword(self.client, ctx, playlist, IndexOrKeyword)
            else:
                await ctx.send("Não existe uma playlist sua com esse nome.")
        else:
            await ctx.send("Argumento inválido. Use:\n"
                           "`removefromplaylist <playlist-name> <index|keyword> <[start:end]|keyword name>`")

    # seeallplaylist <user id or @user>
    @commands.command()
    async def seeallplaylist(self, ctx, *, userID):

        if (match := re.match(r"^<?@?!?([0-9]+)>?$", userID)):
            userID = match.group(1)
        else:
            await ctx.send("O _ID_ do usuário informado não é válido. Verifique novamente.")
            return

        userPlaylists = playlistQuery.GetUserPlaylists(ctx.guild.id, userID)

        msg = f"> Playlists do usuário <@{userID}>:\n"
        for playlist in userPlaylists:
            msg = msg + f"\t**#{userPlaylists.index(playlist)+1} -** {playlist[0]}\t_(Songs: {playlist[1]})_\n"
        
        await ctx.send(msg)

    # showplaylist <user id or @user> <playlist name>
    @commands.command()
    async def showplaylist(self, ctx, *, args):
        
        if (match := re.match(r"^<?@?!?([0-9]+)>? (.+)$", args)):
            userID = match.group(1)
            playlist_name = match.group(2)

            if (playlist := Playlist.returnPlaylist(ctx.guild.id, int(userID), playlist_name)):
                await showSongsFromPlaylist(self.client, ctx, playlist)

        else:
            await ctx.send("Argumentos inválidos. Utilize:\n"
                           "`showplaylist <id do usuário ou mencionado> <playlist name>`")

    # loadplaylist <user id> <playlist-name>
    @commands.command()
    async def loadplaylist(self, ctx, *, args):
        if await isUserConnectedInVoiceChannel(ctx):
            index = None
             
            if (matches := re.match(r"<?@?(?:[!&]?)([0-9]+)>? ((?:.(?!\d+-\d+))+) ?(?:(\d+)-(\d+))?$", args)):
                userID = int(matches.group(1))
                playlist_name = matches.group(2)
                
                if matches.group(3) and matches.group(4):
                    index = {
                        'start': int(matches.group(3)),
                        'end': int(matches.group(4))
                    }
                    if validateIndex(index) == False:
                        return

                if (playlist := Playlist.returnPlaylist(ctx.guild.id, userID, playlist_name)):
                    if await PlaylistCanBePlayed(ctx, playlist):
                        if index:
                            playlist.songs = playlist.songs[index['start']-1 : index['end']]

                        await addPlaylistSongsToQueue(self.client, ctx, playlist)
                else:
                    await ctx.send(f"Não existe uma playlist do usuário <@{userID}> com esse nome.")
            else:
                await ctx.send("Argumento inválido. Use:\n"
                               "`loadplaylist <@user ou id do usuário> <nome da playlist>`")

    # deleteplaylist <playlist-name>
    @commands.command()
    async def deleteplaylist(self, ctx, *, playlist_name):
        if (playlist := Playlist.returnPlaylist(ctx.guild.id, ctx.author.id, playlist_name)):
            playlistQuery.delete(playlist)

            await ctx.send(f"Playlist `{playlist.name}` deletada com sucesso.")
        else:
            await ctx.send("Não existe uma playlist sua com esse nome.")

    # clearplaylist <playlist-name>
    @commands.command()
    async def clearplaylist(self, ctx, *, playlist_name):    
        if (playlist := Playlist.returnPlaylist(ctx.guild.id, ctx.author.id, playlist_name)):

            playlist.songs = []
            playlistQuery.updatePlaylistSongs(playlist)

            await ctx.send(f"Playlist `{playlist.name}` limpada com sucesso.")
        else:
            await ctx.send("Você não tem uma playlist com esse nome.")


async def addPlaylistSongsToQueue(client, ctx, playlist):

    await addSongsToQueue(client, ctx, playlist.songs)

    embed = discord.Embed(color=ctx.guild.me.top_role.color,
                        title='**Adicionado a Fila**',
                        description=f"`{len(playlist.songs)}` músicas da playlist *{playlist.name}*.  [{ctx.author.mention}]")
    await ctx.send(embed=embed)

    await PlaySong(client, ctx)


async def saveQueueToNewPlaylist(ctx, privacy, playlist_name):
    if privacy == None:
        privacy = 'public'

    try:
        if not PlaylistExists(ctx.guild.id, ctx.author.id, playlist_name):
            songs = takeSongsFromQueue()
            playlistQuery.create(ctx.guild.id, ctx.guild.name, ctx.author.id, playlist_name, f'{ctx.author.name}#{ctx.author.discriminator}', privacy, songs)
        else:
            await ctx.send("Já existe uma playlist sua com esse nome.")
            return
    except Exception as error:
        print(error)
        await ctx.send("Não foi possível criar uma playlist.")
        return

    await ctx.send("Playlist criada com sucesso!\n"
    f"\n> _Nome:_ `{playlist_name}`" 
    f"\n> _Propriedade:_ **{'Pública' if privacy == 'public' else 'Privado'}**"
    "\n\n_Essa playlist foi criada com as músicas da fila atual._"
        "\n_Você pode alterar a propriedade utilizando o comando `updateplaylist`._")




async def saveQueueToExistencePlaylist(ctx, playlist_name):
    try:
        if (playlist := Playlist.returnPlaylist(ctx.guild.id, ctx.author.id, playlist_name)):
            songs = takeSongsFromQueue()
            playlistQuery.addSongs(playlist, songs)
            if len(songs) > 1:
                embed = discord.Embed(color=ctx.guild.me.top_role.color,
                                title='**Adicionado a Playlist**',
                                description=f"`{len(songs)}` músicas em *{playlist.name}*.  [{ctx.author.mention}]")
            else:
                embed = discord.Embed(color=ctx.guild.me.top_role.color,
                                title='**Adicionado a Playlist**',
                                description=f'[{songs[0]["title"]}]({songs[0]["url"]}) em  *{playlist.name}*.  [{ctx.author.mention}]')
                
            await ctx.send(embed=embed)
        else:
            await ctx.send("Não existe uma playlist sua com esse nome.")
            
    except Exception as error:
        print(error)
        await ctx.send("Não foi possível adicionar músicas na playlist.")



def takeSongsFromQueue():
    queueSongs = []

    queueSongs.append({'title': f"{songPlayingNow['title']}", 'url': f"{songPlayingNow['url']}"})
    
    for song in queue:
        queueSongs.append({'title': f"{song['title']}", 'url': f"{song['url']}"})

    return queueSongs    


def isPlaylistPublic(ctx, playlist):
    public = True

    if ctx.author.id != playlist.owner_id: 
        if playlist.privacy == 'private':
            public = False

    return public


async def removeSongsFromIndex(ctx, playlist, index):
    # Caso index não case a string, vai dar erro  no método groupdict()
    index = re.match(r'^(?P<start>\d+)-(?P<end>\d+)$', index).groupdict()
    index['start'], index['end'] = int(index['start']), int(index['end'])

    if index and validateIndex(index):
        del playlist.songs[index['start']-1 : index['end']]
        playlistQuery.updatePlaylistSongs(playlist)
    else:
        await ctx.send("O index informado é inválido. Use `começo-fim`\n"
                       "*Exemplo:* **1-14; 12-16; ...")


def validateIndex(index):
    boolean = True
    
    if index['start'] > index['end']:
        boolean = False
    
    if index['start'] < 1:
        boolean = False

    return boolean


async def removeSongFromKeyword(client, ctx, playlist, search):
    prohibitedCharacters = ["_", "-", "/", "\\", "(", ")", "[", "]", "^", ",", ";", "{", "}", '"', "'",
                            '.', '<', '>']

    keywords = search.split(' ')
    keywords = [x.strip().lower() for x in keywords if not (x in prohibitedCharacters)]
    keywords = [re.sub(r"[-()/\[\]\\\"'*#/@;:<>{}`+=~|.!?,]", "", keyword) for keyword in keywords]

    # regex_expression example: ^.*?\bcat\b.*?\bmat\b.*?$ with ['cat', 'mat']
    regex_expression = '^'
    for keyword in keywords:
        regex_expression = regex_expression + f".*?\\b{keyword}\\b"
    regex_expression = regex_expression + '.*?$'

    matchedSong = None
    for song in playlist.songs:
        if (matchedTitle := re.match(r"{}".format(regex_expression), song['title'].lower())):
            matchedSong = song
            break

    if matchedSong:
        if await confirmFoundSong(client, ctx, matchedSong, playlist.name):
            playlist.songs.remove(matchedSong)
            playlistQuery.updatePlaylistSongs(playlist)

            message = await ctx.send("Música removida com sucesso!")
            await message.delete(delay=5)
    else:
        await ctx.send(f"Não foi possível achar nenhuma música correspondente em **{playlist.name}**.")

async def confirmFoundSong(client, ctx, song, playlist_name):
    
    confirmSongMessage = await ctx.send("A música achada foi **{}**\n"
                                        "da playlist  :arrow_right:  **{}**.\n"
                                        "\nDeseja confirmar?".format(song['title'], playlist_name))
    
    emojis = ['✅', '❌']
    await confirmSongMessage.add_reaction(emojis[0])
    await confirmSongMessage.add_reaction(emojis[1])

    def check(reaction, user):
        return reaction.message.id == confirmSongMessage.id \
            and user == ctx.author \
            and (str(reaction.emoji) == emojis[0]
            or str(reaction.emoji) == emojis[1])

    try:
        reaction, user = await client.wait_for('reaction_add', timeout=40, check=check)
        await confirmSongMessage.delete()
        
        if str(reaction.emoji) == emojis[0]:
            return True
        elif str(reaction.emoji) == emojis[1]:
            return False

    except asyncio.TimeoutError:
        error = await ctx.send("Você demorou muito.")
        await error.delete(delay=5)
        await confirmSongMessage.delete()
        return False


def PlaylistExists(guild_id, user_id, playlist_name):
    if playlistQuery.checkExistence(guild_id, user_id, playlist_name):
        return True
    else:
        return False

    
async def PlaylistCanBePlayed(ctx, playlist):
    playable = True

    if playlist.privacy == 'public' or ctx.author.id == playlist.owner_id:
        if len(playlist.songs) == 0:
            await ctx.send("Essa playlist não tem nenhuma música. Para adicionar músicas utilize:\n"
                            "\n`.addtoplaylist <nome da playlist> - <nome da música ou url>`")
            playable = False
    else:
        playable = False
        await ctx.send("Essa playlist está privada e você não é dono dela.")

    return playable
    

async def showSongsFromPlaylist(client, ctx, playlist):

    if isPlaylistPublic(ctx, playlist):
        if len(playlist.songs) > 0:
            page = 1

            message = await ctx.send(f"Mostrando músicas da playlist _{playlist.name}_")
            await asyncio.sleep(1.5)
            await constructSongsFromPlaylistMessage(ctx, playlist, message, page)
            
            emojis = ['⏫', '⬆️', '⬇️', '⏬']
            for emoji in emojis:
                await message.add_reaction(emoji)
            
            while True: 
                page = await waitPageFromPlaylistMessageChange(client, ctx, playlist, message, page)
                
                if page:
                    await constructSongsFromPlaylistMessage(ctx, playlist, message, page)
                else:
                    break
    else:
        await ctx.send(f"A **{playlist.name}** playlist é **privada**")


async def constructSongsFromPlaylistMessage(ctx, playlist, message, page):
    max_pages = returnMaxPlaylistPages(playlist.songs)

    page_list = playlist.songs[SONGS_PER_PAGE * (page - 1):SONGS_PER_PAGE * page]

    new_message = f"Página **{page}** de **{max_pages}** da playlist `{playlist.name}`\n\n"

    index = SONGS_PER_PAGE * (page - 1)
    for song in page_list:
        index = index + 1
        new_message = new_message + f'`[{index}]` **{song["title"]}**\n'

    await message.edit(content=new_message)


async def waitPageFromPlaylistMessageChange(client, ctx, playlist, message, page):
    emojis = ['⏫', '⬆️', '⬇️', '⏬']
    exceptions = []
    
    def check(reaction, user):
        return reaction.message.id == message.id \
            and user == ctx.author \
            and (str(reaction.emoji) == emojis[0]
            or str(reaction.emoji) == emojis[1]
            or str(reaction.emoji) == emojis[2]
            or str(reaction.emoji) == emojis[3])


    done, pending = await asyncio.wait(
        [client.wait_for('reaction_add', timeout=120, check=check), 
        client.wait_for('reaction_remove', timeout=120, check=check)], 
        return_when=asyncio.FIRST_COMPLETED)
    
    for task in done:
        exceptions.append(task.exception())

    for pending_task in pending:
        pending_task.cancel()

    if exceptions[0] == None:
        reaction = done.pop().result()[0]
        
        max_pages = returnMaxPlaylistPages(playlist.songs)

        if reaction.emoji == emojis[0]:
            page = FirstPage(page)
        elif reaction.emoji == emojis[1]:
            page = PageUp(page)
        elif reaction.emoji == emojis[2]:
            page = PageDown(page, max_pages)     
        elif reaction.emoji == emojis[3]:
            page = LastPage(page, max_pages)

        return page
    else:
        return False


def returnMaxPlaylistPages(playlistSongs):
    max_pages = len(playlistSongs) // SONGS_PER_PAGE
    if len(playlistSongs) % SONGS_PER_PAGE > 0:
        max_pages = max_pages + 1

    if max_pages == 0:
        max_pages = 1
    
    return max_pages


def FirstPage(page):
    page = 1
    return page


def PageUp(page):
    page -= 1
    if page <= 0:
        page = 1
    return page


def PageDown(page, max_pages):
    page += 1
    if page > max_pages:
        page = max_pages
    return page


def LastPage(page, max_pages):
    page = max_pages
    return page


def setup(client):
    client.add_cog(PlaylistCommands(client))
