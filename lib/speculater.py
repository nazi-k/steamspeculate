import lib.auditor as auditor
import lib.utils as utils
from lib.models import Game
from lib.table_scraper import TableScraper
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
            self._update_wallet_balance()
        self._limit_of_allowed_orders = (self._int_wallet_balance * 10) - self._sum_all_buy_orders

    def _get_dollar_max_buy_price(self) -> float:
        int_dollar_exchange_rate = int(utils.get_dollar_exchange_rate() * 100)
        dollar_wallet_balance = self._int_wallet_balance / int_dollar_exchange_rate
        dollar_limit_of_allowed_orders = self._limit_of_allowed_orders / int_dollar_exchange_rate
        return dollar_wallet_balance if self._int_wallet_balance < self._limit_of_allowed_orders \
            else dollar_limit_of_allowed_orders

    def _get_sum_all_buy_orders(self) -> int:
        sum_all_buy_orders = 0
        for buy_order in self._get_buy_orders().values():
            sum_all_buy_orders += utils.convert_price_to_int(buy_order['price']) * buy_order['quantity']
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

    def _remove_item_name_in_buy_orders(self, item_name: str) -> None:
        try:
            self._items_name_in_buy_orders.remove(item_name)
        except ValueError:
            pass

    def _get_my_inventory_asset_id_end_item_name(self, game: GameOptions) -> list:
        return [(asset_id, values['name'])
                for asset_id, values in self._steam_client.get_my_inventory(game=game).items()]

    def if_profit_create_buy_order(self, item_hash_name: str, game: GameOptions, is_recursion: bool = False):
        if item_hash_name not in self._items_name_in_buy_orders:
            item_audit_info = auditor.get_profitability_info(item_hash_name, game, self._steam_client)
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
        self._scraper.set_max_price(self._get_dollar_max_buy_price())
        for game in self._games:
            items_hash_name = self._scraper.get_items_hash_name(game.table)
            for item_hash_name in items_hash_name:
                try:
                    self.if_profit_create_buy_order(item_hash_name, game.steam)
                except IndexError:
                    sleep(60 * 2)

    def cancel_non_profit_buy_orders(self):
        for buy_order in self._get_buy_orders().values():
            item_name = buy_order['item_name']
            try:
                game = utils.get_game_with_item_name(item_name)
            except utils.NoHashName:
                self._steam_client.market.cancel_buy_order(buy_order['order_id'])
                self._remove_item_name_in_buy_orders(item_name)
                #
                print(f'Cancel buy orders "{item_name}"')
                #
                continue
            buy_price = utils.convert_price_to_int(buy_order['price'])
            buy_order_audit_info = auditor.get_profitability_info(item_name, game, self._steam_client,
                                                                  buy_price=buy_price)
            if not buy_order_audit_info.is_profit:
                self._steam_client.market.cancel_buy_order(buy_order['order_id'])
                self._remove_item_name_in_buy_orders(item_name)
                #
                print(f'Cancel buy orders "{item_name}"')
                #
            elif buy_order_audit_info.number_buy_orders_before_this > 15:  # Алгоритм після скількох відміняти/підіймати ціну
                self._steam_client.market.cancel_buy_order(buy_order['order_id'])
                self._remove_item_name_in_buy_orders(item_name)
                #
                print(f'Cancel buy orders "{item_name}"')
                #
            sleep(3.5)
        self._update_limit_of_allowed_orders(update_sum_all_buy_orders=True)

    def cancel_non_competitive_sell_orders(self):
        pass

    def sell_all_inventory(self):
        for game in self._games:
            for asset_id, item_name in self._get_my_inventory_asset_id_end_item_name(game.steam):
                self._steam_client.market.create_sell_order(assetid=asset_id, game=game.steam,
                                                            money_to_receive=auditor.get_min_sell_price(item_name,
                                                                                                        game.steam))
                self._remove_item_name_in_buy_orders(item_name)
                #
                print(f'Create sell order "{item_name}"')
                #
        self._update_limit_of_allowed_orders(update_sum_all_buy_orders=True)

    def run(self):
        while True:
            self.cancel_non_profit_buy_orders()
            sleep(30)
            self.create_buy_orders()
            sleep(30)
            self.sell_all_inventory()
            sleep(30)
            self.cancel_non_competitive_sell_orders()
            sleep(30)
