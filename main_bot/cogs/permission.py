import discord
import re
from discord.ext import commands
from discord.utils import get
from typing import Union, Optional

from database.database import Database
from database.exceptions import AttemptOverwriteError
from database.player_permissions import PlayerPermissions

class PermissionCommands(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        ctx.author = await ctx.guild.fetch_member(ctx.author.id) or ctx.author

        return guild_check

    @commands.command()
    async def admin(self, ctx, mode: str, id_mentioned: Optional[Union[discord.Member, discord.Role, str]]):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx)

        if await self._check_exceptions(ctx, mode, id_mentioned, perms):
            return

        target = self._get_from_mention(ctx, id_mentioned)

        if mode == 'add' and id_mentioned:
            try:
                self._add_to_permission(perms.admin, id_mentioned)
                await ctx.send(f"Adicionado **'**{target}**'** em Admin.")
            except AttemptOverwriteError:
                await ctx.send(f"Já existe **'**{target}**'** em Admin.")
            else:
                await db.player_permissions.update(perms)
                
        elif mode == 'del' and id_mentioned:
            try:
                self._remove_from_permission(perms.admin, id_mentioned)
                await ctx.send(f"Removido **'**{target}**'** em Admin.")
            except ValueError:
                await ctx.send("Não foi possível remover o membro ou cargo.")
            except AttemptOverwriteError:
                await ctx.send(f"Não existe **'**{target}**'** em Admin.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'list':
            author_permission = self._get_permission(ctx, perms)
            if author_permission != 'Admin':
                emoji_permission = '❌'
            else:
                emoji_permission = '✅'

            has_permission = f'{emoji_permission} ({author_permission})'

            await self._send_permission_embed(ctx, perms.admin, has_permission, 
                title="Usuários e funções com as permissões de Admin")

        else:
            prefix = await self.client.get_prefix(ctx)
            return await ctx.send(
                'Utilize:\n```bash\n'
                f'{prefix}admin add <role|member>\n'
                f'{prefix}admin del <role|member>\n'
                f'{prefix}admin list```'
            )

    @commands.command()
    async def dj(self, ctx, mode: str, id_mentioned: Optional[Union[discord.Member, discord.Role, str]]):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx)

        if await self._check_exceptions(ctx, mode, id_mentioned, perms):
            return

        target = self._get_from_mention(ctx, id_mentioned)

        if mode == 'add' and id_mentioned:
            try:
                self._add_to_permission(perms.dj, id_mentioned)
                await ctx.send(f"Adicionado **'**{target}**'** em DJ.")
            except AttemptOverwriteError:
                await ctx.send(f"Já existe **'**{target}**'** em DJ.")
            else:
                await db.player_permissions.update(perms)
                
        elif mode == 'del' and id_mentioned:
            try:
                self._remove_from_permission(perms.dj, id_mentioned)
                await ctx.send(f"Removido **'**{target}**'** em DJ.")
            except ValueError:
                await ctx.send("Não foi possível remover o membro ou cargo.")
            except AttemptOverwriteError:
                await ctx.send(f"Não existe **'**{target}**'** em DJ.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'list':
            author_permission = self._get_permission(ctx, perms)
            if author_permission != 'Admin' and author_permission != 'DJ':
                emoji_permission = '❌'
            else:
                emoji_permission = '✅'

            has_permission = f'{emoji_permission} ({author_permission})'

            await self._send_permission_embed(ctx, perms.dj, has_permission, 
                title="Usuários e funções com as permissões de DJ")

        else:
            prefix = await self.client.get_prefix(ctx)
            return await ctx.send(
                'Utilize:\n```bash\n'
                f'{prefix}dj add <role|member>\n'
                f'{prefix}dj del <role|member>\n'
                f'{prefix}dj list```'
            )

    @commands.command()
    async def user(self, ctx, mode: str, id_mentioned: Optional[Union[discord.Member, discord.Role, str]]):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx)

        if await self._check_exceptions(ctx, mode, id_mentioned, perms):
            return

        target = self._get_from_mention(ctx, id_mentioned)

        if mode == 'add' and id_mentioned:
            try:
                self._add_to_permission(perms.user, id_mentioned)
                await ctx.send(f"Adicionado **'**{target}**'** em User.")
            except AttemptOverwriteError:
                await ctx.send(f"Já existe **'**{target}**'** em User.")
            else:
                await db.player_permissions.update(perms)
                
        elif mode == 'del' and id_mentioned:
            try:
                self._remove_from_permission(perms.user, id_mentioned)
                await ctx.send(f"Removido **'**{target}**'** em User.")
            except ValueError:
                await ctx.send("Não foi possível remover o membro ou cargo.")
            except AttemptOverwriteError:
                await ctx.send(f"Não existe **'**{target}**'** em User.")
            else:
                await db.player_permissions.update(perms)

        elif mode == 'list':
            author_permission = self._get_permission(ctx, perms)
            if author_permission != 'Admin' and author_permission != 'DJ' and author_permission != 'User':
                emoji_permission = '❌'
            else:
                emoji_permission = '✅'

            has_permission = f'{emoji_permission} ({author_permission})'

            await self._send_permission_embed(ctx, perms.user, has_permission, 
                title="Usuários e funções com as permissões de User")

        else:
            prefix = await self.client.get_prefix(ctx)
            return await ctx.send(
                'Utilize:\n```bash\n'
                f'{prefix}user add <role|member>\n'
                f'{prefix}user del <role|member>\n'
                f'{prefix}user list```'
            )

    async def _check_exceptions(self, ctx, mode, id_mentioned, perms):
        if mode in ('add', 'del') and isinstance(id_mentioned, str):
            await ctx.send("Nada foi encontrado no argumento **'**{}**'**".format(id_mentioned))
            return True

        if mode in ('add', 'del') and not perms.has_author_permission(ctx, perms.admin):
            await ctx.send("Você não tem permissão de administrador para modificar permissões.")
            return True

        return False

    def _get_from_mention(self, ctx: commands.Context, mention: Union[discord.Member, discord.Role]):
        target: str = None
        
        if isinstance(mention, discord.Member):
            target = mention.display_name
        elif isinstance(mention, discord.Role):
            target = mention.name

        return target

    def _add_to_permission(self, permission, mention: Union[discord.Member, discord.Role]):
        if isinstance(mention, discord.Member) and not str(mention.id) in permission.members:
            permission.add_member(mention)
        elif isinstance(mention, discord.Role) and not str(mention.id) in permission.roles:
            permission.add_role(mention)
        else:
            raise AttemptOverwriteError

    def _remove_from_permission(self, permission, mention: Union[discord.Member, discord.Role]):
        if isinstance(mention, discord.Member) and str(mention.id) in permission.members:
            permission.remove_member(mention)
        elif isinstance(mention, discord.Role) and str(mention.id) in permission.roles:
            permission.remove_role(mention)
        else:
            raise AttemptOverwriteError
        
    def _get_permission(self, ctx: commands.Context, perms: PlayerPermissions):
        if perms.has_author_permission(ctx, perms.admin):
            return 'Admin'
        elif perms.has_author_permission(ctx, perms.dj):
            return 'DJ'
        elif perms.has_author_permission(ctx, perms.user):
            return 'User'
        else:
            return 'Base'

    async def _send_permission_embed(self, ctx: commands.Context, permission, has_permission: str, title: str):
        author_icon = ctx.author.avatar_url.BASE + ctx.author.avatar_url._url
        bot_icon = ctx.me.avatar_url.BASE + ctx.me.avatar_url._url

        embed = discord.Embed(title=title, color=ctx.guild.me.top_role.color)
        embed.set_author(name=ctx.author.name, icon_url=author_icon)
        embed.add_field(name="Roles", value=self._get_embed_roles(permission.roles), inline=True)
        embed.add_field(name="Members", value=self._get_embed_members(permission.members), inline=True)
        embed.add_field(name=ctx.author.name, value=has_permission, inline=False)
        embed.set_footer(text=ctx.me.display_name, icon_url=bot_icon)
        await ctx.send(embed=embed)

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

def setup(client):
    client.add_cog(PermissionCommands(client))
