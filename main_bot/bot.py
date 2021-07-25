import os
from pathlib import Path

try:
    import settings
except ImportError:
    print("Could not import settings. Verify if you have in your directory.")
    exit()

from client_config import get_client

# --------Configuration--------
PWD = Path(os.path.dirname(__file__))
BOT_TOKEN = settings.bot_token()

config = {
    "cogs_path": PWD.joinpath('packages', 'cogs'),
    "cogs_module_name": 'packages.cogs'
}

client = get_client(config)
# print("CWD:", os.getcwd())
# print("FILE:", __file__)
# print("PWD", PWD)
# print("COGS_PATH:", COGS_PATH)
# print("Files:", os.listdir(COGS_PATH))
# -----------------------------

# The token is necessary to connect the client with the API
# on discord and use the bot.
client.run(BOT_TOKEN)
