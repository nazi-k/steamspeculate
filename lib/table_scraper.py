import re
import requests
from bs4 import BeautifulSoup
from lib.models import TableGame, TableService


class TableScraper:

    def __init__(
            self,
            phpsessid: str,
            service1: TableService = TableService.STEAM_AUTO,
            service2: TableService = TableService.STEAM,
            low_price: float = 0.1,
            max_price: float = 10000,
            sales_steam: int = 100,
            low_percent_profit: int = 5,
            **kwargs) -> None:

        self._settings = {
            'service1': service1,
            'service2': service2,
            'low_price': low_price,
            'max_price': max_price,
            'low_percent_profit': low_percent_profit,
            'sales_steam': sales_steam
        }

        for key, values in kwargs.items():
            self._settings[key] = values

        self._session = requests.Session()
        self._session.cookies.set(name="PHPSESSID", value=phpsessid)

    def _get_params(self, game: TableGame) -> dict:
        return {
            'ItemsFilter[knife]': 1,
            'ItemsFilter[stattrak]': 1,
            'ItemsFilter[souvenir]': 1,
            'ItemsFilter[sticker]': 1,
            'ItemsFilter[type]': game.type,
            'ItemsFilter[service1]': game.service_prefix + self._settings['service1'],
            'ItemsFilter[service2]': game.service_prefix + self._settings['service2'],
            'ItemsFilter[unstable1]': 1,
            'ItemsFilter[unstable2]': 1,
            'ItemsFilter[hours1]': 192,
            'ItemsFilter[hours2]': 192,
            'ItemsFilter[priceFrom1]': self._settings['low_price'],
            'ItemsFilter[priceTo1]': self._settings['max_price'],
            'ItemsFilter[priceFrom2]': '',
            'ItemsFilter[priceTo2]': '',
            'ItemsFilter[salesBS]': '',
            'ItemsFilter[salesTM]': '',
            'ItemsFilter[salesST]': self._settings['sales_steam'],
            'ItemsFilter[name]': '',
            'ItemsFilter[service1Minutes]': 30,
            'ItemsFilter[service2Minutes]': 30,
            'ItemsFilter[percentFrom1]': self._settings['low_percent_profit'],
            'ItemsFilter[percentFrom2]': '',
            'ItemsFilter[timeout]': 5,
            'ItemsFilter[service1CountFrom]': 1,
            'ItemsFilter[service1CountTo]': '',
            'ItemsFilter[service2CountFrom]': 1,
            'ItemsFilter[service2CountTo]': '',
            'ItemsFilter[percentTo1]': '',
            'ItemsFilter[percentTo2]': '',
            'refreshonoff': '',
            'per-page': 30
        }

    def set_settings(self, **kwargs) -> None:
        for key, values in kwargs.items():
            self._settings[key] = values

    def set_max_price(self, max_price: float) -> None:
        self.set_settings(max_price=max_price)

    def _get_page(self, page: int, game: TableGame) -> str:
        url = "https://table.altskins.com/ru/site/items"
        params = self._get_params(game)
        params['page'] = page
        return self._session.get(url=url, params=params).text

    def get_items_hash_name(self, game: TableGame) -> set:
        page = 1
        items_hash_name = set()
        while True:
            bs = BeautifulSoup(self._get_page(page, game), 'html.parser')
            tags_with_url = bs.find_all('a', {'href': re.compile(r'https://steamcommunity\.com')})
            items_hash_name_on_page = \
                set(map(lambda item_hash_name: item_hash_name['href'].split('/')[-1], tags_with_url))

            items_hash_name |= items_hash_name_on_page

            if len(items_hash_name_on_page) < 30:
                break
            if items_hash_name_on_page <= items_hash_name:
                break
            page += 1

        return items_hash_name
