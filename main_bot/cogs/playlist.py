import discord
import re
import ast
from .music import songPlayingNow, queue
from .music import searchSongs, addSongsToQueue, PlaySong
from database import PlaylistDatabase
from discord.ext import commands

playlistQuery = PlaylistDatabase('guilds_database.db')


class Playlist(commands.Cog):

    def __init__(self, client):
        self.client = client

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
                if not playlistQuery.checkExistence(ctx.guild.id, ctx.author.id, playlist_name):
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
                if playlistQuery.checkExistence(ctx.guild.id, ctx.author.id, playlist_name):
                    playlist_name = playlistQuery.returnName(ctx.guild.id, ctx.author.id, playlist_name)
                    playlistQuery.update(ctx.guild.id, ctx.author.id, playlist_name, privacy)
                    await ctx.send("Playlist atualizada com sucesso!\n"
                        f"\n> _Nome:_ `{playlist_name}`" 
                        f"\n> _Propriedade:_ **{'Pública' if privacy == 'public' else 'Privado'}**")
                else:
                    await ctx.send("Não existe uma playlist sua com esse nome.")
            except Exception as error:
                print(error)
                await ctx.send("Não foi possível atualizar sua playlist.")
        else:
            await ctx.send("Você não informou o nome da playlist.")

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


        if playlistQuery.checkExistence(ctx.guild.id, ctx.author.id, playlist_name):
            playlist_name = playlistQuery.returnName(ctx.guild.id, ctx.author.id, playlist_name)
            songs = await searchSongs(self.client, ctx, search)
            if songs:
                playlistQuery.addSongs(ctx.guild.id, ctx.author.id, playlist_name, songs['items'])
                if songs['playlist']:
                    embed = discord.Embed(color=ctx.guild.me.top_role.color,
                                    title='**Adicionado a Playlist**',
                                    description=f"`{len(songs['items'])}` músicas em *{playlist_name}*.  [{ctx.author.mention}]")
                else:
                    embed = discord.Embed(color=ctx.guild.me.top_role.color,
                                    title='**Adicionado a Playlist**',
                                    description=f'[{songs["items"][0]["title"]}]({songs["items"][0]["url"]}) em  *{playlist_name}*.  [{ctx.author.mention}]')
                    
                await ctx.send(embed=embed)
            else:
                await ctx.send("Algum erro aconteceu.")
        else:
            await ctx.send("Não existe uma playlist sua com esse nome.")

    @commands.command()
    async def savequeuetoplaylist(self, ctx, *, args):
        regex = re.match(r'^(add|new) ((public|private) )?(.+)$', args)
        
        if regex:
            if songPlayingNow:
                privacy = regex.group(3)
                playlist_name = regex.group(4)

                if regex.group(1) == 'new':
                    await Playlist.saveQueueToNewPlaylist(ctx, privacy, playlist_name)
                elif regex.group(1) == 'add':
                    await Playlist.saveQueueToExistencePlaylist(ctx, playlist_name)
            else:
                await ctx.send("Não existe nenhuma música na fila de reprodução.")
        else:
            await ctx.send("Argumento inválido. Use: \n\n"
                           "`.savequeuetoplaylist <add|new> [public|private] <playlist-name>`")

    @commands.command()
    async def includeplaylist(self, ctx, *args):
        # Verifica os argumentos.
        if not len(args) < 4:
            for x in args:
                hyphen = re.match(r"^-$", x)
                if hyphen != None:
                    self_playlist_name = " ".join(args[0:(args.index(x))])

                    afterHyphen = args[args.index(x)+1:]

                    if len(afterHyphen) != 0:
                        id = re.match(r"^<?@?([!&]?)([0-9]+)>?$", afterHyphen[0])
                        if id != None and id.group(1) != '&':
                            userID = id.group(2)
                        else:
                            await ctx.send("O nome de usuário informado não é válido. Verifique novamente.")
                            return

                        songs_interval = re.match(r"^([0-9]*)-([0-9]*)$", args[-1])
                        if songs_interval != None:
                            songs_start = songs_interval.group(1)
                            songs_end = songs_interval.group(2)

                            if len(afterHyphen) >= 3:
                                userID_playlist_name = " ".join(afterHyphen[1:len(afterHyphen)-1])
                            else:
                                await ctx.send("Não foi informado nenhuma playlist origem do usuário.")
                                return
                        else:
                            songs_start = 0
                            songs_end = -1

                            if len(afterHyphen) >= 2:
                                userID_playlist_name = " ".join(afterHyphen[1:len(afterHyphen)])
                            else:
                                await ctx.send("Não foi informado nenhuma playlist origem do usuário.")
                                return    
        
                        break
                    else:
                        await ctx.send("Falta de argumentos. Use:\n\n"
                           "`.includeplaylist <playlist-name> - <id-user> <playlist-name-user> [songs-interval]`")
                        return

                # Caso eles vasculhou e nem achou '-' no último argumento. Ele executa:
                elif args.index(x) == len(args)-1:
                    await ctx.send('Comando inválido. Não esqueça do `-`, exemplo:\n'
                                '\n`.includeplaylist Favorite songs - @Joao Tryhard`')
                    return
        else:
            await ctx.send("Falta de argumentos. Use:\n\n"
                           "`.includeplaylist <playlist-name> - <id-user> <playlist-name-user> [songs-interval]`")
            return

        print('\n', args)
        print()
        print(self_playlist_name)
        print(userID)
        print(userID_playlist_name)
        print(songs_start)
        print(songs_end)
        print(ctx.message.raw_mentions)

    @commands.command()
    async def removefromplaylist(self, ctx, playlist_name, search):
        pass

    @commands.command()
    async def seeallplaylist(self, ctx, *, userID):

        id = re.match(r"^<?@?([!&]?)([0-9]+)>?$", userID)
        if id != None and id.group(1) != '&':
            userID = id.group(2)
        else:
            await ctx.send("O _ID_ de usuário informado não é válido. Verifique novamente.")
            return

        userPlaylists = playlistQuery.GetUserPlaylists(ctx.guild.id, userID)

        msg = f"> Playlists do usuário <@{userID}>:\n"
        for item in userPlaylists:
            msg = msg + f"\t**#{userPlaylists.index(item)+1} -** {item[0]}\t_(Songs: {item[1]})_\n"
        
        await ctx.send(msg)

    @commands.command()
    async def showplaylist(self, ctx, userID, playlist_name):
        pass

    @commands.command()
    async def loadplaylist(self, ctx, userID, *, playlist_name):
        id = re.match(r"^<?@?([!&]?)([0-9]+)>?$", userID)
        if id != None and id.group(1) != '&':
            userID = id.group(2)
        else:
            await ctx.send("O _ID_ de usuário informado não é válido. Verifique novamente.")
            return

        if playlistQuery.checkExistence(ctx.guild.id, userID, playlist_name):
            playlist_name = playlistQuery.returnName(ctx.guild.id, userID, playlist_name)
        else:
            await ctx.send(f"Não existe uma playlist do usuário <@{userID}> com esse nome.")
        
        songsResult = playlistQuery.returnSongs(ctx.guild.id, userID, playlist_name)
        if songsResult['privacy'] == 'public' or ctx.author.id == int(userID):
            songs = ast.literal_eval(songsResult['songs'])
            
            if len(songs) > 0:
                await Playlist.addPlaylistSongsToQueue(self.client, ctx, songs, playlist_name)
            else:
                await ctx.send("Essa playlist não tem nenhuma música. Para adicionar músicas utilize:\n"
                               "\n`.addtoplaylist <nome da playlist> - <nome da música ou url>`" 
                )
                return
        else:
            await ctx.send("Essa playlist está privada e você não é dono dela.")

    @commands.command()
    async def deleteplaylist(self, ctx, *, playlist_name):
        if playlistQuery.checkExistence(ctx.guild.id, ctx.author.id, playlist_name):
            playlist_name = playlistQuery.returnName(ctx.guild.id, ctx.author.id, playlist_name)
            playlistQuery.delete(ctx.guild.id, ctx.author.id, playlist_name)
            await ctx.send(f"Playlist `{playlist_name}` deletada com sucesso.")
        else:
            await ctx.send("Não existe uma playlist sua com esse nome.")

    @staticmethod
    async def addPlaylistSongsToQueue(client, ctx, songs, playlist_name):

        await addSongsToQueue(client, ctx, songs)

        embed = discord.Embed(color=ctx.guild.me.top_role.color,
                            title='**Adicionado a Fila**',
                            description=f"`{len(songs)}` músicas da playlist *{playlist_name}*.  [{ctx.author.mention}]")
        await ctx.send(embed=embed)
  
        await PlaySong(client, ctx)

    @staticmethod
    async def saveQueueToNewPlaylist(ctx, privacy, playlist_name):
        if privacy == None:
            privacy = 'public'

        try:
            if not playlistQuery.checkExistence(ctx.guild.id, ctx.author.id, playlist_name):
                songs = []
                songs.append({'title': f"{songPlayingNow['title']}", 'url': f"{songPlayingNow['url']}"})
                for song in queue:
                    songs.append({'title': f"{song['title']}", 'url': f"{song['url']}"})

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

    @staticmethod
    async def saveQueueToExistencePlaylist(ctx, playlist_name):
        try:
            if playlistQuery.checkExistence(ctx.guild.id, ctx.author.id, playlist_name):
                playlist_name = playlistQuery.returnName(ctx.guild.id, ctx.author.id, playlist_name)
                
                songs = []
                songs.append({'title': f"{songPlayingNow['title']}", 'url': f"{songPlayingNow['url']}"})
                for song in queue:
                    songs.append({'title': f"{song['title']}", 'url': f"{song['url']}"})

                playlistQuery.addSongs(ctx.guild.id, ctx.author.id, playlist_name, songs)
            else:
                await ctx.send("Não existe uma playlist sua com esse nome.")
                return
        except Exception as error:
            print(error)
            await ctx.send("Não foi possível adicionar músicas na playlist.")
            return

        if len(songs) > 1:
            embed = discord.Embed(color=ctx.guild.me.top_role.color,
                            title='**Adicionado a Playlist**',
                            description=f"`{len(songs)}` músicas em *{playlist_name}*.  [{ctx.author.mention}]")
        else:
            embed = discord.Embed(color=ctx.guild.me.top_role.color,
                            title='**Adicionado a Playlist**',
                            description=f'[{songs[0]["title"]}]({songs[0]["url"]}) em  *{playlist_name}*.  [{ctx.author.mention}]')
            
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Playlist(client))