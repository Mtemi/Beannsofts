from typing import Dict, Any, List, Optional
from app.src.services.OptionsBot.enums import State
from app.src.utils.binance.clientOriginal import Client as BinanceClient
from datetime import datetime, timedelta


class OptionsBot():
    """
    OptionsBot is the main class of the bot.
    This is from here the bot start its logic.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Init all variables and objects the bot needs to work
        :param config: configuration dict
        """
        self.tradingCoin: str

        self.Binance = BinanceClient(
            api_key=config["key"], api_secret=config["secret"])

        self.state = State.STOPPED

        self.config = config

        #  TODO implement strategy injectr class
        self.strategy

        self.walletBalance

        # TODO implement notifier for the webUI and telegram Bot
        self.notifier

        self.dataPovider

        self.botExpiryDate

    def notifyStatus(self, msg: str) -> None:
        pass

    def cleanUp(self) -> None:
        """Clean up, cancell all orders on bot begin"""

    def startUp(self) -> None:
        """ On bot init send notification and perform init actions"""

    def process(self) -> None:
        """Performs buys and sells"""

    def cancellOrders(self) -> None:
        self.Binance.options_cancel_all_orders({"symbol": self.tradingCoin})

    def getWalletBalance(self):
        balance = self.Binance.options_account_info()
        if balance:
            for coin in balance["data"]:
                if coin["currency"] in "BTCUSDT":
                    return {
                        "balance": coin["balance"]
                    }
                else:
                    return {
                        "balance": 0
                    }
        else:
            return "None"

    def refreshCandleData(self, symbol, timeFrame) -> None:
        """Refresh candle data with each cycle"""

    def createOrder(self) -> int:
        """ Execute buy orders for new trade
        1. analyze data from candlestick
        2. Check signal from Strategy.if buy perform buy, if sell perform sell.
        """

    def calculateExpiryDate(self, timePeriod: int) -> int:
        time = datetime.utcnow() + timedelta(days=+timePeriod)
        return time
    
    def isExpired(self) -> bool:
        if self.botExpiryDate == datetime.utcnow():
            return True
        else:
            return False
    

            
  
            
