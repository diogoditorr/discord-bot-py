import aiosqlite
import discord
import ast
import re
from discord.ext import commands
from discord.utils import get
from typing import Union

from .exceptions import AttemptOverwriteError


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


class PlayerPermissions():    
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

    def has_author_permission(self, ctx: commands.Context, permission: Union[AdminPermission, DjPermission, UserPermission]) -> bool:
        if isinstance(permission, (AdminPermission, DjPermission, UserPermission)):
            return (self._author_in_members(ctx, permission) or self._author_in_roles(ctx, permission))
        else:
            raise TypeError

    def _author_in_members(self, ctx: commands.Context, permission: Union[AdminPermission, DjPermission, UserPermission]) -> bool:
        if str(ctx.author.id) in permission.members or \
         ctx.author.guild_permissions.administrator:
            return True
        else:
            return False

    def _author_in_roles(self, ctx: commands.Context, permission: Union[AdminPermission, DjPermission, UserPermission]) -> bool:
        for role in ctx.author.roles:
            if str(role.id) in permission.roles:
                return True
        
        return False
            
    def __repr__(self):
        return '<PlayerPermissions guild_id={} guild_name={}>'.format(self.guild.id, self.guild.name)


class Permissions:

    @classmethod
    async def _create_instance(cls, connection: aiosqlite.Connection):
        self = Permissions()
        self.connection = connection
        return self

    async def get(self, ctx: commands.Context):
        perms = await self._fetch_guild_perms(ctx)
        if not perms:
            await self._create_new_entry(ctx)
            perms = await self._fetch_guild_perms(ctx)

        obj = PlayerPermissions(ctx.guild, perms)

        return obj    

    async def _create_new_entry(self, ctx: commands.Context):
        everyone_role = get(ctx.author.roles, position=0)

        await self.connection.execute("INSERT INTO player_permissions VALUES (?,?,?,?,?,?,?)", 
                    (ctx.guild.id, '[]', '[]', f"['{everyone_role.id}']", '[]', f"['{everyone_role.id}']", '[]'))
        await self.connection.commit()

    async def _fetch_guild_perms(self, ctx: commands.Context):
        self.cursor = await self.connection.execute("""
            SELECT admin_roles, admin_members, 
            dj_roles, dj_members, 
            user_roles, user_members
            
            FROM player_permissions
            WHERE guild_id = ?
        """, (ctx.guild.id,))
        
        perms = await self.cursor.fetchone()
        
        return perms if perms else None

    async def update(self, perms: PlayerPermissions):
        if not isinstance(perms, PlayerPermissions):
            raise TypeError("Object is not an instance of PlayerPermissions")

        list_permissions = [perms.admin.roles, perms.admin.members,
            perms.dj.roles, perms.dj.members,
            perms.user.roles, perms.user.members        
        ]

        parameters = [ str(x) for x in list_permissions ]
        parameters.append(perms.guild.id)

        await self.connection.execute("""
            UPDATE player_permissions
            SET admin_roles = ?, admin_members = ?, 
                dj_roles = ?, dj_members = ?,
                user_roles = ?, user_members = ?
            WHERE guild_id = ?
        """, parameters)
        await self.connection.commit()

    def __repr__(self):
        return '<Permissions>'

