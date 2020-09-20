import sqlite3
import aiosqlite
import ast
import os

from .prefix import Prefix
from .player_permissions import Permissions


PWD = os.path.abspath(os.path.dirname(__file__))


class Database:
    @classmethod
    async def connect(cls): 
        self = Database()
        self.connection = await aiosqlite.connect(os.path.realpath(PWD + '\guilds_database.sqlite'))
        self.prefix = await Prefix._create_instance(self.connection)
        self.player_permissions = await Permissions._create_instance(self.connection)

        return self

    @classmethod
    async def create(cls):
        self = await cls.connect()

        self.cursor = await self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS guild (
                guild_id BIGINT NOT NULL,
                guild_name TEXT NOT NULL,
                owner_id BIGINT NOT NULL,
                owner VARCHAR(60) NOT NULL,
                prefix VARCHAR(60) NOT NULL,

                CONSTRAINT pk_guild_id PRIMARY KEY (guild_id)
            );

            CREATE TABLE IF NOT EXISTS player_permissions (
                guild_id BIGINT NOT NULL,
                admin_roles TEXT NOT NULL,
                admin_members TEXT NOT NULL,
                dj_roles TEXT NOT NULL,
                dj_members TEXT NOT NULL,
                user_roles TEXT NOT NULL,
                user_members TEXT NOT NULL,

                CONSTRAINT fk_guild_id FOREIGN KEY (guild_id) REFERENCES guild (guild_id),
                CONSTRAINT uk_guild_id UNIQUE (guild_id)
            );
        """)
        await self.connection.commit()

    async def __aexit__(self):
        await self.connection.close()
        await self.cursor.close()