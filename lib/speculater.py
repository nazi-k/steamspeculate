from lib.auditor import get_profitability_info
from lib.models import Game
from lib.table_scraper import TableScraper
from lib.utils import get_dollar_exchange_rate, convert_price_to_int
from os import getenv
from steampy.client import SteamClient
from steampy.models import GameOptions, Currency
from steampy.exceptions import ApiException
from time import sleep


class Speculater:

    def __init__(self, steam_client: SteamClient,
                 phpsessid: str = getenv('PHPSESSID'),
                 currency: Currency = Currency.UAH) -> None:
        self._steam_client = steam_client
        self.currency = currency
        self._games = [Game.TF2, Game.DOTA2]

        self._int_wallet_balance: int
        self._limit_of_allowed_orders: int

        self._items_name_in_buy_orders = self._get_items_name_in_buy_orders()
        self._sum_all_buy_orders = self._get_sum_all_buy_orders()

        self._update_wallet_balance()
        self._update_limit_of_allowed_orders()

        self._scraper = TableScraper(phpsessid, max_price=self._get_dollar_max_buy_price())

    def _update_wallet_balance(self):
        self._int_wallet_balance = int(self._steam_client.get_wallet_balance() * 100)

    def _update_limit_of_allowed_orders(self, update_sum_all_buy_orders: bool = False):
        if update_sum_all_buy_orders:
            self._sum_all_buy_orders = self._get_sum_all_buy_orders()
        self._limit_of_allowed_orders = (self._int_wallet_balance * 10) - self._sum_all_buy_orders

    def _get_dollar_max_buy_price(self) -> float:
        dollar_exchange_rate = int(get_dollar_exchange_rate() * 10)
        dollar_wallet_balance = self._int_wallet_balance / dollar_exchange_rate
        dollar_limit_of_allowed_orders = self._limit_of_allowed_orders / dollar_exchange_rate
        return dollar_wallet_balance if self._int_wallet_balance > self._limit_of_allowed_orders \
            else dollar_limit_of_allowed_orders

    def _get_sum_all_buy_orders(self) -> int:
        sum_all_buy_orders = 0
        for buy_order in self._get_buy_orders().values():
            sum_all_buy_orders += convert_price_to_int(buy_order['price']) * buy_order['quantity']
        return sum_all_buy_orders

    def _get_items_name_in_buy_orders(self) -> list:
        return [buy_order['item_name'] for buy_order in self._get_buy_orders().values()]

    def _get_buy_orders(self) -> dict:
        return self._steam_client.market.get_my_market_listings()['buy_orders']

    # поки не використовується
    def _get_sell_listings(self) -> dict:
        return self._steam_client.market.get_my_market_listings()['sell_listings']

    def _add_item_name_in_buy_orders(self, item_name: str) -> None:
        self._items_name_in_buy_orders.append(item_name)

    # поки не використовується
    def _get_my_inventory_items_value(self, game: GameOptions, key: str) -> list:
        return [item[key] for item in self._steam_client.get_my_inventory(game=game).values()]

    def _get_my_inventory_items_name_id(self, game: GameOptions) -> list:
        return [item_name_id for item_name_id in self._steam_client.get_my_inventory(game=game).keys()]

    def if_profit_create_buy_order(self, item_hash_name: str, game: GameOptions, is_recursion: bool = False):
        if item_hash_name not in self._items_name_in_buy_orders:
            item_audit_info = get_profitability_info(item_hash_name, game, self._steam_client, currency=self.currency)
            #####
            print(item_hash_name, end='')
            #####
            try:
                if (self._int_wallet_balance >= item_audit_info.buy_price) and item_audit_info.is_profit:
                    #####
                    print(':', item_audit_info.buy_price, end='')
                    #####
                    try:
                        self._steam_client.market.create_buy_order(
                            market_name=item_hash_name,
                            price_single_item=str(item_audit_info.buy_price),
                            quantity=item_audit_info.quantity,
                            game=game,
                            currency=self.currency)

                        self._add_item_name_in_buy_orders(item_hash_name)
                        self._sum_all_buy_orders += item_audit_info.buy_price
                        self._update_limit_of_allowed_orders()
                    except ApiException:
                        self._update_wallet_balance()
                        self._update_limit_of_allowed_orders(update_sum_all_buy_orders=True)
                        dollar_max_buy_price = self._get_dollar_max_buy_price()
                        if dollar_max_buy_price < 0.1:
                            pass  # треба виходити нічого не купиш
                        else:
                            self._scraper.set_max_price(dollar_max_buy_price)
                    finally:
                        sleep(4)
                sleep(3)
                #####
                print()
                #####
            except IndexError:
                if is_recursion:
                    return
                sleep(60 * 5)
                self.if_profit_create_buy_order(item_hash_name, game, True)
                return

    def create_buy_orders(self):
        self._update_wallet_balance()
        for game in self._games:
            items_hash_name = self._scraper.get_items_hash_name(game.table)
            for item_hash_name in items_hash_name:
                try:
                    self.if_profit_create_buy_order(item_hash_name, game.steam)
                except IndexError:
                    sleep(60 * 2)

    def sell_all_inventory(self):
        for game in self._games:
            for item_name_id in self._get_my_inventory_items_name_id(game.steam):
                self._steam_client.market.create_sell_order(assetid=item_name_id, game=game.steam,
                                                            money_to_receive='100000')  # Добавити за якою ціною продати

# видалити з _items_name_in_buy_orders і відняти від _sum_all_buy_orders якщо щось купилось(появилось в інвентарі)
