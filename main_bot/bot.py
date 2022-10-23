import os
import sys
from pathlib import Path

import discord
from dotenv import dotenv_values

from packages.bot_client import BotClient

# Load environment variables from .env file
env_path = Path(os.path.dirname(__file__)).absolute() / '.env'
if not env_path.exists():
    print("Could not find '.env' file. Verify if you have in your directory.")
    exit()

# Constants
ENV = dotenv_values(dotenv_path=env_path)
PWD = Path(os.path.dirname(__file__))

# --------Configuration--------
# config = {
#     "cogs_path": PWD.joinpath('packages', 'cogs'),
#     "cogs_module_name": 'packages.cogs'
# }

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = BotClient(intents=intents)

# The token is necessary to connect the client with the API
# on discord and use the bot.
client.run(ENV['BOT_TOKEN'])
