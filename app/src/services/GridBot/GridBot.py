from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
import time
import json
import requests
from app.src.services import BinanceOps
from app.src.services.GridBot.Helpers import OrderStatus
from app.src.services.Notifications.Notification import Notification
from app.src.utils import logging
import redis
import pickle
from app.src.utils.binance.streams import ThreadedWebsocketManager
from app.src.models import GridBotModel
from app.src.config import Config
from app.src import db

logger = logging.GetLogger(__name__)

event_name = 'grid-bot'
msginfo = 'info'
msgerror = 'error'


class GridBot():
    def __init__(self, params):
        self.params = params
        self.userId = params['user_id']
        self.botID = params['bot_id']
        self.chatId = params['chatId']
        self.botName = params['botName']
        self.key = params['key']
        self.secret = params['secret']
        self.symbol = params['symbol']
        self.upperLimitPrice = params['upperLimitPrice']
        self.lowerLimitPrice = params['lowerLimitPrice']
        self.gridQty = params['gridQty']
        # self.BinanceOps = BinanceOps(
        #     api_key=params['key'], api_secret=params['secret'], trade_symbol=params['symbol'])

        self.operation = params['operation']

        if params['operation'] == 'binance':
            self.BinanceOps = BinanceOps(
                api_key=self.key, api_secret=self.secret, trade_symbol=self.symbol)
        elif params['operation'] == 'binance-futures':
            self.BinanceOps = BinanceFuturesOps(
                api_key=self.key, api_secret=self.secret, trade_symbol=self.symbol)

        self.pricePrecision = self.BinanceOps.pricePrecision
        self.qtyPrecision = self.BinanceOps.qtyPrecision
        self.BuyOrders = []
        self.SellOrders = []

        # self.redisConn = redis.StrictRedis(Config.REDIS_URL)
        self.redisConn = redis.from_url(Config.REDIS_URL)

        self.rpc = Notification()

        self.msgTemp = {
            "msg": 'GRID Bot Starting...',
            "msgType": msginfo,
            "eventName": event_name,
            "channel": self.userId,
            "chatId": self.chatId,
            "kwargs": {'extra': 'no info'}
        }
        logger.info("point")

        self.msgTemp.update({"msg": f'{self.botName} - Grid Bot Starting...'})
        self.rpc.sendNotification(self.msgTemp)
    # Creating the grids and additing the data as a json in the database

    def pricePointsCalculator(self):
        """
        Calculates all the grids based on the data passed by the upperLimit, lowerlimit adn gridQty
        """

        currentPrice = self.BinanceOps.getLastPrice()
        try:
            float(currentPrice)
            gridGap = currentPrice - self.lowerLimitPrice
            priceGap = gridGap / (self.gridQty/2)
            lowerPricePoints = [currentPrice]
            upperPricePoints = [currentPrice]

            # lower grid price points
            for i in range((int(self.gridQty/2 - 2))):
                lowerPricePoints.append(lowerPricePoints[i]-priceGap)
            lowerPricePoints.append(self.lowerLimitPrice)

            # upper grid price points
            for i in range((int(self.gridQty/2 - 2))):
                upperPricePoints.append(upperPricePoints[i]+priceGap)
            upperPricePoints.append(self.upperLimitPrice)

            # The n number of grids - upper and lower grids combined
            new_list = upperPricePoints + lowerPricePoints

            db.session.query(GridBotModel).filter_by(
                id=self.botID).update({"gridPoints": new_list})
            db.session.commit()
            logger.info(f"Grids Computed successifully.")
            return True
        except Exception:
            logger.error(f'Failed,{currentPrice}')
            return False

    def getGrids(self):
        """
        Fetch the grids from the database
        """
        bot = db.session.query(GridBotModel).filter_by(id=self.botID).first()
        grids = bot.gridPoints
        return grids

    def priceBasedGridSplitter(self, price):
        """
        This method splits the grids the grids to sell grids and buy grids  based on the current price
        sorts to determine the price position based on the current price
        """
        grids = self.getGrids()

        sellGrids = []
        buyGrids = []

        for i in grids:
            if i > price:
                sellGrids.append(i)
            elif i < price:
                buyGrids.append(i)
        logger.info("The buy and sell grids splitted successfully")

        return [sorted(sellGrids), sorted(buyGrids, reverse=True)]

    def checkSellOrdersExecuted(self, previousSellprices, price):
        """
        Checks  the already executed limit orders for Sell based on price current position and the previous grid positions.

        """
        executed = None
        for i in previousSellprices:
            if price >= i:
                executed = i
                break
            else:
                pass
        return executed

    def checkBuyOrdersExecuted(self, previousBuyprices, price):
        """
        Checks  the already executed limit orders for Buy based on price current position and the previous grid positions.

        """
        executed = None
        for i in previousBuyprices:
            if price <= i:
                executed = i
                break
            else:
                pass
        return executed

    def trader(self, price, botName):
        """
        Receives the live price from the websocket and consolidates all the grid bot helper to get the trade signals and perform trade  

        """
        buyOrders = []
        sellOrders = []

        # sellPoints at index 0 buypoints index 1
        pricePoints = self.priceBasedGridSplitter(price)

        # print("The grid Price points", pricePoints)
        logger.info("GRID LAYOUT")
        logger.info(pricePoints)

        # These are the potential buy and sell points based on the previous price calculated 0 sells  and 1 buys

        sellPoints = pricePoints[0]
        buyPoints = pricePoints[1]

        # The price is currently between these two set of grids place a buy order from the sell grids and  buy from the buy pricePoints
        buyOrderPrice = buyPoints[0]
        sellOrderPrice = sellPoints[0]

        # Get the previous saved grids from the redis store. The botName is the key for storing the previous set of grids
        previousValueGrids = self.redisConn.get(botName)
        if previousValueGrids == None:
            # This is the first run for the grid bot take the immmediate  buy and sell point.
            sellOrders.append(sellOrderPrice)
            buyOrders.append(buyOrderPrice)

            # ------------Calling the sell and buy order function-------------------------
            try:
                self.sellOrderPlacer(sellOrderPrice)
            except Exception as e:
                logger.error("Sell order not placed", str(e))
            try:
                self.buyOrderPlacer(buyOrderPrice)
            except Exception as e:
                logger.error("Buy order not placed", str(e))

            previousValueGrids = [sellOrders, buyOrders]
            self.redisConn.set(botName, pickle.dumps(previousValueGrids))
            logger.info(
                f"Performed intial sell and buy limit orders on the immediate grid levels: SELL@{sellOrderPrice} BUY@{buyOrderPrice}")
            logger.info(
                f"Traking orders LIMIT SELL@{sellOrders} LIMIT BUY@{buyOrders}")

            msg1 = f"Performed intial sell and buy limit orders on the immediate grid levels: SELL@{sellOrderPrice} BUY@{buyOrderPrice}"
            self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
            self.rpc.sendNotification(self.msgTemp)

            msg2 = f"Traking orders LIMIT SELL@{sellOrders} LIMIT BUY@{buyOrders}"
            self.msgTemp.update({"msg": f'{self.botName} - {msg2}'})
            self.rpc.sendNotification(self.msgTemp)

            logger.info("Price points on monitor")
            logger.info(previousValueGrids)

        else:
            # load the json data from byte to dictionary
            previousValueGrids = pickle.loads(previousValueGrids)

            logger.info("Price points on monitor")
            logger.info(previousValueGrids)

            sellOrdersStored = previousValueGrids[0]
            buyOrdersStored = previousValueGrids[1]

            sellexecuted = self.checkSellOrdersExecuted(
                sellOrdersStored, price)

            if sellexecuted:
                logger.info(
                    f"LIMIT SELL@{sellexecuted} already executed clearing it from monitor")

                sellOrdersStored.remove(sellexecuted)

                logger.info(f"LIMIT SELL@{sellexecuted} cleared from monitor")
                if len(sellPoints) != 0 and sellPoints[0] not in sellOrdersStored:
                    logger.info(f" Performing new SELL@{sellPoints[0]}")

                    # self.sellOrderPlacer(sellPoints[0])

                    try:
                        self.sellOrderPlacer(sellPoints[0])
                    except Exception as e:
                        logger.error("Sell order not placed", str(e))
                    sellOrdersStored.append(sellPoints[0])
                    msg1 = f" Performing new SELL@{sellPoints[0]}"
                    self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
                    self.rpc.sendNotification(self.msgTemp)

                else:

                    logger.info(
                        f"LIMIT SELL@{sellPoints[0]} already on monitor")
                    msg2 = f"LIMIT SELL@{sellPoints[0]} already on monitor"
                    self.msgTemp.update({"msg": f'{self.botName} - {msg2}'})
                    self.rpc.sendNotification(self.msgTemp)

                if len(buyPoints) >= 2 and buyPoints[1] not in buyOrdersStored:
                    logger.info(f"Perfoming BUY complimentary @{buyPoints[1]}")

                    buyOrdersStored.append(buyPoints[1])
                    # self.buyOrderPlacer(buyPoints[1])

                    try:
                        self.buyOrderPlacer(buyPoints[1])
                    except Exception as e:
                        logger.error("Buy order not placed", str(e))

                    msg1 = f"Perfoming BUY complimentary @{buyPoints[1]}"
                    self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
                    self.rpc.sendNotification(self.msgTemp)
                else:
                    logger.info(f"LIMIT BUY@{buyPoints[1]} already on monitor")
                    msg2 = f"LIMIT BUY@{buyPoints[1]} already on monitor"
                    self.msgTemp.update({"msg": f'{self.botName} - {msg2}'})
                    self.rpc.sendNotification(self.msgTemp)

                previousValueGrids = [sellOrdersStored, buyOrdersStored]
                self.redisConn.set(botName, pickle.dumps(previousValueGrids))

                logger.info("Price points on monitor")
                logger.info(previousValueGrids)

            buyexecuted = self.checkBuyOrdersExecuted(buyOrdersStored, price)

            if buyexecuted:
                # print("Buying point")
                # print(f"buying at {buyPoints[0]}")
                # print(f"selling at {sellPoints[1]}")
                logger.info(
                    f"LIMIT BUY@{buyexecuted} already executed clearing it from monitor")
                msg1 = f"LIMIT BUY@{buyexecuted} already executed clearing it from monitor"
                self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
                self.rpc.sendNotification(self.msgTemp)
                buyOrdersStored.remove(buyexecuted)

                logger.info(f"LIMIT BUY@{buyexecuted} cleared from monitor")
                msg1 = f"LIMIT BUY@{buyexecuted} cleared from monitor"
                self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
                self.rpc.sendNotification(self.msgTemp)

                if len(buyPoints) != 0 and buyPoints[0] not in buyOrdersStored:
                    logger.info(f"Performing new BUY @{buyPoints[0]}")
                    msg1 = f"Performing new BUY @{buyPoints[0]}"
                    self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
                    self.rpc.sendNotification(self.msgTemp)

                    # self.buyOrderPlacer(buyPoints[0])

                    try:
                        self.buyOrderPlacer(buyPoints[0])
                    except Exception as e:
                        logger.error("Buy order not placed", str(e))

                    buyOrdersStored.append(buyPoints[0])

                else:
                    logger.info(
                        f"Perfoming Complemntary LIMIT SELL@{buyPoints[1]} already on monitor")
                    msg1 = f"Perfoming Complemntary LIMIT SELL@{buyPoints[1]} already on monitor"
                    self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
                    self.rpc.sendNotification(self.msgTemp)
                if len(sellPoints) > 2 and sellPoints[1] not in sellOrdersStored:
                    sellOrdersStored.append(sellPoints[1])
                    # self.sellOrderPlacer(sellPoints[1])
                    try:
                        self.sellOrderPlacer(sellPoints[1])
                    except Exception as e:
                        logger.error("Sell order not placed", str(e))

                else:
                    logger.info(
                        f"LIMIT SELL@{sellPoints[1]} already on monitor")
                    msg1 = f"LIMIT SELL@{sellPoints[1]} already on monitor"
                    self.msgTemp.update({"msg": f'{self.botName} - {msg1}'})
                    self.rpc.sendNotification(self.msgTemp)

                previousValueGrids = [sellOrdersStored, buyOrdersStored]
                self.redisConn.set(botName, pickle.dumps(previousValueGrids))

                logger.info("Price points on monitor")
                logger.info(previousValueGrids)

    def priceStream(self, symbol, api_key, api_secret, botName):
        twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
        self.redisConn

        def handle_socket_message(price_data):
            print(price_data)
            self.redisConn.set(symbol, pickle.dumps(price_data))

            # Checking Takeprofits triggers

        #twm.start()
        #twm.start_symbol_book_ticker_socket(callback=handle_socket_message, symbol=symbol)

        #twm.join()  # continue checking until all conditions are met execute the order and close the tasks

    def start(self):
        while True:
            price_data = self.redisConn.get(self.symbol)
            price_data = pickle.loads(price_data)
            current_price = float(price_data['b'])

            self.trader(current_price, "Testname")

            print("[X] {0} data:{1}".format(price_data['s'], current_price))

        # place the orders here

        # store the price points to track the  price movement

        # FOLLOWING THE PRICE WHEN THE PRICE REACHES THE ONE ON THE SET grids

        # set the opposite order on the opposite grid

        # Place the first order

        # placd the second order from the sell

    def sellOrderPlacer(self, limitPrice):

        URL_PATH = "http://0.0.0.0:5550/bot/record/orders"
        HEADERS = {
            'Content-Type': 'application/json'
        }

        quantity = self.BinanceOps.round_decimals_down(
            self.params["qtyPerGrid"], self.qtyPrecision)

        sellPrice = self.BinanceOps.round_decimals_down(
            float(limitPrice), int(self.pricePrecision))
        logger.info("point", sellPrice )

        param = {
            'symbol': self.params['symbol'],
            'side': 'SELL',
            'type': 'LIMIT',
            'quantity': quantity,
            'price': sellPrice
        }

        newSellOrder = {}
        if self.operation == "binance":
            param.update({"timeInForce": "GTC"})
            newSellOrder = self.BinanceOps.create_order(**param)
            logger.debug("Sell order response spot", newSellOrder)
        if self.operation == "binance-futures":
            param.update({'timeInForce': 'GTC'})
            newSellOrder = self.BinanceOps.futures_create_order(**param)
            logger.debug("Sell order response futures", newSellOrder)

        if newSellOrder:
            # BuyDeleteOrders.append(buyOrder)
            # self.SellOrders.append(newSellOrder)
            OrderToSave = newSellOrder
            orderID = OrderToSave['orderId']
            del OrderToSave['orderId']
            OrderToSave.update({'binance_order_id': orderID, 'bot_id': int(self.botID), 'user_id': int(
                self.userId), 'created_on': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())})

        #     # TODO Save to the database directly to remove the requests
        #     x = requests.post(URL_PATH, headers=HEADERS,
        #                       data=json.dumps(OrderToSave))

    def buyOrderPlacer(self, limitPrice):
        URL_PATH = "http://0.0.0.0:5550/bot/record/orders"
        HEADERS = {
            'Content-Type': 'application/json'
        }
        quantity = self.BinanceOps.round_decimals_down(
            self.params["qtyPerGrid"], self.qtyPrecision)
        buy_price = self.BinanceOps.round_decimals_down(
            float(limitPrice), int(self.pricePrecision))

        logger.info("point,", buy_price)
        param = {
            "symbol": self.params['symbol'],
            "side": "BUY",
            "quantity": quantity,
            "price": buy_price,
            'timeInForce': "GTC",
            'type': "LIMIT",
        }
        new_buy_order={}

        if self.operation == "binance":
            new_buy_order = self.BinanceOps.create_order(**param)
            logger.debug("Buy order response spot", new_buy_order)
            
        if self.operation == "binance-futures":
            param.update({"timeInForce": "GTC"})
            new_buy_order = self.BinanceOps.futures_create_order(**param)
            logger.debug("Buy order response futures", new_buy_order)
        if new_buy_order:
            self.BuyOrders.append(new_buy_order)
            OrderToSave = new_buy_order
            orderID = OrderToSave['orderId']
            del OrderToSave['orderId']
            OrderToSave.update({'binance_order_id': orderID, 'bot_id': int(self.botID), 'user_id': int(
                self.userId), 'created_on': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())})

        #     x = requests.post(URL_PATH, headers=HEADERS,
        #                       data=json.dumps(OrderToSave))

    def getBidAskPrice(self):
        ticker = {}
        param = {"symbol": self.params['symbol']}
        print(param)
        if self.operation == "binance":
            ticker = self.BinanceOps.get_orderbook_ticker(**param)
        if self.operation == "binance-futures":
            print("futures")
            ticker = self.BinanceOps.futures_orderbook_ticker(**param)

        print(f"ticker: {ticker}")
        bidPrice = 0
        askPrice = 0
        if ticker:
            bidPrice = float(ticker['bidPrice'])
            askPrice = float(ticker['askPrice'])
        logger.info("point")
        return bidPrice, askPrice


def gridbotStreamer(grid_bot_instance):

    twm = ThreadedWebsocketManager(
        api_key=grid_bot_instance.key, api_secret=grid_bot_instance.secret)

    def handle_socket_message(price_data):
        current_price = float(price_data['b'])
        print("[X] {0} data:{1}".format(price_data['s'], current_price))

        # grid_bot_instance.trader(current_price, "Testname")
        # Checking Takeprofits triggers

    #twm.start()
    #twm.start_symbol_book_ticker_socket(callback=handle_socket_message, symbol=grid_bot_instance.symbol)

    #twm.join()  # continue checking until all conditions are met execute the order and close the tasks
