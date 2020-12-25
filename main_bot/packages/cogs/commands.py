import discord
import time
import random
from discord.ext import commands

from ..database.database import Database

def permsVerify(context):
    perm = ['Admins']
    roles = [x.name for x in context.author.roles]
    print(roles)

    for x in range(0, len(perm)):
        if roles.__contains__(perm[x]):
            return True

    return False


class Commands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def prefix(self, ctx, *args):
        database = await Database.connect()

        if not args:
            await ctx.send(f"O prefixo para esse servidor é `{await database.prefix.get(ctx.guild)}`")
        else:
            prefix = " ".join(args)

            await database.prefix.update(ctx.guild, prefix)
            await ctx.send("O prefixo do servidor mudou!\n"
                          f"Utilize qualquer comando agora com o prefixo:  `{prefix}`")


    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(self.client.latency * 1000)}ms {ctx.author.mention}')

    @commands.command(aliases=['8ball', 'test'])
    async def _8ball(self, ctx, *, question):
        """
            Manda uma pergunta para o bot e receberá uma resposta sendo: sim, não,
            talvez, ou outra mensagem.

            Tente você mesmo ^^

        :param ctx: Contexto da mensagem
        :param question: Pergunta para o bot
        :return: Uma resposta
        """
        responses = [
            'É correto dizer sim.',
            'Decidamente sim.',
            'Sem dúvidas',
            'Sim - definitivamente.',
            'Pelo meus cálculos, sim.',
            'Pelo que eu vejo, sim',
            'Provavelmente',
            'Parece ótimo',
            'Sim',
            'Isso indica um sim',
            'Melhor não contar agora',
            'Talvez',
            'Responder nebuloso, tente novamente',
            'Pergunte novamente mais tarde.',
            'Não há como prever agora.',
            'Concentre-se e pergunte novamente.',
            'Não conte com isso.',
            'Minha resposta é não.',
            'Minhas fontes dizem não.',
            'Não parece ser bom.',
            'Muito duvidoso.'
        ]
        await ctx.send(f'Question: {question}\nAnswer: {random.choice(responses)}')

    @commands.command()
    async def clear(self, ctx, amount=5):
        if permsVerify(ctx):
            await ctx.send(f'Certo! Limpando as últimas **{amount}** mensagens!')
            time.sleep(3)
            await ctx.channel.purge(limit=(amount + 2))
        else:
            await ctx.send(
                f"Você não tem permisão para usar esse comando.")

    @commands.command()
    async def helpa(self, ctx):
        embed = discord.Embed(title="Music Settings", description="Testing WebHook", color=0x740af5)
        embed.add_field(name="**>** Campo 1", value="Descrição...", inline=True)
        embed.add_field(name="**>** Campo 2", value="Alguma coisa.", inline=False)
        embed.add_field(name="**>** Bot Criado Pelo:", value="Diego **<3**", inline=True)
        embed.set_footer(text="Este bot foi criado utilizando a linguagem Python")
        await ctx.send(embed=embed)

    # The "*" means that every paramenter after 'member' will be in one sigle parameter
    # after it, the "reason".
    # e.g. .kick Diego Você fez uma coisa muito má
    #
    # "Você fez uma coisa muito má" will be storage in the 'reason' keyword parameter.
    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if permsVerify(ctx):
            await ctx.send(f"Expulsando o usuário {member.mention} do servidor."
                           f'\n\n**Motivo:**  *"{reason}"*')
            return
            await member.kick(reason=reason)
        else:
            await ctx.send(
                f"Você não tem permisão para usar esse comando.\nFale com o dono do servidor {ctx.guild.owner.mention}.")

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if permsVerify(ctx):
            await ctx.send(f"Banindo o usuário {member.mention} do servidor."
                           f'\n\n**Motivo:**  *"{reason}"*')
            return
            await member.ban(reason=reason)
        else:
            await ctx.send(
                f"Você não tem permisão para usar esse comando.\nFale com o dono do servidor {ctx.guild.owner.mention}.")

    @commands.command()
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        print(banned_users)
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Desbanido {user.name}#{user.discriminator}')
                return

    @commands.command()
    async def x1(self, ctx, member: discord.Member, *, msg):
        await ctx.send(
            f'**VEM PRO X1 LIXO!!! {member.mention}** '
            f'\nO jogador {ctx.author.mention} te desafiou pro **x1 lixo** com a seguinte mensagem: '
            f'\n\n *"{msg}"* '
            f'\n\n**Vai arregar?!?!**')


def setup(client):
    client.add_cog(Commands(client))
