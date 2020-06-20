import discord
import re
from .music import searchSongs, addTracksToQueue
from database import Database
from discord.ext import commands

database = Database('settings.db')


class Playlist(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def createplaylist(self, ctx, *args):
        Playlist.printA()

        if len(args) > 0:
            if args[0] == 'private' or args[0] == 'public':
                privacy = args[0]
                playlist_name = " ".join(args[1:len(args)])
            else:
                privacy = 'public'
                playlist_name = " ".join(args)
            
            try:
                if not database.playlistCheckExistence(ctx.guild.id, ctx.author.id, playlist_name):
                    database.playlistCreate(ctx.guild.id, ctx.guild.name, ctx.author.id, playlist_name, f'{ctx.author.name}#{ctx.author.discriminator}', privacy, "")
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
                if database.playlistCheckExistence(ctx.guild.id, ctx.author.id, playlist_name):
                    playlist_name = database.playlistReturnName(ctx.guild.id, ctx.author.id, playlist_name)
                    database.playlistUpdate(ctx.guild.id, ctx.author.id, playlist_name, privacy)
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


        if database.playlistCheckExistence(ctx.guild.id, ctx.author.id, playlist_name):
            playlist_name = database.playlistReturnName(ctx.guild.id, ctx.author.id, playlist_name)
            songs = await searchSongs(self.client, ctx, search)
            if songs:
                database.playlistAddTracks(ctx.guild.id, ctx.author.id, playlist_name, songs['items'])
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
    async def savequeuetoplaylist(self, ctx, *args):
        if args[0] == 'private' or args[0] == 'public':
            privacy = args[0]
            playlist_name = " ".join(args[1:len(args)])
        else:
            privacy = 'public'
            playlist_name = " ".join(args)
        
        print('\n', privacy)
        print(playlist_name)

    @commands.command()
    async def includeplaylist(self, ctx, *args):
        # Verifica os argumentos.
        if not len(args) < 4:
            for x in args:
                hyphen = re.match(r"^-$", x)
                if hyphen != None:
                    self_playlist_name = " ".join(args[0:(args.index(x))])

                    playlist = args[args.index(x)+1:]

                    if not len(playlist) == 0:
                        id = re.match(r"^<?@?([!&]?)([0-9]+)>?$", playlist[0])
                        if id != None and id.group(1) != '&':
                            userID = id.group(2)
                        else:
                            await ctx.send("O nome de usuário informado não é válido. Verifique novamente.")
                            return

                        tracks_option = re.match(r"^([0-9]*)-([0-9]*)$", args[-1])
                        if tracks_option != None:
                            tracks_start = tracks_option.group(1)
                            tracks_end = tracks_option.group(2)

                            if len(playlist) >= 3:
                                userID_playlist_name = " ".join(playlist[1:len(playlist)-1])
                            else:
                                await ctx.send("Não foi informado nenhuma playlist origem do usuário.")
                                return
                        else:
                            tracks_start = 0
                            tracks_end = -1

                            if len(playlist) >= 2:
                                userID_playlist_name = " ".join(playlist[1:len(playlist)])
                            else:
                                await ctx.send("Não foi informado nenhuma playlist origem do usuário.")
                                return    
        
                        break
                    else:
                        await ctx.send("Falta de argumentos. Use:\n\n"
                           "`.includeplaylist <playlist-name> - <id-user> <playlist-name-user> [tracks-option]`")
                        return

                # Caso eles vasculhou e nem achou '-' no último argumento. Ele executa:
                elif args.index(x) == len(args)-1:
                    await ctx.send('Comando inválido. Não esqueça do `-`, exemplo:\n'
                                '\n`.includeplaylist Favorite songs - @Joao Tryhard`')
                    return
        else:
            await ctx.send("Falta de argumentos. Use:\n\n"
                           "`.includeplaylist <playlist-name> - <id-user> <playlist-name-user> [tracks-option]`")
            return

        print('\n', args)
        print()
        print(self_playlist_name)
        print(userID)
        print(userID_playlist_name)
        print(tracks_start)
        print(tracks_end)
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

        playlists = database.listPlaylistsUser(ctx.guild.id, userID)

        msg = f"> Playlists do usuário <@{userID}>:\n"
        for item in playlists:
            msg = msg + f"\t**#{playlists.index(item)+1} -** {item[0]}\n"
        
        await ctx.send(msg)

    @commands.command()
    async def showplaylist(self, ctx, userID, playlist_name):
        pass

    @commands.command()
    async def loadplaylist(self, ctx, userID, playlist_name):
        pass

    @commands.command()
    async def deleteplaylist(self, ctx, *, playlist_name):
        if database.playlistCheckExistence(ctx.guild.id, ctx.author.id, playlist_name):
            playlist_name = database.playlistReturnName(ctx.guild.id, ctx.author.id, playlist_name)
            database.playlistDelete(ctx.guild.id, ctx.author.id, playlist_name)
            await ctx.send(f"Playlist `{playlist_name}` deletada com sucesso.")
        else:
            await ctx.send("Não existe uma playlist sua com esse nome.")

    @staticmethod
    def addPlaylistTracksToQueue(client, ctx, tracks):
        pass

    @staticmethod
    def printA():
        print('A-A-A-A-A')

def setup(client):
    client.add_cog(Playlist(client))