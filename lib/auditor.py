import lib.utils as utils
from lib.models import ProfitabilityInfo
from steampy.client import SteamClient
from steampy.models import GameOptions, Currency


def get_profitability_info(item_hash_name: str,
                           game: GameOptions,
                           steam_client: SteamClient,
                           min_percent_profit: int = 5,
                           currency: Currency = Currency.UAH) -> ProfitabilityInfo:

    median_price = utils.convert_price_to_int(
        steam_client.market.fetch_price(item_hash_name, game, currency)['median_price'])

    item_name_id = utils.get_item_name_id(item_hash_name, game)
    histogram = utils.get_item_orders_histogram(item_name_id)

    highest_buy_order = int(histogram['highest_buy_order']) + 1
    lowest_sell_order = int(histogram['lowest_sell_order'])

    if utils.get_percent_profit(highest_buy_order, lowest_sell_order) >= min_percent_profit and \
            utils.get_percent_profit(highest_buy_order, median_price) > 0:
        return ProfitabilityInfo(True, highest_buy_order)
    else:
        return ProfitabilityInfo(False, 0)
