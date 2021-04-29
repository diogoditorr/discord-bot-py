from __future__ import annotations

import os
from pathlib import Path
from typing import Union

import aiosqlite
from aiosqlite.cursor import Cursor

from .player_permissions import Permissions
from .prefix import Prefix

PWD = Path(os.path.dirname(__file__))


class Database:
    __slots__ = ('connection', 'prefix', 'player_permissions', 'cursor')

    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection
        self.cursor: Union[Cursor, None] = None
        self.prefix = Prefix(self.connection)
        self.player_permissions = Permissions(self.connection)

    @classmethod
    async def connect(cls) -> Database:
        connection = await aiosqlite.connect(PWD.joinpath('guilds_database.sqlite'))
        
        return Database(connection)

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
