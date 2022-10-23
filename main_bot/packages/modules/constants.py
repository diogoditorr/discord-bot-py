import re
from .utils import load_yaml_config


URL_RX = re.compile(r'https?://(?:www\.)?.+')
LAVALINK_SERVER_CONFIG = load_yaml_config()