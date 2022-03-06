import discord
import os
import sys
import site
from discord.ext import commands

# Import of settings
import settings

os.chdir(os.path.dirname(os.path.abspath(__file__)))

bot_token = settings.bot_token()
prefix = settings.prefix()

client = commands.Bot(command_prefix=prefix)

cogs_PATH = f'{sys.path[0]}\cogs'

async def permsVerify(context):
    if context.message.author.id == context.guild.owner.id:
        return True
    else:
        await context.send("Você não tem permissão para usar essa comando.")
        return False


@client.command()
async def load(ctx, extension):
    if await permsVerify(ctx):
        await ctx.send(f'Ativando o arquivo "{extension}.py".')
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Ativado o arquivo "{extension}.py".')


@client.command()
async def unload(ctx, extension):
    if await permsVerify(ctx):
        await ctx.send(f'Desativando o arquivo "{extension}.py".')
        client.unload_extension(f'cogs.{extension}')
        await ctx.send(f'Desativado o arquivo "{extension}.py".')


@client.command()
async def reload(ctx, extension):
    if await permsVerify(ctx):
        await ctx.send(f'Recarregando o arquivo "{extension}.py".')
        client.reload_extension(f'cogs.{extension}')
        await ctx.send(f'Recarregado o arquivo "{extension}.py".')


@client.command()
async def reload_all(ctx):
    if await permsVerify(ctx):
        await ctx.send(f'Recarregando todos os arquivos.')

        for filename_unload in os.listdir(cogs_PATH):
            if filename_unload.endswith('.py'):
                client.reload_extension(f'cogs.{filename_unload[:-3]}')

        await ctx.send(f'Todos os módulos foram recarregados.')

for filename in os.listdir(cogs_PATH):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
client.load_extension('jishaku')

# The token is necessary to connect the client with the API
# on discord and use the bot.

client.run(bot_token)
