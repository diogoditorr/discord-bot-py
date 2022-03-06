
import os
from typing import Literal, TypeVar

import discord
from discord.ext import commands

from packages.cogs.tasks import Tasks
from packages.database.database import Database

def get_client(config: dict) -> commands.Bot:
    first_start = True

    intents = discord.Intents.default()
    intents.members = True
    client = commands.Bot(command_prefix=get_prefix, intents=intents)

    @client.event
    async def on_ready():
        print(f'Bot {client.user} is ready')

        game = discord.Game("Made by: Diego")
        await client.change_presence(status=discord.Status.online, activity=game)

        # Tasks.change_status.start()

        load_cogs()

        await Database.create()

    def load_cogs():
        nonlocal first_start
        if first_start:
            for filename in os.listdir(config["cogs_path"]):
                if filename.endswith('.py'):
                    client.load_extension(
                        f'{config["cogs_module_name"]}.{filename[:-3]}')
            client.load_extension('jishaku')

            first_start = False

    @client.command()
    async def load(ctx, extension):
        if await permsVerify(ctx):
            await ctx.send(f'Ativando o arquivo "{extension}.py".')
            client.load_extension(f'{config["cogs_module_name"]}.{extension}')
            await ctx.send(f'Ativado o arquivo "{extension}.py".')

    @client.command()
    async def unload(ctx, extension):
        if await permsVerify(ctx):
            await ctx.send(f'Desativando o arquivo "{extension}.py".')
            client.unload_extension(
                f'{config["cogs_module_name"]}.{extension}')
            await ctx.send(f'Desativado o arquivo "{extension}.py".')

    @client.command()
    async def reload(ctx, extension):
        if await permsVerify(ctx):
            await ctx.send(f'Recarregando o arquivo "{extension}.py".')
            client.reload_extension(
                f'{config["cogs_module_name"]}.{extension}')
            await ctx.send(f'Recarregado o arquivo "{extension}.py".')

    @client.command()
    async def reload_all(ctx):
        if await permsVerify(ctx):
            await ctx.send(f'Recarregando todos os arquivos.')

            for filename_unload in os.listdir(config["cogs_path"]):
                if filename_unload.endswith('.py'):
                    client.reload_extension(
                        f'{config["cogs_module_name"]}.{filename_unload[:-3]}')

            await ctx.send(f'Todos os módulos foram recarregados.')

    @client.command()
    async def shutdown(ctx):
        if ctx.message.author.id == ctx.guild.owner.id:
            print("shutdown")

            try:
                await client.close()
            except:
                print("EnvironmentError")
                client.clear()
            else:
                await ctx.send("You do not own this bot!")

    async def permsVerify(context):
        if context.message.author.id == context.guild.owner_id:
            return True
        else:
            await context.send("Você não tem permissão para usar essa comando.")
            return False

    return client

async def get_prefix(bot, message: discord.Message):
    database = await Database.connect()

    guild: discord.Guild = message.guild
    prefix = await database.prefix.get(guild)

    return prefix