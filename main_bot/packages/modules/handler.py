import re


class Query:
    _URL_RX = re.compile(r'https?://(?:www\.)?.+')

    def __init__(self, content, youtube_mode=True):
        
        arguments = content.split()
        if arguments[0] == '-f':
            self.first_song = True
            self.query = " ".join(arguments[1:])
        else:
            self.first_song = False
            self.query = " ".join(arguments)

        self.query = self.query.strip('<>')

        if Query._URL_RX.match(self.query):
            self.first_song = True          
        else:
            if youtube_mode:
                self.query = f'ytsearch:{self.query}'

    def __repr__(self):
        return '<Query content="{}">'.format(self.query)
