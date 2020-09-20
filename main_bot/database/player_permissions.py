import aiosqlite
import discord
import ast
import re

from .exceptions import AttemptOverwriteError

MENTION_EXP = re.compile(r'<@([&!?]*)(\d+)>')


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

    def __repr__(self):
        return '<PlayerPermissions guild_id={} guild_name={}>'.format(self.guild.id, self.guild.name)


class BasePermissionPlayer:
    def __init__(self):
        self.members = []
        self.roles = []

    def add_member(self, member: str):
        self.members.append(member)

    def add_role(self, role: str):
        self.roles.append(role)

    def remove_member(self, member: str):
        self.members.remove(member)

    def remove_role(self, role: str):
        self.roles.remove(role)


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


class Permissions:

    @classmethod
    async def _create_instance(cls, connection: aiosqlite.Connection):
        self = Permissions()
        self.connection = connection
        return self

    async def get(self, guild: discord.Guild):
        perms = await self._fetch_guild_perms(guild)
        if not perms:
            await self._create_new_entry(guild)
            perms = await self._fetch_guild_perms(guild)

        obj = PlayerPermissions(guild, perms)

        return obj    

    async def _create_new_entry(self, guild: discord.Guild):
        await self.connection.execute("INSERT INTO player_permissions VALUES (?,?,?,?,?,?,?)", 
                    (guild.id, '[]', '[]', '["@everyone"]', '[]', '[]', '[]'))
        await self.connection.commit()

    async def _fetch_guild_perms(self, guild: discord.Guild):
        self.cursor = await self.connection.execute("""
            SELECT admin_roles, admin_members, 
            dj_roles, dj_members, 
            user_roles, user_members
            
            FROM player_permissions
            WHERE guild_id = ?
        """, (guild.id,))
        
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
