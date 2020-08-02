
### Language
* [Português Brasil]()

# 🤖 discord-bot-py
Working with the Discord.py library.

This bot has commands focused on **music**. It has main commands like *play, pause, repeat, next, stop...*, and commands to create a playlist in your server, stored in a database **(sqlite3)**.

## ⚙ How to run the Bot:

You need first create a `settings.py` inside the `main_bot` folder with the following code:

```python
def bot_token():
    return 'Your bot Token'

def prefix():.
    return 'Prefix for the bot. Can be . ? / - whatever '

def youtube_api_key():
    return 'Your Youtube API Key. If you don't have one, you need to create. It's free.'
```

#### Requirements (Python packages. It's also in Pipfile):
* [**Discord.py**](https://github.com/Rapptz/discord.py) 
* [**Youtube-dl**](https://github.com/ytdl-org/youtube-dl) - I recommend install as in your virtual environment as in your python PATH using `pip install youtube-dl`
* [**google-api-python-client**](https://github.com/googleapis/google-api-python-client) - Module to use Youtube Data API. 

#### External Requirements:
* [**FFmpeg**](https://ffmpeg.org/) - It converts the audio to play on Discord. Download and place the directory of the folder in your Enviroment Variables.

After you've done the things above. Just run `/main_bot/bot.py` file.

## 🎶 All Commands
* [Click here]()

## 📝 License
This project is under the MIT license. See the [LICENSE](./LICENSE) for more information.
