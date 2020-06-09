import discord
import asyncio
from discord.ext import commands
import logging

# Creates the 'discord.log' file
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Client is the connection to Discord
client = commands.Bot(command_prefix='.')

print(discord.__version__)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    game = discord.Game("Using for Test")
    await client.change_presence(status=discord.Status.online, activity=game)
    print([channel.name for channel in client.get_all_channels()])
    print([member.name for member in client.get_all_members()])


@client.event
async def on_message(message):
    # 'author' is on the class discord.Member
    print(message.content)
    print(f' {message.author} (Cargos):', [x.name for x in message.author.roles])
    print(f' {message.author}: '
          "Pertence a Admins" if 'Admins' in [x.name for x in message.author.roles] else "Não pertence.")
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    await client.process_commands(message)


@client.event
async def on_reaction_add(reaction, user):
    channel = reaction.message.channel
    await channel.send('{} has added {} to the message: {}'.format(user.name, reaction.emoji, reaction.message.content))
    print('oi')
# '1️⃣'
# '2️⃣'
# '3️⃣'
# '4️⃣'

@client.event
async def on_reaction_remove(reaction, user):
    channel = reaction.message.channel
    await channel.send('{} has removed {} from message: {}'.format(user.name, reaction.emoji, reaction.message.content))
    m = await channel.send('Oi')
    print(m)


@client.command()
async def test(ctx):
    message = await ctx.send("Testando mensagem de reação.")
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
        reaction, user = await client.wait_for('reaction_add', timeout=10, check=check)
        await ctx.send("**Tudo pronto!**")
        await message.delete()
    except asyncio.TimeoutError:
        await ctx.send("Você demorou muito.")
        return





client.run('NzA0NzI0OTc3NjI2MTIwMjEz.Xsx-sw.S4Ub_XcTbvR6wAyUSxrqbtoGAVA')
