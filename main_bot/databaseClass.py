import sqlite3
import ast

class PlaylistDatabase:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                guild_id BIGINT NOT NULL,
                guild_name TEXT NOT NULL,
                user_id BIGINT NOT NULL,
                playlist_name VARCHAR(50) NOT NULL,
                playlist_owner VARCHAR(60) NOT NULL,
                privacy VARCHAR(7) NOT NULL,
                length_songs INT NOT NULL,
                songs TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def create(self, guild_id, guild_name, user_id, playlist_name, playlist_owner, privacy, songs=[]):
        self.cursor.execute("INSERT INTO playlists VALUES (?,?,?,?,?,?,?,?)",
        (guild_id, guild_name, user_id, playlist_name, playlist_owner, privacy, len(songs), str(songs)))
        self.connection.commit()

    def updatePlaylistPrivacy(self, playlist, privacy):
        self.cursor.execute("""
            UPDATE playlists
            SET privacy = ?
            WHERE guild_id = ? AND
            user_id = ? AND
            LOWER(playlist_name) = LOWER(?)
        """, (privacy, playlist.guild_id, playlist.owner_id, playlist.name))
        self.connection.commit()

    def updatePlaylistSongs(self, playlist):
        self.cursor.execute("""
            UPDATE playlists
            SET songs = ?, length_songs = ?
            WHERE guild_id = ? AND 
            user_id = ? AND 
            LOWER(playlist_name) = LOWER(?)
        """, (str(playlist.songs), len(playlist.songs), playlist.guild_id, playlist.owner_id, playlist.name))
        self.connection.commit()

    def delete(self, playlist):
        self.cursor.execute("""
            DELETE FROM playlists
            WHERE guild_id = ? AND
            user_id = ? AND
            playlist_name = ?
        """, (playlist.guild_id, playlist.owner_id, playlist.name))
        self.connection.commit()

    def addSongs(self, playlist, new_songs):
        for song in new_songs:
            playlist.songs.append(song)

        self.cursor.execute("""
            UPDATE playlists
            SET songs = ?, length_songs = ?
            WHERE guild_id = ? AND
            user_id = ? AND
            LOWER(playlist_name) = LOWER(?)
        """, (str(playlist.songs), len(playlist.songs), playlist.guild_id, playlist.owner_id, playlist.name))
        self.connection.commit()

    def GetUserPlaylists(self, guild_id, user_id):
        self.cursor.execute("""
            SELECT playlist_name, length_songs
            FROM playlists
            WHERE guild_id = ? AND
            user_id = ?
            ORDER BY playlist_name
        """, (guild_id, user_id))
        return self.cursor.fetchall()

    # def returnName(self, guild_id, user_id, playlist_name):
    #     self.cursor.execute("""
    #         SELECT playlist_name
    #         FROM playlists
    #         WHERE guild_id = ? AND
    #         user_id = ? AND
    #         LOWER(playlist_name) = LOWER(?)
    #     """, (guild_id, user_id, playlist_name))
    #     return self.cursor.fetchone()[0]

    def returnPlaylist(self, guild_id, user_id, playlist_name):
        self.cursor.execute("""
            SELECT guild_id,
                playlist_name, 
                playlist_owner, 
                user_id, 
                privacy, 
                songs
            FROM playlists
            WHERE guild_id = ? AND
            user_id = ? AND
            LOWER(playlist_name) = LOWER(?)
        """, (guild_id, user_id, playlist_name))

        results = self.cursor.fetchone()

        if results != None:
            playlist = {
                'guild_id': int(results[0]),
                'name': results[1],
                'owner': results[2],
                'owner_id': int(results[3]),
                'privacy': results[4], 
                'songs': ast.literal_eval(results[5])
            }
        else:
            playlist = None
        
        return playlist

    def checkExistence(self, guild_id, user_id, playlist_name):
        self.cursor.execute("""
            SELECT guild_id, user_id, playlist_name FROM playlists 
            WHERE 
            guild_id = ? AND
            user_id = ? AND
            LOWER(playlist_name) = LOWER(?)
        """, (guild_id, user_id, playlist_name))

        if len(self.cursor.fetchall()) > 0:
            return True
        else:
            return False

    def __del__(self):
        self.connection.close()