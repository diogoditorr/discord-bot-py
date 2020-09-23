from discord.ext import commands

class Error(Exception):
    pass


class AttemptOverwriteError(Error):
    """ Raised when an attempt to overwrite an existing value in database 
    inappropriate"""
    def __init__(self, message=None):
        self.message = message


class PlayerPermissionError(commands.CheckFailure):
    def __init__(self, permission: str = None, *args):
        self.permission = permission