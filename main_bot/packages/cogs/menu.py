import discord
from discord.ext import commands, menus

class Menus(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def create_menu(self, ctx):
        m = MyMenu()
        await m.start(ctx)

    @commands.command()
    async def delete_things(self, ctx):
        confirm = await Confirm('Delete everything?').prompt(ctx)
        if confirm:
            await ctx.send('deleted...')

    @commands.command()
    async def list_page_source(self, ctx):
        pages = menus.MenuPages(
            source=PaginatorSource(range(1, 100)), 
            clear_reactions_after=True
        )
        await pages.start(ctx)


class InteractiveController(menus.Menu):
    pass


class PaginatorSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=4)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        return '\n'.join(f'{i}. {v}' for i, v in enumerate(entries, start=offset))


class MyMenu(menus.Menu):
    async def send_initial_message(self, ctx, channel):
        return await channel.send(f'Hello {ctx.author}')

    @menus.button('\N{THUMBS UP SIGN}')
    async def on_thumbs_up(self, payload):
        await self.message.edit(content=f'Thanks {self.ctx.author}!')

    @menus.button('\N{THUMBS DOWN SIGN}')
    async def on_thumbs_down(self, payload):
        await self.message.edit(content=f"That's not nice {self.ctx.author}...")

    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f')
    async def on_stop(self, payload):
        self.stop()


class Confirm(menus.Menu):
    def __init__(self, msg):
        super().__init__(timeout=30.0, delete_message_after=True)
        self.msg = msg
        self.result = None

    async def send_initial_message(self, ctx, channel):
        return await channel.send(self.msg)

    @menus.button('\N{WHITE HEAVY CHECK MARK}')
    async def do_confirm(self, payload):
        self.result = True
        self.stop()

    @menus.button('\N{CROSS MARK}')
    async def do_deny(self, payload):
        self.result = False
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result

    
def setup(client):
    client.add_cog(Menus(client))