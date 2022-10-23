from __future__ import annotations
import ast
from typing import Union

import aiosqlite
import discord
from discord.ext import commands
from discord.utils import get


class BasePermissionPlayer:
    def __init__(self):
        self.members = []
        self.roles = []

    def add_member(self, member: discord.Member):
        self.members.append(str(member.id))

    def add_role(self, role: discord.Role):
        self.roles.append(str(role.id))

    def remove_member(self, member: discord.Member):
        self.members.remove(str(member.id))

    def remove_role(self, role: discord.Role):
        self.roles.remove(str(role.id))


class AdminPermission(BasePermissionPlayer):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return '<AdminPermission>'


class DjPermission(BasePermissionPlayer):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return '<DjPermission>'


class UserPermission(BasePermissionPlayer):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return '<UserPermission>'


class PlayerPermissions:
    def __init__(self, guild: discord.Guild, perms: tuple):
        self.guild = guild
        self.admin = AdminPermission()
        self.dj = DjPermission()
        self.user = UserPermission()

        if perms:
            perms = list(map(lambda x: ast.literal_eval(x), perms))

            self.admin.roles = perms[0]
            self.admin.members = perms[1]

            self.dj.roles = perms[2]
            self.dj.members = perms[3]

            self.user.roles = perms[4]
            self.user.members = perms[5]

    def has_user_permission(self, user: discord.Member | discord.User,
                              permission: Union[AdminPermission, DjPermission, UserPermission]) -> bool:
        if not isinstance(user, discord.Member):
            raise AttributeError("'{}' is not a 'discord.Member' object".format(user.__class__))

        if isinstance(permission, (AdminPermission, DjPermission, UserPermission)):
            return (self._user_in_members(user, permission) or self._user_in_roles(user, permission))
        else:
            raise TypeError

    def _user_in_members(self, user: discord.Member, permission: Union[AdminPermission, DjPermission, UserPermission]) -> bool:
        if str(user.id) in permission.members or \
                user.guild_permissions.administrator:
            return True
        else:
            return False

    def _user_in_roles(self, user: discord.Member, permission: Union[AdminPermission, DjPermission, UserPermission]) -> bool:
        for role in user.roles:
            if str(role.id) in permission.roles:
                return True

        return False

    def __repr__(self):
        return '<PlayerPermissions guild_id={} guild_name={}>'.format(self.guild.id, self.guild.name)


class Permissions:
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection

    async def get(self, user: discord.Member | discord.User, guild: discord.Guild) -> PlayerPermissions:
        """Returns a PlayerPermissions object"""
        perms = await self._fetch_guild_perms(guild)
        if not perms:
            await self._create_new_entry(user, guild)
            perms = await self._fetch_guild_perms(guild)

        return PlayerPermissions(guild, perms)

    async def update(self, perms: PlayerPermissions):
        if not isinstance(perms, PlayerPermissions):
            raise TypeError("'{}' is not an instance of PlayerPermissions".format(type(perms).__name__))

        list_permissions = [perms.admin.roles, perms.admin.members,
                            perms.dj.roles, perms.dj.members,
                            perms.user.roles, perms.user.members
                            ]

        parameters = [str(x) for x in list_permissions]
        parameters.append(str(perms.guild.id))

        await self.connection.execute("""
            UPDATE player_permissions
            SET admin_roles = ?, admin_members = ?, 
                dj_roles = ?, dj_members = ?,
                user_roles = ?, user_members = ?
            WHERE guild_id = ?
        """, parameters)
        await self.connection.commit()

    async def _fetch_guild_perms(self, guild: discord.Guild) -> tuple|None:
        self.cursor = await self.connection.execute("""
            SELECT admin_roles, admin_members, 
            dj_roles, dj_members, 
            user_roles, user_members
            
            FROM player_permissions
            WHERE guild_id = ?
        """, (guild.id,))

        perms = await self.cursor.fetchone()

        return perms if perms else None

    async def _create_new_entry(self, user: discord.Member, guild: discord.Guild):
        everyone_role = get(user.roles, position=0)

        await self.connection.execute("INSERT INTO player_permissions VALUES (?,?,?,?,?,?,?)",
                                      (guild.id, '[]', '[]', f"['{everyone_role.id}']", '[]',
                                       f"['{everyone_role.id}']", '[]'))
        await self.connection.commit()

    def __repr__(self):
        return '<Permissions>'
