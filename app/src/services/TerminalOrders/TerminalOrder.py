from enum import Enum
import arrow
import datetime
import threading
import pickle
import redis

from app.src.services.TerminalOrders.terminalorderservices import ExchangeResolver, OrderOps
from app.src.utils.binance.streams import ThreadedWebsocketManager

conn = redis.StrictRedis('localhost')
class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class Status(Enum):
    OPEN = "open"
    CLOSE = "closed"
    FILLED = "filled"
class StatusReasons(Enum):
    TIMEOUT = "Timeout expired, order cancelled"
    BALANCE = "Insufficient Balance"
    FILLED = "Successfully Executed, target price reached"
    CANCELED = "Cancelled Order"
    FILLED_TRAILING = "Successfully Executed, Trailing price reached"

class TerminalOrderer:
    def __init__(self, config: dict()):
        """This config contains all the params required to open an order"""
        self.order = config
        order_type = self.order['type'].upper()
        self.order.update({"type": order_type})
        self.exchange = ExchangeResolver.loadExchange(config)
        self.status = Status.OPEN.value
    
    def startUp(self):
        def cancel():
            self.handleTimedOut()
            print("++++++++CANCELED TASK+++++++++")
            twc.stop()

        # Check if timeout has a value and start the time. Will start a counter thread when timeout is reached will  exceute cancel() callback and cancel order.
        if self.order['timeout'] != None or self.order["timeout"] != 0:
            timeInSeconds = int(self.order["timeout"])
            print("TimeOut Clock has started, execute in:-- {} seconds".format(timeInSeconds))
            startTime = threading.Timer(timeInSeconds, cancel)
            startTime.start()
        
        twc = ThreadedWebsocketManager(api_key=self.order["exchangeInfo"]["key"], api_secret=self.order["exchangeInfo"]["secret"])
        twc.start()
      
        def priceChecker(latestPrice): 
            currentPrice = float(latestPrice["b"])
            print(currentPrice)

            if self.status == "open":
                if self.order["targetprice"] != 0:
                    if self.checkTriggerPrice(currentPrice):
                        try:
                            createdOrder =  self.executeOrder()
                            print(createdOrder)
                            twc.stop()
                        except Exception as e:
                            self.cancelOrder(str(e))
                            twc.stop()
                if self.order["trailing"] != 0:
                    tempMarketPrice = float(currentPrice)
                    trailingPrice = float(self.order["trailing"])
                    storeKeyID = self.order["orderid"]
                    print(f"{storeKeyID}: {self.order['orderid']}")
                    priceComparisonList = conn.get(storeKeyID)
                
                    if priceComparisonList == None:
                        # store the temp_market price in a redis store
                        stop_loss_limit =((100 + trailingPrice)/100) * tempMarketPrice

                        priceComparisonList=[float(stop_loss_limit),float(tempMarketPrice)]
                    
                        conn.set(storeKeyID, pickle.dumps(priceComparisonList))
                    else:
                        priceComparisonList = pickle.loads(priceComparisonList)
                    
                    tempMarketPrice = priceComparisonList[1]

                    if currentPrice < tempMarketPrice:

                        percentMarketChange =(float((tempMarketPrice - currentPrice))/tempMarketPrice) * 100
                        # now move the stop_loss_limit by the same percentage change
                        stop_loss_limit =((100 - percentMarketChange)/100) * priceComparisonList[0]

                        priceComparisonList[0] = float(stop_loss_limit)
                        priceComparisonList[1] = float(currentPrice)

                        conn.set(storeKeyID, pickle.dumps(priceComparisonList))

                    elif (currentPrice - priceComparisonList[0]) >= 0:
                        print("[X] Trailing stop loss limit reached. Sending order to binance ata [{0}].".format([priceComparisonList[0],currentPrice]))
                        try:
                            createdOrder = self.executeOrder()
                            print(createdOrder)
                            twc.stop()
                            # lets delete the keyf from our redis database
                            conn.delete(storeKeyID)
                        except Exception as e:
                            self.cancelOrder(str(e))
                    else:
                        # Just update the current price
                        priceComparisonList[1] = float(currentPrice)
                        conn.set(storeKeyID, pickle.dumps(priceComparisonList))
                        print("[X] Trailig stop comparison list at [{0}].Still checking ...".format(priceComparisonList))
            else:
                twc.stop()

        # Start the binance socket Listener
        twc.start_symbol_book_ticker_socket(callback=priceChecker, symbol=self.order["symbol"])
        twc.join()

    def createSpot(self):
        """Create a conditional Buy Market or Limit Order - Spot Trading"""
        quantity = self.exchange.round_decimals_down(self.order["amt"], self.exchange.qtyPrecision)
        if self.order['type'] == "MARKET":
            orderParams = {
                "side": self.order["side"],
                "symbol": self.order["symbol"],
                "type": OrderType.MARKET.value,
                "quantity": quantity
            }
            return orderParams

        if self.order['type'] == "LIMIT":
            orderParams = {
                "side": self.order["side"],
                "symbol": self.order["symbol"],
                "type": OrderType.LIMIT.value,
                "quantity": quantity,
                "price": self.order["targetprice"],
                "timeInForce": self.order["timeinforce"]
            }
            return orderParams
        return None

    def createFutures(self):
        """Create a conditional Buy Market or Limit Order - Spot Trading"""
        quantity = self.exchange.round_decimals_down(float(self.order["amt"]), self.exchange.qtyPrecision)
        price = self.exchange.round_decimals_down(float(self.order["targetprice"]), self.exchange.pricePrecision)

        # Set the leverge in BinanceFuturesOps
        self.setLeverage()

        if self.order['type'] == "MARKET":
            orderParams = {
                "side": self.order["side"],
                "symbol": self.order["symbol"],
                "type": OrderType.MARKET.value,
                "quantity": quantity,
                "timeInForce": self.order["timeinforce"]
            }
            return orderParams

        if self.order['type'] == "LIMIT":
            orderParams = {
                "side": self.order["side"],
                "symbol": self.order["symbol"],
                "type": OrderType.LIMIT.value,
                "quantity": quantity,
                "price": price,
                "timeInForce": self.order["timeinforce"]
            }
            return orderParams
        return None
    
    def checkTrailingPrice(self, currentPrice: float) -> bool:
        """Check if trailing price is reached. Returns True if reached """
        trailingprice = self.exchange.round_decimals_down(float(self.order['trailingprice']), self.exchange.pricePrecision)
        if currentPrice == trailingprice:
            return True
        return False

    def checkTriggerPrice(self, currentPrice: float) -> bool:
        """Check if trigger price is reached. Returns True if reached """
        triggerprice = self.exchange.round_decimals_down(float(self.order['triggerprice']), self.exchange.pricePrecision)
        if currentPrice >= triggerprice:
            return True
        return False

    def setLeverage(self) -> None:
        """Set Leverage for Futures Order"""
        params = {
            "symbol": self.order["symbol"],
            "leverage":self.order["leverage"]
        }
        self.exchange.futures_change_leverage(**params)
    
    def cancelOrder(self, reason) -> None:
        """Cancels an order,changes the order status to false"""

        orderDetails = {
            "status": Status.CLOSE.value,
            "modified_on": datetime.datetime.utcnow(),
            "change_reason": reason 
        }
        
        self.notifyUser(orderDetails)
        OrderOps.updateOrderDetails(self.order["orderid"], orderDetails)

        self.status = Status.CLOSE.value
        self.notifyUser(orderDetails)
            
    def handleTrailingPrice(self) -> None:
        """
        Check to see if trailing  for market is active
        :param order: Current order
        :return: None
        """

    def notifyUser(self, msg) -> None:
        """Send update status to Notification Module"""
        # TODO Implement notification mechanism to both telegram and webUI
        print("Trade Message, {}".format(msg))

    def executeOrder(self):
        """Execute Order to Binance API"""
        if self.order["exchangeInfo"]["exchangeType"] == "binance":
            params = self.createSpot()
            print(params)
            try:
                result = self.exchange.create_order(**params)
                self.status = Status.FILLED.value
                self.notifyUser("order Filled")
                # TODO Send message notification for success
               
            except Exception as e:
                print("Exception: -------", str(e))
                self.cancelOrder(str(e))
                # TODO Send message notification for fail

        if self.order["exchangeInfo"]["exchangeType"] == "binance-futures":
            params = self.createFutures()
            new_params = params.copy()
            new_params.pop("timeInForce")
            print(f"-------------new params---- {new_params}")

            try:
                result = self.exchange.futures_create_order(**new_params)
                self.status = Status.FILLED.value
                self.notifyUser("order Filled")
                # TODO Send message notification for success
            except Exception as e:
                self.cancelOrder(str(e))
                # TODO Send message notification for fail
            
    def getTimeOutExpiry(self) -> bool:
        """
        Calculate the expiry date time in utcno() based on given timeout
        """
        timeout = int(self.order.get('timeout'))
        utcnow = arrow.utcnow()
        timeOutExpiry = utcnow.shift(seconds=+timeout).date()
        return timeOutExpiry
    
    def handleTimedOut(self) -> None:
        """
        Cancell an order when timeout timeframe is achieved
        """
        self.cancelOrder(StatusReasons.TIMEOUT.value)