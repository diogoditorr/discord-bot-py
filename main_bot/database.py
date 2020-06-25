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
                songs TEXT
            )
        """)
        self.connection.commit()

    def create(self, guild_id, guild_name, user_id, playlist_name, playlist_owner, privacy, songs):
        self.cursor.execute("INSERT INTO playlists VALUES (?,?,?,?,?,?,?)",
        (guild_id, guild_name, user_id, playlist_name, playlist_owner, privacy, songs))
        self.connection.commit()

    def update(self, guild_id, user_id, playlist_name, privacy):
        self.cursor.execute("""
            UPDATE playlists
            SET privacy = ?
            WHERE guild_id = ? AND
            user_id = ? AND
            LOWER(playlist_name) = LOWER(?)
        """, (privacy, guild_id, user_id, playlist_name))
        self.connection.commit()

    def delete(self, guild_id, user_id, playlist_name):
        self.cursor.execute("""
            DELETE FROM playlists
            WHERE guild_id = ? AND
            user_id = ? AND
            playlist_name = ?
        """, (guild_id, user_id, playlist_name))
        self.connection.commit()

    def addTracks(self, guild_id, user_id, playlist_name, tracks):
        songs = PlaylistDatabase.playlistReturnTracks(self, guild_id, user_id, playlist_name)['tracks']

        if songs == "":
            songs = list(songs)
        else:
            songs = ast.literal_eval(songs)
        
        for track in tracks:
            songs.append(track)

        tracks = str(songs)

        self.cursor.execute("""
            UPDATE playlists
            SET songs = ?
            WHERE guild_id = ? AND
            user_id = ? AND
            playlist_name = ?
        """, (tracks, guild_id, user_id, playlist_name))
        self.connection.commit()

    def GetUserPlaylists(self, guild_id, user_id):
        self.cursor.execute("""
            SELECT playlist_name
            FROM playlists
            WHERE guild_id = ? AND
            user_id = ?
            ORDER BY playlist_name
        """, (guild_id, user_id))
        return self.cursor.fetchall()

    def returnName(self, guild_id, user_id, playlist_name):
        self.cursor.execute("""
            SELECT playlist_name
            FROM playlists
            WHERE guild_id = ? AND
            user_id = ? AND
            LOWER(playlist_name) = LOWER(?)
        """, (guild_id, user_id, playlist_name))
        return self.cursor.fetchone()[0]

    def returnTracks(self, guild_id, user_id, playlist_name):
        self.cursor.execute("""
            SELECT privacy, songs
            FROM playlists
            WHERE guild_id = ? AND
            user_id = ? AND
            playlist_name = ?
        """, (guild_id, user_id, playlist_name))

        results = self.cursor.fetchone()
        return {'privacy': f'{results[0]}', 'tracks': f'{results[1]}'}

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