from .databaseClass import PlaylistDatabase

playlistQuery = PlaylistDatabase('guilds_database.db')

class Playlist():

    def __init__(self, playlist):
        self.guild_id = playlist['guild_id']
        self.name = playlist['name']
        self.owner = playlist['owner']
        self.owner_id = playlist['owner_id']
        self.privacy = playlist['privacy']
        self.songs = playlist['songs']
    

    @classmethod
    def returnPlaylist(cls, guild_id, user_id, playlist_name):
        playlist = playlistQuery.returnPlaylist(guild_id, user_id, playlist_name)
        
        if playlist:
            return cls(playlist)
        else:
            return None