import os
from pathlib import Path
import discord
import yaml

async def get_member(ctx):
    return await ctx.guild.fetch_member(ctx.author.id) if isinstance(ctx.author, discord.User) else ctx.author


def convert_duration(duration: int) -> str:
    duration = duration // 1000

    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)

    return f'{hours:02d}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes:02d}:{seconds:02d}'

def load_yaml_config():
    yaml_config_path = \
        Path(os.path.dirname(__file__)).parent.parent / 'application.yml'

    if not yaml_config_path.exists():
        raise FileNotFoundError(f'{yaml_config_path} not found.')

    with open(yaml_config_path) as f:
        return yaml.safe_load(f)
