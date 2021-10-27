from lib.speculater import Speculater
from os import getenv
from steampy.client import SteamClient

try:
    import environment_variables
except ImportError:
    raise ImportError('Відсутній файл environment_variables.py з змінними середовища')

STEAM_API_KEY = getenv('STEAM_API_KEY')
USERNAME = getenv('USERNAME')
PASSWORD = getenv('PASSWORD')
PATH_TO_STEAMGUARD_FILE = getenv('PATH_TO_STEAMGUARD_FILE')

PHPSESSID = getenv('PHPSESSID')

steam_client = SteamClient(STEAM_API_KEY)
steam_client.login(USERNAME, PASSWORD, PATH_TO_STEAMGUARD_FILE)

speculater = Speculater(steam_client, phpsessid=PHPSESSID)

speculater.run()
