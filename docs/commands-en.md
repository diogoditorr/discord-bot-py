# Table Of Content:

- [Important](#important):
- [Music commands](#music-commands):
  - [join](#join)
  - [leave](#leave)
  - [play](#play)
  - [playnext](#playnext)
  - [next](#next)
  - [pause](#pause)
  - [resume](#resume)
  - [queue](#queue)
  - [repeat](#repeat)
  - [shuffle](#shuffle)
  - [stop](#stop)
  - [volume](#volume)
- [Permission commands](#permission-commands)
  - [admin](#admin)
  - [dj](#dj)
  - [user](#user)
- [Others](#others)

# Important

- Between `< >` : **Mandatory**
- Between `[ ]` : **Opcional**
- The commands are displayed in _Portuguese Brazil_ (my country).

# Music commands

### [join](#table-of-content)

`<prefix>join`

Join a Voice Channel. If you are not in one, the bot will warn you.

### [leave](#table-of-content)

`<prefix>leave`

Leave the Voice Channel where the bot is connected.

### [play](#table-of-content)

`<prefix>play <url or keyword>`

Search a song/playlist on Youtube to play or add in queue.

### [playnext](#table-of-content)

`<prefix>play <url or keyword>`

Search a song/playlist on Youtube to play next in the queue. If it is a playlist, all the songs will be played in sequence.

### [next](#table-of-content)

`<prefix>next`

Go to the next song in the queue. If it is repeating the queue, it does not delete the current song.

### [pause](#table-of-content)

`<prefix>pause`

Pause the player.

### [resume](#table-of-content)

`<prefix>resume`

Resume/unpause the player.

#### Aliases:

- _unpause_

### [queue](#table-of-content)

`<prefix>queue [page]`

Show the the songs of the queue (10 per page).

#### Aliases:

- _q_

### [repeat](#table-of-content)

`<prefix>repeat <single|all|off>`

Repeats: a single song or all the songs from queue.

### [shuffle](#table-of-content)

`<prefix>shuffle`

Shuffle the queue.

### [stop](#table-of-content)

`<prefix>stop`

Clean the queue and stop the player.

### [volume](#table-of-content)

`<prefix>volume [0 to 1000]`

Set the volume of the player or show the current volume.

# Permission commands

Configure members and roles to give access to specific commands.

**Commands for each role:**

- **User:** play, playnext, queue, next, join, leave.
- **Dj:** _everything from user and_, pause, resume, repeat, shuffle, volume, stop.
- **Admin:** _everything._

### [admin](#table-of-content)

`<prefix>admin <add|del|list>`

### [dj](#table-of-content)

`<prefix>dj <add|del|list>`

### [user](#table-of-content)

`<prefix>user <add|del|list>`

# Others

### [prefix](#table-of-content)

`<prefix>|@botMentioned prefix [new prefix]`

Show the current prefix of the server or set a new prefix.

**Default prefix: .**
