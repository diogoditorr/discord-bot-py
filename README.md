# discord-bot-py
Working with the Discord.py library

# How to run the Bot:

You need first create a `settings.py` inside the `main_bot` folder with the following code:

```
def bot_token():
    return 'Your bot Token'

def prefix():.
    return 'Prefix for the bot. Can be . ? / - whatever '

def youtube_api_key():
    return 'Your Youtube API Key. If you don't have one, you need to create. It's free.'
```

## Requirements (Python packages. It's also in Pipfile)
* **Youtube-dl** - I recommend install as in your virtual environment as in your python PATH using `pip install youtube-dl`
* **Discord.py**
* **google-api-python-client**

## External Requirements
* **FFmpeg** - It converts the audio to play on Discord. Download and place the directory of the folder in your Enviroment Variables.

After you've done the things above. Just run `python ./main_bot/bot.py`
