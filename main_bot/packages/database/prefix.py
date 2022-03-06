from __future__ import annotations
import os
from typing import Union

import aiosqlite
import discord


class Prefix:
    DEFAULT = '.'

    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection

    async def get(self, guild: discord.Guild) -> str: 
        prefix = await self._fetch_guild_prefix(guild)
        if not prefix:
            await self._create_new_entry(guild)
            prefix = Prefix.DEFAULT

        return prefix

    async def update(self, guild: discord.Guild, prefix: str) -> None:
        await self.connection.execute("UPDATE guild SET prefix = ? WHERE guild_id = ?", 
                                        (prefix, guild.id,))
        await self.connection.commit()

    async def _fetch_guild_prefix(self, guild: discord.Guild) -> Union[str, None]:
        self.cursor = await self.connection.execute("""
            SELECT prefix
            FROM guild
            WHERE guild_id = ?;
        """, (guild.id,))

        prefix = await self.cursor.fetchone()

        if prefix:
            return prefix[0]
        else:
            return None

    async def _create_new_entry(self, guild: discord.Guild) -> None:
        await self.connection.execute("INSERT INTO guild VALUES (?,?,?,?,?)",
                                            (guild.id, guild.name, guild.owner.id, 
                                            guild.owner.name+"#"+guild.owner.discriminator,
                                            Prefix.DEFAULT))
        await self.connection.commit()

    def __repr__(self):
        return "<Prefix>"


