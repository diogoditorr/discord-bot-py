import re
from typing import Literal, Optional, Union

import discord
from discord import Interaction, Member, Message, Role, app_commands
from discord.ext import commands
from discord.utils import get

from ..database.database import Database
from ..database.exceptions import AttemptOverwriteError
from ..database.player_permissions import PlayerPermissions


class PermissionCommands(app_commands.Group):
    def __init__(self):
        super().__init__(
            name='permission',
            description='Comandos para gerenciar permissões.'
        )

    @app_commands.command()
    async def admin(
        self,
        interaction: Interaction,
        mode: Literal['add', 'del', 'list'],
        id_mentioned: Member | Role | None
    ):
        db = await Database.connect()
        perms = await db.player_permissions.get(interaction.user, interaction.guild)

        if await self._check_exceptions(interaction, mode, id_mentioned, perms):
            return

        target = self._get_from_mention(interaction, id_mentioned)

        if mode == 'add' and id_mentioned:
            try:
                self._add_to_permission(perms.admin, id_mentioned)
                await interaction.response.send_message(f"Adicionado **'**{target}**'** em Admin.")
            except AttemptOverwriteError:
                await interaction.response.send_message(f"Já existe **'**{target}**'** em Admin.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'del' and id_mentioned:
            try:
                self._remove_from_permission(perms.admin, id_mentioned)
                await interaction.response.send_message(f"Removido **'**{target}**'** em Admin.")
            except ValueError:
                await interaction.response.send_message("Não foi possível remover o membro ou cargo.")
            except AttemptOverwriteError:
                await interaction.response.send_message(f"Não existe **'**{target}**'** em Admin.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'list':
            author_permission = self._get_permission(interaction, perms)
            if author_permission != 'Admin':
                emoji_permission = '❌'
            else:
                emoji_permission = '✅'

            has_permission = f'{emoji_permission} ({author_permission})'

            await self._send_permission_embed(interaction, perms.admin, has_permission,
                                              title="Usuários e funções com as permissões de Admin")

        else:
            return await interaction.response.send_message(f"""
                Usuário|Cargo exigido no modo `{mode}`
            """)

    @app_commands.command()
    async def dj(
        self,
        interaction: Interaction,
        mode: Literal['add', 'del', 'list'],
        id_mentioned: Member | Role | None
    ):
        db = await Database.connect()
        perms = await db.player_permissions.get(interaction.user, interaction.guild)

        if await self._check_exceptions(interaction, mode, id_mentioned, perms):
            return

        target = self._get_from_mention(interaction, id_mentioned)

        if mode == 'add' and id_mentioned:
            try:
                self._add_to_permission(perms.dj, id_mentioned)
                await interaction.response.send_message(f"Adicionado **'**{target}**'** em DJ.")
            except AttemptOverwriteError:
                await interaction.response.send_message(f"Já existe **'**{target}**'** em DJ.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'del' and id_mentioned:
            try:
                self._remove_from_permission(perms.dj, id_mentioned)
                await interaction.response.send_message(f"Removido **'**{target}**'** em DJ.")
            except ValueError:
                await interaction.response.send_message("Não foi possível remover o membro ou cargo.")
            except AttemptOverwriteError:
                await interaction.response.send_message(f"Não existe **'**{target}**'** em DJ.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'list':
            author_permission = self._get_permission(interaction, perms)
            if author_permission != 'Admin' and author_permission != 'DJ':
                emoji_permission = '❌'
            else:
                emoji_permission = '✅'

            has_permission = f'{emoji_permission} ({author_permission})'

            await self._send_permission_embed(interaction, perms.dj, has_permission,
                                              title="Usuários e funções com as permissões de DJ")

        else:
            return await interaction.response.send_message(f"""
                Usuário|Cargo exigido no modo `{mode}`
            """)

    @app_commands.command()
    async def user(
        self,
        interaction: Interaction,
        mode: Literal['add', 'del', 'list'],
        id_mentioned: Member | Role | None
    ):
        db = await Database.connect()
        perms = await db.player_permissions.get(interaction.user, interaction.guild)

        if await self._check_exceptions(interaction, mode, id_mentioned, perms):
            return

        target = self._get_from_mention(interaction, id_mentioned)

        if mode == 'add' and id_mentioned:
            try:
                self._add_to_permission(perms.user, id_mentioned)
                await interaction.response.send_message(f"Adicionado **'**{target}**'** em User.")
            except AttemptOverwriteError:
                await interaction.response.send_message(f"Já existe **'**{target}**'** em User.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'del' and id_mentioned:
            try:
                self._remove_from_permission(perms.user, id_mentioned)
                await interaction.response.send_message(f"Removido **'**{target}**'** em User.")
            except ValueError:
                await interaction.response.send_message("Não foi possível remover o membro ou cargo.")
            except AttemptOverwriteError:
                await interaction.response.send_message(f"Não existe **'**{target}**'** em User.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'list':
            author_permission = self._get_permission(interaction, perms)
            if author_permission != 'Admin' and author_permission != 'DJ' and author_permission != 'User':
                emoji_permission = '❌'
            else:
                emoji_permission = '✅'

            has_permission = f'{emoji_permission} ({author_permission})'

            await self._send_permission_embed(interaction, perms.user, has_permission,
                                              title="Usuários e funções com as permissões de User")

        else:
            return await interaction.response.send_message(f"""
                Usuário|Cargo exigido no modo `{mode}`
            """)

    async def _check_exceptions(
        self,
        interaction: Interaction,
        mode: Literal['add', 'del', 'list'],
        id_mentioned: Member | Role | None,
        perms: PlayerPermissions
    ):
        if mode in ('add', 'del') and isinstance(id_mentioned, str):
            await interaction.response.send_message("Nada foi encontrado no argumento **'**{}**'**".format(id_mentioned))
            return True

        if mode in ('add', 'del') and not perms.has_user_permission(interaction.user, perms.admin):
            await interaction.response.send_message("Você não tem permissão de administrador para modificar permissões.")
            return True

        return False

    def _get_from_mention(self, interaction: Interaction, mention: Member | Role):
        target: str = None

        if isinstance(mention, Member):
            target = mention.display_name
        elif isinstance(mention, Role):
            target = mention.name

        return target

    def _add_to_permission(self, permission, mention: Member | Role):
        if isinstance(mention, Member) and not str(mention.id) in permission.members:
            permission.add_member(mention)
        elif isinstance(mention, Role) and not str(mention.id) in permission.roles:
            permission.add_role(mention)
        else:
            raise AttemptOverwriteError

    def _remove_from_permission(self, permission, mention: Member | Role):
        if isinstance(mention, Member) and str(mention.id) in permission.members:
            permission.remove_member(mention)
        elif isinstance(mention, Role) and str(mention.id) in permission.roles:
            permission.remove_role(mention)
        else:
            raise AttemptOverwriteError

    def _get_permission(self, interaction: Interaction, perms: PlayerPermissions):
        if perms.has_user_permission(interaction.user, perms.admin):
            return 'Admin'
        elif perms.has_user_permission(interaction.user, perms.dj):
            return 'DJ'
        elif perms.has_user_permission(interaction.user, perms.user):
            return 'User'
        else:
            return 'Base'

    async def _send_permission_embed(self, interaction: Interaction, permission, has_permission: str, title: str):
        user_icon = interaction.user.avatar.url
        bot_icon = interaction.guild.me.default_avatar.url

        embed = discord.Embed(
            title=title, color=interaction.guild.me.top_role.color)
        embed.set_author(name=interaction.user.name, icon_url=user_icon)
        embed.add_field(name="Roles", value=self._get_embed_roles(
            permission.roles), inline=True)
        embed.add_field(name="Members", value=self._get_embed_members(
            permission.members), inline=True)
        embed.add_field(name=interaction.user.name,
                        value=has_permission, inline=False)
        embed.set_footer(text=interaction.user.display_name, icon_url=bot_icon)
        await interaction.response.send_message(embed=embed)

    def _get_embed_members(self, members: list):
        if members:
            msg = ''

            for member in members:
                msg += f'<@{member}>\n'

            return msg
        else:
            return '<none>'

    def _get_embed_roles(self, roles: list):
        if roles:
            msg = ''

            for role in roles:
                msg += f'<@&{role}>\n'

            return msg
        else:
            return '<none>'
