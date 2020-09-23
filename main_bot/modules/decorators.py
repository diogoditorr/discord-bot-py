import discord
from discord.ext import commands

from database.database import Database
from database.exceptions import PlayerPermissionError

def has_admin_permission():

    async def predicate(ctx: commands.Context):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx)
        
        if not perms.has_author_permission(ctx, perms.admin):
            raise PlayerPermissionError(permission='Admin')
        else:
            return True
        
    return commands.check(predicate)


def has_dj_permission():

    async def predicate(ctx: commands.Context):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx)
        
        if not (perms.has_author_permission(ctx, perms.admin) or 
                perms.has_author_permission(ctx, perms.dj)):
            raise PlayerPermissionError(permission='DJ')
        else:
            return True

    return commands.check(predicate)


def has_user_permission():

    async def predicate(ctx: commands.Context):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx)
        
        if not (perms.has_author_permission(ctx, perms.admin) or
                perms.has_author_permission(ctx, perms.dj) or
                perms.has_author_permission(ctx, perms.user)):
            raise PlayerPermissionError(permission='User')
        else:
            return True

    return commands.check(predicate)

def test_error():

    async def predicate(ctx: commands.Context):
        raise PlayerPermissionError(permission='DJ')

    return commands.check(predicate)