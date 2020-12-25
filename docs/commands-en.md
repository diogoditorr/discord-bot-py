## Table Of Content:
* [Important](#important):
* [Music commands](#music-commands):
    * [join](#join)              
    * [leave](#leave)
    * [play](#play)
    * [playnext](#playnext)            
    * [next](#next)               
    * [pause](#pause)                       
    * [resume](#resume)              
    * [queue](#queue)               
    * [repeat](#repeat)              
    * [shuffle](#shuffle)                        
    * [stop](#stop) 
* [Playlist commands](#playlist-commands):
    * [createplaylist](#createplaylist)
    * [updateplaylist](#updateplaylist)
    * [deleteplaylist](#deleteplaylist)      
    * [clearplaylist](#clearplaylist)       
    * [addtoplaylist](#addtoplaylist)       
    * [removefromplaylist](#removefromplaylist)  
    * [includeplaylist](#includeplaylist)     
    * [savequeuetoplaylist](#savequeuetoplaylist) 
    * [seeallplaylist](#seeallplaylist)      
    * [showplaylist](#showplaylist)        
    * [loadplaylist](#loadplaylist)        

## Important
* Between `< >` : **Mandatory**
* Between `[ ]` : **Opcional**
* The commands are displayed in *Portuguese Brazil* (my country). An option to change will be available later.

## Music commands

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
* *unpause*

### [queue](#table-of-content)
`<prefix>queue [page]`

Show the the songs of the queue (10 per page).

#### Aliases:
* *q*

### [repeat](#table-of-content)
`<prefix>repeat <single|all|off>`

Repeats: a single song or all the songs from queue.

### [shuffle](#table-of-content)
`<prefix>shuffle`

Shuffle the queue.

### [stop](#table-of-content)
`<prefix>stop`

Clean the queue and stop the player.

## Playlist commands

### [createplaylist](#table-of-content)
`<prefix>createplaylist [privacy: private|public] <playlist-name>`

Create a new playlist in a database which you can add songs and play them later. Every playlist is *public* by default.

#### Examples
```
.createplaylist My favorite Songs
.createplaylist public My favorite Songs
.createplaylist private My favorite Songs
```

### [updateplaylist](#table-of-content)
`<prefix>updateplaylist [public|private] <playlist-name>`

Change your playlist privacy to public or private. If no one is specified, public is referenced. 

### [deleteplaylist](#table-of-content)
`<prefix>deleteplaylist <playlist-name>`

Delete the playlist specified.

### [clearplaylist](#table-of-content)
`<prefix>clearplaylist <playlist-name>`

Clean all the songs in the playlist.

### [addtoplaylist](#table-of-content)
`<prefix>addtoplaylist <playlist-name> - <url or keyword>`

Search a song/playlist on Youtube to add it to the playlist. It works the same way as **play** command.
* The character "**-**" is **required!**

### [removefromplaylist](#table-of-content)
`<prefix>removefromplaylist <playlist-name> index|keyword <index or keyword>`

Remove song/songs from your playlist. You can remove using index (numbers) or keyword (name of the song).

#### Examples
```
.removefromplaylist My favorite Songs index 1-14 (delete the 1st until the 14th song)
.removefromplaylist My favorite Songs index 3-4
.removefromplaylist My favorite Songs keyword Legend - The Score
```

### [includeplaylist](#table-of-content)
`<prefix>includeplaylist <your-playlist-name> - <user id or @user> <user-playlist-name> [songs-interval]`

A command to export songs from a playlist to your playlist. 
* You can specify which songs you want to export. <br>
* You can export your own playlist to another playlist you created.
* The character "**-**" is **required!**

#### Examples
```
.includeplaylist My favorite Songs - @Chris Chris' playlist
.includeplaylist My favorite Songs - @Chris Chris' playlist 3-54
.includeplaylist My favorite Songs - @Diego My favorite Songs (2)
.includeplaylist My favorite Songs - @Diego My favorite Songs (2) 1-4
```

### [savequeuetoplaylist](#table-of-content)
`<prefix>savequeuetoplaylist <add|new> [public|private] <playlist-name>`

Take the songs playing in the queue and add to your or create a new playlist.

#### Examples
```
.savequeuetoplaylist add My favorite Songs
.savequeuetoplaylist new Queue Songs
.savequeuetoplaylist new private Queue Songs
```

### [seeallplaylist](#table-of-content)
`<prefix>seeallplaylist <user id or @user>`

Sends a message with all the playlists and the size of each one of a user.
 
### [showplaylist](#table-of-content)
`<prefix>showplaylist <user id or @user> <playlist name>`

Sends a message to see all the songs from a playlist. The access is denied if is private (unless is *your* playlist). You can navigate through pages using emojis.

### [loadplaylist](#table-of-content)
`<prefix>loadplaylist <user id or @user> <playlist-name> [songs-interval]`

Load the songs from a playlist to play in queue.

#### Examples
```
.loadplaylist @Diego My favorite Songs
.loadplaylist @Diego My favorite Songs 43-55
.loadplaylist @Diego My favorite Songs 1-10
```

