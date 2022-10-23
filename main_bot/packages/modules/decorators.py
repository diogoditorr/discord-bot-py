import discord
from discord import app_commands
from discord.ext import commands

from ..database.database import Database
from ..database.exceptions import PlayerPermissionError


def has_admin_permission():

    async def predicate(interaction: discord.Interaction):
        db = await Database.connect()
        perms = await db.player_permissions.get(interaction.user, interaction.guild)

        if not perms.has_user_permission(interaction.user, perms.admin):
            raise PlayerPermissionError(permission='Admin')
        else:
            return True

    return app_commands.check(predicate)


def has_dj_permission():

    async def predicate(interaction: discord.Interaction):
        db = await Database.connect()
        perms = await db.player_permissions.get(interaction.user, interaction.guild)

        if not (perms.has_user_permission(interaction.user, perms.admin) or
                perms.has_user_permission(interaction.user, perms.dj)):
            raise PlayerPermissionError(permission='DJ')
        else:
            return True

    return app_commands.check(predicate)


def has_user_permission():

    async def predicate(interaction: discord.Interaction):
        db = await Database.connect()
        perms = await db.player_permissions.get(interaction.user, interaction.guild)

        if not (perms.has_user_permission(interaction.user, perms.admin) or
                perms.has_user_permission(interaction.user, perms.dj) or
                perms.has_user_permission(interaction.user, perms.user)):
            raise PlayerPermissionError(permission='User')
        else:
            return True

    return app_commands.check(predicate)
    
