![discord](https://user-images.githubusercontent.com/35296262/89131859-45fd0d80-d4e6-11ea-8e9f-5faad231d10a.png)

### Language
* [Português Brasil](./README-pt-br.md)

# 🤖 discord-bot-py
This bot has commands focused on **music**, like *play, pause, repeat, next, stop...*.

This version uses [Lavalink](https://github.com/freyacodes/Lavalink). Readme of previous version with youtube-dl [here](docs/README-youtube-dl.md) (deprecated)

## ⚙ How to run the Bot:

* Cloning the project:
```bash
$ git clone https://github.com/diogoditorr/discord-bot-py

# Enter the main_bot folder
$ cd discord-bot-py/main_bot
```

* Install dependencies with pipenv:
```bash
$ pipenv install
```

* Create **.env** from the example file. Do not forget to set your **BOT_TOKEN**.

### **Running Lavalink**

* Create the **application.yml** file from example.
* Download Lavalink.jar [here](https://github.com/freyacodes/Lavalink/releases) or use this command inside the _main_bot_ folder:

```bash
$ curl -s https://api.github.com/repos/freyacodes/Lavalink/releases/latest \
| grep "Lavalink.jar" \
| cut -d : -f 2,3 \
| tr -d \" \
| wget -qi -
```

* Run in a new terminal
```bash
$ java -jar Lavalink.jar
```

> More information in [Lavalink repository](https://github.com/freyacodes/Lavalink)

### **Running the Bot**
```bash
$ python bot.py
```


## 🎶 All Commands
* [Click here](./docs/commands-en.md)

## 📝 License
This project is under the MIT license. See the [LICENSE](./LICENSE) for more information.
