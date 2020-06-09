import discord
import os
import sys
from discord.ext import commands

# Adiciona em 'sys.path' o diretório da pasta 'discord-bot-py' para não dar erro de
# exportação de módulo em main_bot/cogs/events --> 'from main_bot.cogs.tasks import Tasks'
import re
path = re.match(r"(?P<path>.+)\\", sys.path[0])
sys.path.append(f"{path['path']}")
# ---------------------------------------------------

# Importa as configurações
import settings

bot_token = settings.bot_token()
prefix = settings.prefix()

client = commands.Bot(command_prefix=prefix)

cogs_PATH = f'{sys.path[0]}\cogs'

@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Ativando o arquivo "{extension}.py"')


@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.send(f'Desativando o arquivo "{extension}.py"')


@client.command()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Recarregando o arquivo "{extension}.py"')

for filename in os.listdir(cogs_PATH):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(bot_token)
