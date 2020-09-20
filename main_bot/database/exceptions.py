
class Error(Exception):
    pass


class AttemptOverwriteError(Error):
    """ Raised when an attempt to overwrite an existing value in database 
    inappropriate"""
    def __init__(self, message):
        self.message = message