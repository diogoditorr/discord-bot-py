import os
import sys
from pathlib import Path

from dotenv import dotenv_values

from client_config import get_client

# Load environment variables from .env file
env_path = Path(os.path.dirname(__file__)).absolute() / '.env'
if not env_path.exists():
    print("Could not find '.env' file. Verify if you have in your directory.")
    exit()

# Constants
ENV = dotenv_values(dotenv_path=env_path)
PWD = Path(os.path.dirname(__file__))

# --------Configuration--------
config = {
    "cogs_path": PWD.joinpath('packages', 'cogs'),
    "cogs_module_name": 'packages.cogs'
}

client = get_client(config)

# The token is necessary to connect the client with the API
# on discord and use the bot.
client.run(ENV['BOT_TOKEN'])
