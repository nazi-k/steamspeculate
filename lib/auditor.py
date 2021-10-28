import lib.utils as utils
from lib.models import ProfitabilityInfo
from steampy.client import SteamClient
from steampy.models import GameOptions, Currency
from steampy.exceptions import TooManyRequests
from time import sleep


def get_profitability_info(item_hash_name: str,
                           game: GameOptions,
                           steam_client: SteamClient,
                           buy_price: int = None,
                           min_percent_profit: int = 5,
                           currency: Currency = Currency.UAH) -> ProfitabilityInfo:
    try:
        median_price = utils.convert_price_to_int(
            steam_client.market.fetch_price(item_hash_name, game, currency)['median_price'])
    except TooManyRequests or KeyError:
        sleep(60 * 5)
        try:
            median_price = utils.convert_price_to_int(
                steam_client.market.fetch_price(item_hash_name, game, currency)['median_price'])
        except TooManyRequests or KeyError:
            return ProfitabilityInfo(False)

    item_name_id = utils.get_item_name_id(item_hash_name, game)
    histogram = utils.get_item_orders_histogram(item_name_id)

    lowest_sell_order = int(histogram['lowest_sell_order'])
    highest_buy_order = int(histogram['highest_buy_order']) + 1

    if buy_price is None:
        buy_price = highest_buy_order
    else:
        percent_profit = utils.get_percent_profit(buy_price, lowest_sell_order)
        number_buy_orders_before_this = get_number_buy_orders_before_this(buy_price, histogram)
        if percent_profit >= min_percent_profit:
            return ProfitabilityInfo(True, buy_price, percent_profit, number_buy_orders_before_this)
        else:
            return ProfitabilityInfo(False)

    percent_profit = utils.get_percent_profit(buy_price, lowest_sell_order)
    if percent_profit >= min_percent_profit and utils.get_percent_profit(buy_price, median_price) > 0:
        return ProfitabilityInfo(True, buy_price, percent_profit)
    else:
        return ProfitabilityInfo(False)


def get_number_buy_orders_before_this(price_this: int, histogram: dict):
    number_buy_orders_before_this = 0
    for buy_order_info in histogram['buy_order_graph']:
        if utils.convert_price_to_int(buy_order_info[2].replace(str(buy_order_info[1]), '', 1)) <= price_this:
            return number_buy_orders_before_this
        number_buy_orders_before_this += buy_order_info[1]
    print('get_number_buy_orders_before_this')
    raise  # Ордер відсутній


def get_min_sell_price(item_name: str, game: GameOptions = None) -> str:
    if not game:
        game = utils.get_game_with_item_name(item_name)
    item_name_id = utils.get_item_name_id(item_name, game)
    histogram = utils.get_item_orders_histogram(item_name_id)
    lowest_sell_order = int(histogram['lowest_sell_order'])
    min_sell_price = round(((lowest_sell_order - 1) * (1 - 0.1303)))
    return str(min_sell_price)
