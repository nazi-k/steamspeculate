import re
import requests
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
    return (((sell - (sell * 0.1303)) - buy) * 100) / buy


def get_item_name_id_with_html(html: str) -> str:
    return re.findall(r'Market_LoadOrderSpread\(\s*(\d+)\s*\)', html)[0]


def get_item_name_id(item_hash_name: str, game: GameOptions) -> str:
    url = SteamUrl.COMMUNITY_URL + '/market/listings/' + game.app_id + '/' + item_hash_name
    return get_item_name_id_with_html(requests.get(url).text)


def convert_price_to_int(price: str) -> int:
    return int(float(re.findall(r'\d+\.\d{2}|\d+', price.replace(',', '.'))[0]) * 100)


def get_dollar_exchange_rate(currency: Currency = Currency.UAH) -> float:
    return round(int(get_item_orders_histogram(1, currency)['highest_buy_order']) /
                 int(get_item_orders_histogram(1, Currency.USD)['highest_buy_order']), 2)
