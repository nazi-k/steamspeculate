from collections import namedtuple
from steampy.models import GameOptions


class TableGame:
    PredefinedOptions = namedtuple('PredefinedOptions', ['type', 'service_prefix'])

    CS = PredefinedOptions(1, '')
    DOTA2 = PredefinedOptions(2, 'd_')
    Z1BR = PredefinedOptions(3, 'h_')
    RUST = PredefinedOptions(4, 'r_')
    TF2 = PredefinedOptions(5, 'tf_')

    def __init__(self, type: int, service_prefix: str) -> None:
        self.type = type
        self.service_prefix = service_prefix


class Game:
    PredefinedOptions = namedtuple('PredefinedOptions', ['table', 'steam'])

    CS = PredefinedOptions(TableGame.CS, GameOptions.CS)
    DOTA2 = PredefinedOptions(TableGame.DOTA2, GameOptions.DOTA2)
    TF2 = PredefinedOptions(TableGame.TF2, GameOptions.TF2)

    def __init__(self, table: TableGame, steam: GameOptions) -> None:
        self.table = table
        self.steam = steam


class TableService:
    BITSKINS = 'showbs'
    BITSKINS_AUTO = "showbsa"
    BITSKINS_7 = "showbs7"
    BITSKINS_LS = "showbss"
    DMARKET = "showdma"
    MARKET_CSGO = "showtm"
    MARKET_CSGO_AUTO = "showtma"
    MARKET_CSGO_LS = "showtmls"
    STEAM = "showsteam"
    STEAM_AUTO = "showsteama"
    STEAM_LS = "showsteamls"


class ProfitabilityInfo:
    is_profit: bool
    buy_price: int

    def __init__(self, is_profit: bool, buy_price: int) -> None:
        self.is_profit = is_profit
        self.buy_price = buy_price
        self.quantity = 1  # алгоритм по кількості купівлі
