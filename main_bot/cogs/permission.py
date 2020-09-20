import discord
import re
from discord.ext import commands

from database.database import Database
from database.exceptions import AttemptOverwriteError
from database.player_permissions import (PlayerPermissions, AdminPermission, 
                                            DjPermission, UserPermission)

class PermissionCommands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def admin(self, ctx, *, args):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx.guild)

        member, role, target = self._get_mentions(ctx)
        
        if (cmd := re.match(r'^(add|del|list)(?: (<?@[?!&]*\d+>?)| @everyone)?$', args)):
            mode = cmd.group(1)

            if mode == 'add' and (member or role):
                try:
                    self._add_to_permission(perms.admin, member, role)
                except AttemptOverwriteError:
                    await ctx.send(f"Já existe **'{target}'** em Admin.")
                else:
                    await db.player_permissions.update(perms)
                   
            elif mode == 'del' and (member or role):
                try:
                    self._remove_from_permission(perms.admin, member, role)
                except ValueError:
                    await ctx.send("Não foi possível remover o membro ou cargo.")
                except AttemptOverwriteError:
                    await ctx.send(f"Já existe **'{target}'** em Admin.")
                else:
                    await db.player_permissions.update(perms)

            elif mode == 'list':
                author_icon = ctx.author.avatar_url.BASE + ctx.author.avatar_url._url
                bot_icon = ctx.me.avatar_url.BASE + ctx.me.avatar_url._url
                
                author_permission = self._get_permission(str(ctx.author.id), perms)
                if author_permission != 'Admin':
                    emoji_permission = '❌'
                else:
                    emoji_permission = '✅'

                permission = f'{emoji_permission} ({author_permission})'

                embed = discord.Embed(title="Usuários e funções com as permissões de Admin", color=ctx.guild.me.top_role.color)
                embed.set_author(name=ctx.author.name, icon_url=author_icon)
                embed.add_field(name="Roles", value=self._get_embed_roles(perms.admin.roles), inline=True)
                embed.add_field(name="Members", value=self._get_embed_members(perms.admin.members), inline=True)
                embed.add_field(name=ctx.author.name, value=permission, inline=False)
                embed.set_footer(text=ctx.me.display_name, icon_url=bot_icon)
                await ctx.send(embed=embed)
    
        else:
            prefix = await self.client.get_prefix(ctx)
            return await ctx.send(
                'Utilize:\n```bash\n'
                f'{prefix}admin add <role|member>\n'
                f'{prefix}admin del <role|member>\n'
                f'{prefix}admin list```'
            )

    @commands.command()
    async def dj(self, ctx, *, args):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx.guild)

        member, role, target = self._get_mentions(ctx)

        if (cmd := re.match(r'^(add|del|list)(?: (<?@[?!&]*\d+>?)| @everyone)?$', args)):
            mode = cmd.group(1)

            if mode == 'add' and (member or role):
                try:
                    self._add_to_permission(perms.dj, member, role)
                except AttemptOverwriteError:
                    await ctx.send(f"Já existe **'{target}'** em DJ.")
                else:
                    await db.player_permissions.update(perms)
                   
            elif mode == 'del' and (member or role):
                try:
                    self._remove_from_permission(perms.dj, member, role)
                except ValueError:
                    await ctx.send("Não foi possível remover o membro ou cargo.")
                except AttemptOverwriteError:
                    await ctx.send(f"Já existe **'{target}'** em DJ.")
                else:
                    await db.player_permissions.update(perms)

            elif mode == 'list':
                author_icon = ctx.author.avatar_url.BASE + ctx.author.avatar_url._url
                bot_icon = ctx.me.avatar_url.BASE + ctx.me.avatar_url._url
                
                author_permission = self._get_permission(str(ctx.author.id), perms)
                if author_permission != 'DJ' and author_permission != 'Admin':
                    emoji_permission = '❌'
                else:
                    emoji_permission = '✅'

                permission = f'{emoji_permission} ({author_permission})'

                embed = discord.Embed(title="Usuários e funções com as permissões de DJ", color=ctx.guild.me.top_role.color)
                embed.set_author(name=ctx.author.name, icon_url=author_icon)
                embed.add_field(name="Roles", value=self._get_embed_roles(perms.dj.roles), inline=True)
                embed.add_field(name="Members", value=self._get_embed_members(perms.dj.members), inline=True)
                embed.add_field(name=ctx.author.name, value=permission, inline=False)
                embed.set_footer(text=ctx.me.display_name, icon_url=bot_icon)
                await ctx.send(embed=embed)
    
        else:
            prefix = await self.client.get_prefix(ctx)
            return await ctx.send(
                'Utilize:\n```bash\n'
                f'{prefix}dj add <role|member>\n'
                f'{prefix}dj del <role|member>\n'
                f'{prefix}dj list```'
            )

    @commands.command()
    async def user(self, ctx, *, args):
        db = await Database.connect()
        perms = await db.player_permissions.get(ctx.guild)

        member, role, target = self._get_mentions(ctx)

        if (cmd := re.match(r'^(add|del|list)(?: (<?@[?!&]*\d+>?)| @everyone)?$', args)):
            mode = cmd.group(1)

            if mode == 'add' and (member or role):
                try:
                    self._add_to_permission(perms.user, member, role)
                except AttemptOverwriteError:
                    await ctx.send(f"Já existe **'{target}'** em User.")
                else:
                    await db.player_permissions.update(perms)
                   
            elif mode == 'del' and (member or role):
                try:
                    self._remove_from_permission(perms.user, member, role)
                except ValueError:
                    await ctx.send("Não foi possível remover o membro ou cargo.")
                except AttemptOverwriteError:
                    await ctx.send(f"Já existe **'{target}'** em User.")
                else:
                    await db.player_permissions.update(perms)

            elif mode == 'list':
                author_icon = ctx.author.avatar_url.BASE + ctx.author.avatar_url._url
                bot_icon = ctx.me.avatar_url.BASE + ctx.me.avatar_url._url
                
                author_permission = self._get_permission(str(ctx.author.id), perms)
                if author_permission != 'Admin' and author_permission != 'DJ' and author_permission != 'User':
                    emoji_permission = '❌'
                else:
                    emoji_permission = '✅'

                permission = f'{emoji_permission} ({author_permission})'

                embed = discord.Embed(title="Usuários e funções com as permissões de User", color=ctx.guild.me.top_role.color)
                embed.set_author(name=ctx.author.name, icon_url=author_icon)
                embed.add_field(name="Roles", value=self._get_embed_roles(perms.user.roles), inline=True)
                embed.add_field(name="Members", value=self._get_embed_members(perms.user.members), inline=True)
                embed.add_field(name=ctx.author.name, value=permission, inline=False)
                embed.set_footer(text=ctx.me.display_name, icon_url=bot_icon)
                await ctx.send(embed=embed)
    
        else:
            prefix = await self.client.get_prefix(ctx)
            return await ctx.send(
                'Utilize:\n```bash\n'
                f'{prefix}user add <role|member>\n'
                f'{prefix}user del <role|member>\n'
                f'{prefix}user list```'
            )

    def _get_mentions(self, ctx: commands.Context):
        member: str = None
        role: str = None
        target: str = None

        if ctx.message.mentions:
            member = str(ctx.message.mentions[0].id)
            target = ctx.message.mentions[0].display_name
        if ctx.message.role_mentions:
            role = str(ctx.message.role_mentions[0].id)
            target = ctx.message.role_mentions[0].name
        if ctx.message.mention_everyone:
            role = '@everyone'
            target = '@everyone'

        return (member, role, target)

    def _add_to_permission(self, permission, member: str, role: str):
        if member and not member in permission.members:
            permission.add_member(member)
        elif role and not role in permission.roles:
            permission.add_role(role)
        else:
            raise AttemptOverwriteError

    def _remove_from_permission(self, permission, member: str, role: str):
        if member and member in permission.members:
            permission.remove_member(member)
        elif role and role in permission.roles:
            permission.remove_role(role)
        else:
            raise AttemptOverwriteError
        
    def _get_permission(self, author_id: str, perms: PlayerPermissions):
        if author_id in perms.admin.members or '@everyone' in perms.admin.roles:
            return 'Admin'
        elif author_id in perms.dj.members or '@everyone' in perms.dj.roles:
            return 'DJ'
        elif author_id in perms.user.members or '@everyone' in perms.user.roles:
            return 'User'
        else:
            return 'Base'

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
                if not role == '@everyone':
                    msg += f'<@&{role}>\n'
                else:
                    msg += role + '\n'
                    
            return msg
        else:
            return '<none>'

def setup(client):
    client.add_cog(PermissionCommands(client))
