import datetime
import copy
from time import sleep
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src.services import BinanceOps
from typing import Dict, List
from app.src.services.DCABot.strategy.StrategyResolver import StrategyResolver
from app.src.services.DCABot.DataProvider.provider import DataProvider
from app.src.services.Notifications.Notification import Notification
from app.src.models.dcabot import DCABotOrderModel
from app.src import db
from app.src.utils import logging

logger = logging.GetLogger(__name__)

event_name = 'dca-bot'
msginfo = 'info'
msgerror = 'error' 

class DCABot:
    def __init__(self, config: Dict[str, any]) -> None:
        self._config = config
        self.isActive = True
        self.msgTemp = {
            "msg": 'DCA Bot Starting...',
            "msgType": msginfo,
            "eventName": event_name,
            "channel": config['userid'],
            "chatId": config['chatid'],
            "kwargs": {'extra':'no info'}
        }
        
        if config['operation'] == 'binance':
            self.exchange = BinanceOps(
                api_key=config['key'], api_secret=config['secret'], trade_symbol="BTCUSDT")
        elif config['operation'] == 'binance-futures':
            self.exchange = BinanceFuturesOps(
                api_key=config['key'], api_secret=config['secret'], trade_symbol="BTCUSDT")
          
        self.dataprovider = DataProvider(config)

        self.rpc = Notification()
        # self.count = self.count

    def notifyStatus(self, msg):
        """
        Public method for users of this class (worker, etc.) to send notifications
        via RPC about changes in the bot status.
        """
        self.msgTemp.update({"msg": f'{self._config["botname"]} - DCA Bot Starting...'})
        self.rpc.sendNotification(self.msgTemp)
    
    def cleanup(self) -> None:
        """
        Cleanup pending resources on an already stopped bot
        :return: None
        """
        logger.debug('Cleaning up modules ...')
        self.msgTemp.update({
            "msg": f'{self._config["botname"]} - DCA Bot Cleaning up',
        })
        self.rpc.sendNotification(self.msgTemp)

        # Get all open orders
        openOrders = self.checkForOpenTrades()
        logger.debug('Current Open orders to cancel: %s', openOrders)
        if openOrders[0]: 
            # Remove all open orders from the bot
            logger.debug('All the initial open orders', openOrders[1])
            self.cancelOpenOrdersOnExit()

    def startup(self) -> None:
        """
        Called on startup and after loading the bot - triggers notifications and
        performs startup tasks
        """
        # TODO Initialize the stopLoss and takeprofit amount to trade on the DB then update the order on db

        botname = self._config['botname']
        side = self._config['side']
        stake_currency = self._config["pairlist"]
        stake_amount = self._config['qty']
        stoploss = self._config['stoploss']
        trailing_stop = self._config['trailing_stop']
        takeprofit = self._config['takeprofit']
        timeframe = self._config['timeframe']
        exchange_name = self._config['exchangename']
        strategy_name = self._config.get('strategy', '')

        # send initial startup messasge
        self.msgTemp.update({
            'msg':  f'*Bot Name:* `{botname}`\n'
                    f'*Strategy Side:* `{side}`\n'
                    f'*Exchange:* `{exchange_name}`\n'
                    f'*Stake per trade:* `{stake_amount} {stake_currency}`\n'
                    f'*{"Trailing " if trailing_stop else ""}Stoploss:* `{stoploss}`\n'
                    f'*Take profit:* `{takeprofit}`\n'
                    f'*Timeframe:* `{timeframe}`\n'
                    f'*Strategy:* `{strategy_name}`'
        })
        self.rpc.sendNotification(self.msgTemp)
        logger.debug("DCA Bot Started, Notifications sent")

        # self.count = self.count + 1

    def process(self):
        """
        Queries the persistence layer for open trades and handles them,
        otherwise a new trade is created.
        :return: True if one or more trades has been created or closed, False otherwise
        """

        # Reload and load candele data 
        self.dataprovider.reloadMarket()

        # Analyze the reloaded market data to get signals for buy and sell
        # self.strategy.analyze(self._config['pairlist'])
        logger.debug("Query for all open orders for the user and handle expired orders")
        # Query for all open orders for the user and handle expired orders
        openOrders = DCABotOrderModel.find_by_open_order(self._config['id'])
        logger.debug(f"Open Orders Found {openOrders}")
        if openOrders:
            # handle expired orders
            for order in openOrders:
                orderStatus = self.checkForBinanceOrderStatus(order.symbol, order.order_id)
                if orderStatus['status'] == "FILLED":
                    db.session.query(DCABotOrderModel).filter_by(order_id = order.order_id).update({
                        "status":"FILLED",
                        "is_open":False,
                        "filled_amt":orderStatus['executedQty'],
                        "remaining_amt":None,
                        "order_filled_date":datetime.datetime.utcnow(),
                        "order_update_date":datetime.datetime.utcnow(),
                        "order_timeout":None
                    })
                    db.session.commit()
                logger.debug(f"Order Status orderid: {order.order_id} status: {orderStatus['status']}")

            self.checkHandleTimeoutOrder(openOrders)
            
        # check for number of open orders slots available   
        logger.debug("Checking for number of order slots available")
        if self.getFreeOpenTrades(openOrders):
            tradesCreated = self.enterPosition(openOrders)
            logger.debug(f"Trades Created from process , enter Position {tradesCreated}")
            if self._config['interval_between_orders'] is not None:
                logger.debug(f"Sleeping for {self._config['interval_between_orders']} seconds, waiting to begin next order cycle")
                sleep(int(self._config['interval_between_orders']))

        else:
            logger.debug(f"No free slots for open orders")
            
    def enterPosition(self, openOrders: List) -> int:
        """
        Tries to execute buy or sell orders for new trades (positions)
        """
        tradesCreated = 0

        tradingPairs = copy.deepcopy(self._config["pairlist"])
        logger.debug(f'Enter position method, with trading pairs: {tradingPairs}')
        if not tradingPairs:
            logger.debug("Active pair whitelist is empty.")
            return tradesCreated

        # Checks if there are any open orders for symbols in paitlist and skip else place an order for that symbol
        for order in openOrders:
            if order.symbol in tradingPairs:
                tradingPairs.remove(order.symbol)
                logger.debug('Order %s is already open. Ignoring pair %s', order.symbol)
         
        # place orders for new trades
        for tradingPair in tradingPairs:

            logger.debug(f'Enter position method trying to create a trade for {tradingPair}')
            tradesCreated += self.createTrade(tradingPair)
        
        if not tradesCreated:
            logger.debug('No new trades have been created.Trying again...')
        
        return tradesCreated

    def createTrade(self, tradingPair: str) -> bool:
        """
        Check the implemented trading strategy for buy signals.

        If the pair triggers the buy signal a new trade record gets created
        and the buy-order opening the trade gets issued towards the exchange.
        :param: tradingPair: The token symbol to check for buy signals
        :return: True if a trade has been created.
        """
        logger.debug(f"create_trade for pair {tradingPair}")

        # Get analyzed dataframe for the pair
        analyzed_df = self.dataprovider.getAnalyzedDataframe(tradingPair, self._config['timeframe'])
        nowtime = analyzed_df.iloc[-1]['date'] if len(analyzed_df) > 0 else None
        
        # Query for all open orders for the user and handle expiered orders
        openOrders = DCABotOrderModel.find_by_open_order(self._config['id'])
        if not self.getFreeOpenTrades(openOrders):
            logger.debug(f"Can't open a new trade for {tradingPair}: max number of trades is reached.")
            return False
        # running get_signal on historical data fetched
        (buy, sell, buy_tag) = self.dataprovider.get_signal(
            tradingPair,
            self._config['timeframe'],
            analyzed_df
        )
        logger.debug(f"Signals from dataframe Buy: {buy}, Sell: {sell}, Buy Tag: {buy_tag}")

        qty = self._config['qty']

        logger.debug(f"Getting the last price for pair {tradingPair}")

        # Getting trading pair precision for both quantiy and price
        assetPrecision = self.getAssetPrecision(tradingPair)
        logger.debug(f"The asset precisions found {assetPrecision}")

        # Calculating the current price for asset
        lastPrice = self.exchange.round_decimals_down(self.getSymbolLastPrice(tradingPair), assetPrecision['pricePrecision'])

        # Calculating the correct quantity for use in binance order
        stakeAmt = self.exchange.round_decimals_down(self.getQuantityInQuoteAsset(qty, lastPrice), assetPrecision['qtyPrecision'])
 
        if buy and self._config['side'] == "SELL":
            logger.debug(f"Buy signal for pair {tradingPair} ignored because the bot is configured to only sell")
            return False
        
        if sell and self._config['side'] == "BUY":
            logger.debug(f"Sell signal for pair {tradingPair} ignore because the bot is confirgured to only buy")
            return False

        # Execute Buy
        if buy and not sell:
            qty = self._config['qty']
            
            ordertype = self._config['ordertype']
            side = self._config['side']
            logger.debug(f"Executing buy from signal")
            createStatus = self.executeOrder(tradingPair, side, ordertype, stakeAmt, nowtime)
            return createStatus

        # Execute Sell
        if sell and not buy:
            stakeAmt = self._config['qty']
            ordertype = self._config['ordertype']
            side = self._config['side']
            logger.debug(f"Executing sell from signal")
            createStatus = self.executeOrder(tradingPair, side, ordertype, stakeAmt, nowtime)
            return createStatus

        return False

    def executeOrder(self, pair: str, side: str, ordertype: str, qty: float, nowtime) -> None:
        """
        Execute the actual order on the exchange    
        :param pair: The sysmbol to trade on exchange
        :param side: The order side to trade, Buy or Sell
        :param qty: the quantity to trade for the coin symbol
        :param buy_tag: the buy signal tag
        :param nowtime: the current time
        :return: None
        """
        logger.debug(f"execute_order for pair {pair}")
         
        # Get the price of the symbol to trade
        price = self.exchange.round_decimals_down(self.getSymbolLastPrice(pair), self.getAssetPrecision(pair)['pricePrecision'])
        
        params = {
            "symbol": pair,
            "side": side.upper(),
            "type": ordertype.upper(),
            "quantity": qty
        }
        if ordertype.upper() == 'LIMIT':
            params.update({'price': price,'timeInForce':'GTC'})

        global orderResp
        
        if self._config['operation'] == 'binance':
            logger.debug(f"Executing a SPOT order on Binance for {pair} price: {price} order: {ordertype} quantity: {qty}")

            try:
                orderResp = self.exchange.create_order(**params)
            except Exception as e:
                orderResp = str(e)
                self.msgTemp.update({
                    "msg": f'{self._config["botname"]} - DCA Bot Enter Position Exception {e}',
                    "msgType": "error",
                })
                self.rpc.sendNotification(self.msgTemp)
                logger.error(f'FAILED! Exection of Spot order on Binance Failed with error:- {e}')
       
        if self._config['operation'] == 'binance-futures':
            logger.debug(f"Executing a FUTURES order on Binance for {pair} price: {price} order: {ordertype} quantity: {qty}")

            logger.debug(f"Setting leverage to {self._config['leverage']}")
            leverageResp = self.exchange.futures_set_leverage(symbol=pair, leverage=self._config['leverage'])
            logger.debug(f"Leverage Setting response: {leverageResp}")
            
            try:
                orderResp = self.exchange.create_futures_order(**params)
            except Exception as e:
                orderResp = str(e)
                self.msgTemp.update({
                    "msg": f'{self._config["botname"]} - DCA Bot Enter Position Exception {e}',
                    "msgType": "error",
                })
                self.rpc.sendNotification(self.msgTemp)
                logger.error(f'FAILED! Exection of Futures order on Binance Failed with error:- {e}')
        
        logger.debug(f"The order response is: {orderResp}")

        if not "invalid" in orderResp and not "APIError" in orderResp:
            orderId = orderResp['orderId']
            self.msgTemp.update({"msg": f"Bot {self._config['id']} created order for {pair} orderId {orderId} \n"
                        f"*Order side* {side} \n"
                        f"*Order amount* {qty} \n"
                        f"*Order price* {price} \n"
                        f"*Order Status* {orderResp['status']}" })
            self.rpc.sendNotification(self.msgTemp)

            order = DCABotOrderModel(
                bot_id=self._config['id'],
                order_id=orderId,
                user_id=self._config['userid'],
                symbol=pair,
                side=side,
                order_type=ordertype,
                qty=qty,
                price=price,
                status="CREATED",
                is_open=True,
                filled_amt=None,
                remaining_amt=None,
                order_date=nowtime,
                order_filled_date=None,
                order_update_date=None,
                order_timeout=None
            )
            logger.debug(f"Order created: {order}")
            db.session.add(order)
            db.session.commit()
            logger.debug(f"Order {orderId} for {pair} has been created.")
            
            # Update order on the database for filled order ordertypes
            if orderResp['status'] == "FILLED":
                logger.debug(f"Order {orderId} for {pair} has been filled.")
                self.msgTemp.update({"msg": f"Bot {self._config['id']} created order for {pair} orderId {orderId} \n"
                        f"*Order Status* {orderResp['status']}" })
                self.rpc.sendNotification(self.msgTemp)
                logger.debug(f"Order {orderId} for {pair} updating to database...")
                db.session.query(DCABotOrderModel).filter_by(order_id = orderId).update({
                    "status":"FILLED",
                    "is_open":False,
                    "filled_amt":None,
                    "remaining_amt":None,
                    "order_filled_date":datetime.datetime.utcnow(),
                    "order_update_date":datetime.datetime.utcnow(),
                    "order_timeout":None
                })
                db.session.commit()
                logger.debug(f"Order {orderId} for {pair} has been updated to database.")

                logger.debug("Initiating takeProfit handler...")
                self.handleTakeProfit(pair, side, qty, price)

            else:
                db.session.query(DCABotOrderModel).filter_by(order_id = orderId).update({
                    "status":"OPEN",
                    "is_open":False,
                    "filled_amt":None,
                    "remaining_amt":None,
                    "order_filled_date":datetime.datetime.utcnow(),
                    "order_update_date":datetime.datetime.utcnow(),
                    "order_timeout":None
                })
                logger.debug(f"Order {orderId} for {pair} is open.")

            return True

        # Order did not go through
        else:
            logger.error(f"Order of {pair} encountered error {orderResp}")
            self.msgTemp.update({"msg": f"Order of {pair} encountered error {orderResp}"})
            self.rpc.sendNotification(self.msgTemp)
            return False

    def checkForBinanceOrderStatus(self, pair: str, orderid: int) -> dict:
        params = {
            "symbol":pair,
            "orderId":orderid
        }
        if self._config['operation'] == 'binance':
            logger.debug(f"Checking for status on SPOT order on Binance for {pair} orderId: {orderid}")
            orderStatusResp = self.exchange.get_order(**params)
        
        if self._config['operation'] == 'binance-futures':
            logger.debug(f"Checking for status on SPOT order on Binance for {pair} orderId: {orderid}")
            orderStatusResp = self.exchange.futures_get_order(**params)
        
        return orderStatusResp
        

    def getAcctBalance(self, pair: str):
        params = {'asset': pair}
        logger.debug(f"get_acct_balance for pair {pair}")
        if self._config['operation'] == "binance":
            logger.debug(f"get_acct_balance for pair SPOT   ===== {pair}")     
            balance = self.exchange.get_asset_balance(**params)
            logger.debug(f"Balance for {pair} is {balance}")
            return balance
        if self._config['operation'] == "binance-futures":
            balances = self.exchange.futures_account_balance(**params)
            res = next(item["balance"] for item in balances if item["asset"] == pair)
            logger.debug(f"Balance for {pair} is {res}")
            return res

    def getFreeOpenTrades(self, openOrders: List) -> int:
        """
        Return the maximum number of open orders that can be done
        or 0 if the maximum number of open trades is reached
        :param openOrders: A List containing all open orders for the bot
        :return int: number of open trades slots available
        """
        openTrades = len(openOrders) 
        maxSlotsAvailable = max(0, self._config['max_active_trade_count'] - openTrades)
        logger.debug("Max order slots available: {}".format(maxSlotsAvailable))
        return maxSlotsAvailable

    def checkHandleTimeoutOrder(self, orders:List[dict]) -> None:
        """
        Check if any orders are timed out and cancel if necessary
        :param timeoutvalue: Number of minutes until order is considered timed out
        :return: None
        """
        for order in orders:
            if not order.order_timeout:
                continue

            timeNow = datetime.datetime.utcnow()
            if order.order_timeout >= timeNow:
                try:
                    db.session.query(DCABotOrderModel).filter_by(order_id = order.order_id).update({"status":"Cancelled - Timeout", "is_open":False})
                except Exception as e:
                    logger.error("unable to update cancellORder ")

                    if self._config['operation'] == 'binance':
                        params = {
                            "symbol": order.symbol,
                            "orderId": order.order_id
                        }
                        self.exchange.cancel_order(**params)

    def cancelOpenOrdersOnExit(self) -> None:
        """
        Cancel all orders that are currently open
        :return: None
        """
        DCABotOrderModel.cancel_bot_open_orders(self._config['id'])
        logger.debug('Clossing all open orders')

    def cancellAllOpenOrdersBinance(self) -> None:
        """
        Cancels all open orders for the user in Binance
        """
        if self._config['operation'] == 'binance':
            self.exchange.futures_cancel_all_open_orders()
        if self._config['operation'] == 'binance-futures':
            orders = self.get_open_orders()
            for order in orders:
                orderresp = self.exchange.cancel_order(order['orderId'])
                if orderresp['status'] == 'ok':
                    logger.debug(f'Order {order["orderId"]} symbol {order["symbol"]} cancelled')
                else:
                    logger.error(f'Error cancelling order {order["orderId"]}')

    def checkForOpenTrades(self):
        """
        Notify the user when the bot is stopped
        and there are still open trades active.
        """
        open_trades = DCABotOrderModel.get_open_bot_orders(self._config['id'])

        if len(open_trades) != 0:
            self.msgTemp.update({"msg": f"{len(open_trades)} open trades active.\n\n"
                f"Handle these trades manually on Binance, "})
            self.rpc.sendNotification(self.msgTemp)
            return (True, open_trades)
        
        return (False, None)

    def handleTakeProfit(self, pair: str, side: str, amt: float, price: float):
        """ If the order was a sell handle handle a takeprofit buy order
            If the order was a buy handle handle a takeprofit sell order
            -- Check for the recent filled order and handle the takeprofit order in the opposite direction
            -- Background task to handle this checking for the recent filled order and handle the takeprofit order in the opposite direction
        """

        pricePrecision = self.getAssetPrecision(pair)['pricePrecision']

        price = self.getLimitPriceForTakeProfitHander(price, self._config['takeprofit'], pricePrecision, side) 
        logger.debug(f"Prrice for takeprofit handler for symbol {pair} is {price} with side as {side}")

        params = {
            "symbol": pair,
            "type": "LIMIT",
            "quantity": amt,
            "price": price,
            'timeInForce':'GTC'
        }

        if self._config['operation'] == 'binance':
            if side == "BUY":
                params.update({"side":"SELL"})
                orderResp = self.exchange.create_order(**params)
                logger.debug(f"Created a SPOT limit takeprofit order for {pair} side: SELL amt: {amt} price: {price} and order resp {orderResp}")
            if side == "SELL":
                params.update({"side":"BUY"})
                orderResp = self.exchange.create_order(**params)
                logger.debug(f"Created a SPOT limit takeprofit order for {pair} side: BUY amt: {amt} price: {price} and order resp {orderResp}")
                
        if self._config['operation'] == 'binance-futures':
            if side == "BUY":
                params.update({"side":"SELL"})
                orderResp = self.exchange.futures_create_order(**params)
                logger.debug(f"Created a FUTURES limit takeprofit order for {pair} side: SELL  amt: {amt} price: {price} and order resp {orderResp}")
            if side == "SELL":
                params.update({"side":"BUY"})
                orderResp = self.exchange.futures_create_order(**params)
                logger.debug(f"Created a FUTURES limit takeprofit order for {pair} side: BUY  amt: {amt} price: {price} and order resp {orderResp}")
        
        if not "invalid" in orderResp and not "APIError" in orderResp:
            orderId = orderResp['orderId']
            self.msgTemp.update({"msg": f"Bot {self._config['id']} created TakeProfit order for {pair} orderId {orderId} \n"
                        f"*Order side* {side} \n"
                        f"*Order price* {price} \n"
                        f"*Order Status* {orderResp['status']}" })
            self.rpc.sendNotification(self.msgTemp)

            order = DCABotOrderModel(
                bot_id=self._config['id'],
                order_id=orderResp['orderId'],
                user_id=self._config['userid'],
                symbol=pair,
                side=side,
                order_type="TAKEPROFIT-LIMIT",
                qty=amt,
                price=price,
                status="CREATED",
                is_open=True,
                filled_amt=None,
                remaining_amt=None,
                order_date=datetime.datetime.utcnow(),
                order_filled_date=None,
                order_update_date=None,
                order_timeout=None
            )
            db.session.add(order)
            db.session.commit()
        else:
            logger.debug(f"Take Profit Order did not execute error occured.......")
            self.msgTemp.update({"msg": f"Bot {self._config['id']} failed to create a TakeProfit order for {pair} error {str(orderResp)}"})
            self.rpc.sendNotification(self.msgTemp)
    
    def increasePriceByPercentage(self, percentage: float, price: float) -> float:
        """
        Increase the price by a percentage
        :param percentage: Percentage to increase the price by
        :param price: Price to increase
        :return: New price
        """
        return price * (1 + percentage)

    def getQuantityInQuoteAsset(self, qty: int, price: float) -> float:
        """
        Get the quantity in the quote asset
        :param qty: Quantity to convert
        :param price: Price to convert , current exchange rate of symbol
        :param pair: Pair to convert
        :return: Quantity in quote asset
        """
        return qty / price
    
    def getSymbolLastPrice(self, symbol: str) -> float:
        # params= { 'symbol':'BTC'}
        logger.debug(f"Getting the symbol last price for symbol {symbol}")
        params = {'symbol': symbol}
        try:
            if self._config['operation'] == 'binance':
                res = self.exchange.get_symbol_ticker(**params)
                logger.debug(f"last price res: {res}")
                lPrice = float(res['price'])
                logger.debug(f"Found the last price for symbol {symbol} as {lPrice}")
                return lPrice

            if self._config['operation'] == 'binance-futures':
                res = self.exchange.futures_symbol_ticker(**params)
                logger.debug(f"last price res: {res}")
                lPrice = float(res['price'])
                logger.debug(f"Found the last price for symbol {symbol} as {lPrice}")
                return lPrice

        except Exception as e:
            logger.debug(f"ERROR! Getting the symbol last price for symbol {symbol} has exception {e}")
            return e
    
    def getLimitPriceForTakeProfitHander(self, price: float, percentVal: int, pricePrecision: int, side: str) -> float:
        if side == "SELL":
            limitPrice = round(price - (float(percentVal)/100) * price, 8)
            return float(self.exchange.round_decimals_down(limitPrice, pricePrecision))

        elif side == "BUY":
            limitPrice = round(price + (float(percentVal)/100) * price, 8)
            return float(self.exchange.round_decimals_down(limitPrice, pricePrecision))  
    
    def getAssetPrecision(self, symbol: str) -> dict:
        logger.debug(f"Getting asset precisin for {symbol}")
        assetSymbol = symbol
        if self._config['operation'] == 'binance':
            info = self.exchange.get_exchange_info()

            stepSize = ''
            tickSize = ''

            for i in range(len(info['symbols'])):
                if assetSymbol == info['symbols'][i]['symbol']:
                    for x in range(len(info['symbols'][i]['filters'])):
                        if info['symbols'][i]['filters'][x]['filterType'] == 'LOT_SIZE':
                            stepSize = info['symbols'][i]['filters'][x]['stepSize']

                        if info['symbols'][i]['filters'][x]['filterType'] == 'PRICE_FILTER':
                            tickSize = info['symbols'][i]['filters'][x]['tickSize']

            pricePrecision = self.exchange.precisionValueCalc(float(tickSize))
            qtyPrecision = self.exchange.precisionValueCalc(float(stepSize))

            logger.debug(f"Found the price precision: {pricePrecision} and quantity precision: {qtyPrecision}")

            return {"pricePrecision": pricePrecision, "qtyPrecision": qtyPrecision}

        if self._config['operation'] == 'binance-futures':
            info = self.exchange.futures_exchange_info()

            pricePrecision = 0
            quantityPrecision = 0

            for i in range(len(info['symbols'])):
                if assetSymbol == info['symbols'][i]['symbol']:
                    pricePrecision = int(info['symbols'][i]['pricePrecision'])
                    quantityPrecision = int(info['symbols'][i]['quantityPrecision'])
            
            logger.debug(f"Found the price precision: {pricePrecision} and quantity precision: {quantityPrecision}")

            return {"pricePrecision": pricePrecision, "qtyPrecision": quantityPrecision}