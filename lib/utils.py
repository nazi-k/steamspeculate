import re
import requests
import lib.db as db
from lib.db import NoHashName
from typing import Union
from steampy.models import SteamUrl, Currency, GameOptions


def get_item_orders_histogram(item_name_id: Union[str, int], currency: Currency = Currency.UAH) -> dict:
    url = SteamUrl.COMMUNITY_URL + '/market/itemordershistogram'
    params = {
        'language': 'ukrainian',
        'currency': currency.value,
        'item_nameid': item_name_id
    }
    return requests.get(url=url, params=params).json()


def get_percent_profit(buy: int, sell: int) -> float:
    return round(((((sell - (sell * 0.1303)) - buy) * 100) / buy), 2)


def get_item_name_id_with_html(html: str) -> str:
    return re.findall(r'Market_LoadOrderSpread\(\s*(\d+)\s*\)', html)[0]


def get_item_name_id(item_hash_name: str, game: GameOptions) -> str:
    table_name = get_table_name_with_game(game)
    item_name_id = db.get_item_name_id(item_hash_name, table_name)
    if item_name_id:
        return str(item_name_id)
    else:
        url = SteamUrl.COMMUNITY_URL + '/market/listings/' + game.app_id + '/' + item_hash_name
        item_name_id = get_item_name_id_with_html(requests.get(url).text)

        db.insert(table_name, {'item_nameid': int(item_name_id), 'hash_name': item_hash_name})

        return item_name_id


def convert_price_to_int(price: str) -> int:
    return int(float(re.findall(r'\d+\.\d{2}|\d+', price.replace(',', '.'))[0]) * 100)


def get_dollar_exchange_rate(currency: Currency = Currency.UAH) -> float:
    return round(int(get_item_orders_histogram(1, currency)['highest_buy_order']) /
                 int(get_item_orders_histogram(1, Currency.USD)['highest_buy_order']), 2)


def get_game_with_item_name(item_hash_name: str) -> GameOptions:
    game_name = db.get_game_name_with_item_name(item_hash_name)
    if not game_name:
        raise NoHashName(Exception, 'Item name is not identified in any table')
    elif game_name == 'DOTA2':
        return GameOptions.DOTA2
    elif game_name == 'TF2':
        return GameOptions.TF2
    else:
        print('get_game_with_item_name')
        raise


def get_table_name_with_game(game: GameOptions) -> str:
    if game == GameOptions.DOTA2:
        return 'DOTA2'
    elif game == GameOptions.TF2:
        return 'TF2'
    print('get_table_name_with_game')
    raise
