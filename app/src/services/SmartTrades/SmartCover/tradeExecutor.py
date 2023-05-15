from app.src.utils.binance.streams import ThreadedWebsocketManager
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src.services.binanceoperations import BinanceOps
from app.src.utils import logging

from app.src.services.SmartTrades.SmartCover.conditionalMonitors import (
    takeProfitMonitor,
    stopLossMonitor,
    trailingSellMonitor,
    trailingStopLossMonitor,
    trailingTakeProfitMonitor
)

from app.src.services.SmartTrades.dboperations import modifyOrder
from app.src.services.Notifications.Notification import Notification

import threading
import datetime


# Instance to send notification
notifier = Notification()

logger = logging.GetLogger(__name__)

# Event stream settings
event_name = 'smart-cover'
msginfo = 'info'
msgerror = 'error' 

def stopLossTimeoutChecker(twm, timeout, socketName):
    """Handle timeouts"""
    def cancel():
        print("++++++++CANCELED TASK STOPLOSS TIMEOUT REACHED +++++++++")
        twm.stop_socket(socketName)
        twm.stop()       
        return "Done"
        
    print("StopLoss TimeOut Clock has started")
    startTime = threading.Timer(timeout, cancel)
    startTime.start()

def createSmartCoverOrder(user_data, orderDetails):
    """
    Handle sending the orders to binance and returning user responses
    """
    
    key = user_data['api_key']
    secret = user_data['api_secret']
    exchange_type = user_data['exchange_type']

    print("ORDER DETAILfhhdhdhdhdhd ", orderDetails)
    print("dbgbhjbjdsgsd")
    try:
        if exchange_type == "binance":
            BinanceClient = BinanceOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
            newOrder = BinanceClient.create_order(**orderDetails)
        if exchange_type == "binance-futures":
            BinanceClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
            newOrder = BinanceClient.futures_create_order(**orderDetails)

        # newOrder = BinanceClient.sendOrder(orderDetails)

        if newOrder != False:
            resp = {
                "status": "OK",
                "result": newOrder     
            }
            return resp
        else:
            resp = {
                "status": "OK",
                "result": []           
            }
            return resp

    except Exception as e:
        logger.exception("Create Order Exception")
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters"            
        }
        return resp

def initialSell(configs, orderType):
    """Performs the initial Sell of the symbol"""
    initialSellOrderDetails = {
        "side": "SELL",
        "symbol":configs["exchange_data"]["symbol"]
    }
    print(configs["exchange_data"]["entry_sell_price"])
    if configs["order_type"] == "LIMIT":
        initialSellOrderDetails.update({"type": orderType, "quantity":float(configs["exchange_data"]["amount"]), "price":float(configs["exchange_data"]["entry_sell_price"]), "timeInForce": "GTC"})
        # resp = createSmartCoverOrder(configs["user_data"], initialSellOrderDetails)
    if configs["order_type"] == "MARKET":
        initialSellOrderDetails.update({"type": orderType, "quantity":float(configs["exchange_data"]["amount"])})
        # resp = createSmartCoverOrder(configs["user_data"], initialSellOrderDetails)
    if configs["order_type"] == "CONDITIONAL-MARKET":
        initialSellOrderDetails.update({"type": "MARKET", "quantity":float(configs["exchange_data"]["amount"])})
        # resp = createSmartCoverOrder(configs["user_data"], initialSellOrderDetails)
    if configs["order_type"] == "CONDITIONAL-LIMIT":
        initialSellOrderDetails.update({"type": "LIMIT", "quantity":float(configs["exchange_data"]["amount"]), "price":float(configs["exchange_data"]["entry_sell_price"]), "timeInForce": "GTC"})
        # resp = createSmartCoverOrder(configs["user_data"], initialSellOrderDetails)
        
    logger.info("ORDER PARAMAS 0 {}".format(initialSellOrderDetails))
    resp = createSmartCoverOrder(configs["user_data"], initialSellOrderDetails)
    return resp

def orderTemplate(configs, twm, binanceOrderType):
    user_data = configs["user_data"]
    exchange_data = configs["exchange_data"]
    trailing_sell = configs["trailing_sell"]
    take_profit_targets= configs["take_profit_targets"]
    stop_loss_targets= configs["stop_loss_targets"]
    temp_order_id = exchange_data['temp_order_id']
    timeout = int(stop_loss_targets["stop_loss_timeout"])
    orderType = configs["order_type"]
    chatId = configs["telegram_id"]

    notificationMessage = {
        "msg": "Smart Cover",
        "msgType": msginfo,
        "eventName": event_name,
        "channel": user_data['user_id'],
        "chatId": chatId,
        "kwargs": {'extra':'no info'}
    }
    
    initialResp = initialSell(configs, binanceOrderType)
    executedOn = datetime.datetime.utcnow()
    
    if "APIError" not in initialResp["result"]:
        # Send Notification for initial sell order success and tigger buy signal
        notificationMessage.update({"msg":"Smart Cover - Initial Sell Success: {}".format(initialResp)})
        notifier.sendNotification(notificationMessage)
        reason = notificationMessage["msg"]
        modifyOrder(temp_order_id, "open", reason, executedOn, datetime.datetime.utcnow())

        # Binance websocket Callback to handle price checks
        def handleSocketMessages(priceData):
            # print(priceData)

            currentPrice = float(priceData['b'])
            print("CURRENT PRICE", currentPrice)
            if stop_loss_targets["is_set"]:
                if stop_loss_targets["stop_loss_timeout"] != None:
                    stopLossTimeoutChecker(twm, timeout, start_symbol_book_ticker_socket)
                
                # check stopLoss price triggers
                stopLossResp = stopLossMonitor(exchange_data, currentPrice, stop_loss_targets)
                if stopLossResp["on_target"]:
                    # orderParam = {
                    #     "side": "BUY",
                    #     "symbol":configs["exchange_data"]["symbol"],
                    #     "type": "MARKET",
                    #     "quantity":configs["exchange_data"]["amount"]
                    # }
                    resp = createSmartCoverOrder(configs["user_data"], stopLossResp["order_params"])
                    executedOn =  datetime.datetime.utcnow()
                    if resp:
                        notificationMessage.update({"msg":"Smart Cover - StopLoss Triggered: {}".format(resp)})
                        notifier.sendNotification(notificationMessage)
                        reason = notificationMessage["msg"]
                        modifyOrder(temp_order_id, "filled", reason, executedOn, datetime.datetime.utcnow())
                        twm.stop()
                        twm.stop_socket(start_symbol_book_ticker_socket)
                    else:
                        notificationMessage.update({"msgType":msgerror, "msg":"Smart Cover - StopLoss Triggered, Order Error: {}".format(resp)})
                        notifier.sendNotification(notificationMessage)
                        reason = notificationMessage["msg"]
                        modifyOrder(temp_order_id, "cancelled", reason, executedOn, datetime.datetime.utcnow())
                        twm.stop_socket(start_symbol_book_ticker_socket)
                        twm.stop()
                
                if stop_loss_targets["trailing_stop"] != None:
                    trailingStopLossResp = trailingStopLossMonitor(exchange_data, currentPrice, stop_loss_targets)
                    if trailingStopLossResp["on_target"]:
                        # orderParam = {
                        #     "side": "BUY",
                        #     "symbol":configs["exchange_data"]["symbol"],
                        #     "type": "MARKET",
                        #     "quantity":configs["exchange_data"]["amount"]
                        # }
                        print("ORDER PARAMAS 1", trailingStopLossResp)
                        resp = createSmartCoverOrder(configs["user_data"], trailingStopLossResp["order_params"])
                        executedOn = datetime.datetime.utcnow()

                        if resp:
                            notificationMessage.update({"msg":"Smart Cover - Trailling StopLoss Triggered: {}".format(resp)})
                            notifier.sendNotification(notificationMessage)
                            reason = notificationMessage["msg"]
                            modifyOrder(temp_order_id, "filled", reason, executedOn, datetime.datetime.utcnow())
                            twm.stop_socket(start_symbol_book_ticker_socket)
                            twm.stop()

                        else:
                            notificationMessage.update({"msgType":msgerror, "msg":"Smart Cover - Trailling StopLoss Triggered, Order Error: {}".format(resp)})
                            notifier.sendNotification(notificationMessage)
                            reason = notificationMessage["msg"]
                            modifyOrder(temp_order_id, "cancelled", reason, executedOn, datetime.datetime.utcnow())
                            twm.stop_socket(start_symbol_book_ticker_socket)
                            twm.stop()

            if take_profit_targets["is_set"]:
                # check takeProfit price triggers
                takeProfitResp = takeProfitMonitor(exchange_data, currentPrice, take_profit_targets)
                if takeProfitResp["on_target"]:
                    # orderParam = {
                    #     "side": "BUY",
                    #     "symbol":configs["exchange_data"]["symbol"],
                    #     "type": "MARKET",
                    #     "quantity":configs["exchange_data"]["amount"]
                    # }
                    print("ORDER PARAMAS 2", trailingStopLossResp)
                    resp = createSmartCoverOrder(configs["user_data"], takeProfitResp["order_params"])
                    executedOn = datetime.datetime.utcnow()
                    if resp:
                        notificationMessage.update({"msg":"Smart Cover - TakeProfit Triggered: {}".format(resp)})
                        notifier.sendNotification(notificationMessage)
                        # modify order status in database
                        reason = notificationMessage["msg"]
                        modifyOrder(temp_order_id, "filled", reason, executedOn, datetime.datetime.utcnow())
                        twm.stop_socket(start_symbol_book_ticker_socket)
                        twm.stop()
                    else:
                        notificationMessage.update({"msgType":msgerror, "msg":"Smart Cover - TakeProfit Triggered, Order Error: {}".format(resp)})
                        notifier.sendNotification(notificationMessage)
                        # modify order status in database
                        reason = notificationMessage["msg"]
                        modifyOrder(temp_order_id, "cancelled", reason, executedOn, datetime.datetime.utcnow())
                        twm.stop_socket(start_symbol_book_ticker_socket)
                        twm.stop()
                
                if take_profit_targets["trailing_take_profit"] != None:
                    trailingTakeProfitResp = trailingTakeProfitMonitor(exchange_data, currentPrice, take_profit_targets)
                    if trailingTakeProfitResp["on_target"]:
                        # orderParam = {
                        #     "side": "BUY",
                        #     "symbol":configs["exchange_data"]["symbol"],
                        #     "type": "MARKET",
                        #     "quantity":configs["exchange_data"]["amount"]
                        # }
                        print("ORDER PARAMAS 3", trailingStopLossResp)
                        resp = createSmartCoverOrder(configs["user_data"], trailingTakeProfitResp["order_params"])
                        executedOn = datetime.datetime.utcnow()

                        if resp:
                            notificationMessage.update({"msg":"Smart Cover - Trailling TakeProfit Triggered: {}".format(resp)})
                            notifier.sendNotification(notificationMessage)
                            # modify order status in database
                            modifyOrder(temp_order_id, "filled", str(resp), executedOn, datetime.datetime.utcnow())
                            twm.stop_socket(start_symbol_book_ticker_socket)
                            twm.stop()
                        else:
                            notificationMessage.update({"msgType":msgerror, "msg":"Smart Cover - TakeProfit Triggered, Order Error: {}".format(resp)})
                            notifier.sendNotification(notificationMessage)
                            # modify order status in database
                            modifyOrder(temp_order_id, "cancelled", str(resp), executedOn, datetime.datetime.utcnow())
                            twm.stop_socket(start_symbol_book_ticker_socket)
                            twm.stop()

        # twm.start()
        start_symbol_book_ticker_socket = twm.start_symbol_book_ticker_socket(
            callback=handleSocketMessages, symbol=exchange_data["symbol"])
        
        twm.join()  # continue checking until all conditions are met execute the order and close the tasks
    else:
        # Send failed error and stop the task trailing update status in DB for Fail
        # TODO Add code to change status from the DB to FAILED AND GIVE REASON
        notificationMessage.update({"msgType": msgerror, "msg":"Smart Cover - Initial Sell Failed: {}".format(initialResp)})
        notifier.sendNotification(notificationMessage)

        # modify order status in database
        reason = notificationMessage["msg"]
        modifyOrder(temp_order_id, "cancelled", reason, executedOn, datetime.datetime.utcnow())
        twm.stop()
    
def smartCoverExecutor(configs):
    """
    consolidates all the smart cover checker units into one entity and user configurations... creating the Smart sell functionality
    """
    user_data = configs["user_data"]
    exchangeData = configs["exchange_data"]
    triggerPrice = configs["trigger_price"]
    trailingSellTarget = configs["trailing_sell"]
    orderType = configs["order_type"]
    
    # Initialize price websocket
    twm = ThreadedWebsocketManager(api_key=user_data["api_key"], api_secret=user_data["api_secret"])
   

    if orderType == "MARKET":
        # CReate iniatal order and start listmin ORDER TEMPLATE
        twm.start()
        if trailingSellTarget["is_set"]:
            # Open websocket instance and create initial sell
            print("MARKET ORDER WITH TRAILING SET")
            # Binance websocket Callback to handle price checks
            def handleSocketMessages(priceData):
                # print(priceData)
                print("MARKET ORDER WITH TRAILING SET")

                currentPrice = float(priceData['b'])
                print("CURRENT PRICE", currentPrice)
                trailingSellResp = trailingSellMonitor(exchangeData, currentPrice, trailingSellTarget)
                if trailingSellResp["on_target"]:
                    twm.stop()
                    # Check trailing sell and execute inital sell, then stop socket
                    orderTemplate(configs, twm, "MARKET")

            # twm.start()
            twm.start_symbol_book_ticker_socket(
                callback=handleSocketMessages, symbol=exchangeData["symbol"])

            # twm.join()  # continue checking until all conditions are met execute the order and close the tasks
    
        else:
            # USE WHEN TRAILING IS False, Place the initiall sell order immediately on binance
            print("MARKET WITHOUT TRAILING SET")
            orderTemplate(configs, twm, "MARKET")

    if orderType == "LIMIT":
        print("LIMIT ORDER")
        # place initall sell limit order  on Binance with the set limit price
        orderTemplate(configs, twm, "LIMIT")

    if orderType == "CONDITIONAL-MARKET":
        # This bit of code will trigger initial sell order when the price condition is met and when the trailing set 
        # TODO create 2 ifs for when there is trailing and whne the trailing is not set 

        if trailingSellTarget["is_set"]:
            def handleSocketMessages(priceData):
                print("CONDTITONAL MARKET WITH TRAILING SET")

                currentPrice = float(priceData['b'])
                print("CURRENT PRICE {} TRIGGER PRICE: {}".format(currentPrice, triggerPrice))
                if currentPrice >= float(triggerPrice):
                    trailingSellResp = trailingSellMonitor(exchangeData, currentPrice, trailingSellTarget)
                    if trailingSellResp["on_target"]:
                        twm.stop()
                        # Check trailing sell and execute inital sell, then stop socket
                        orderTemplate(configs, twm, "MARKET")

            twm.start()
            twm.start_symbol_book_ticker_socket(
                callback=handleSocketMessages, symbol=exchangeData["symbol"])

            twm.join()  # continue checking until all conditions are met execute the order and close the tasks
                        
        else:
            # Binance websocket Callback to handle price checks
            def handleSocketMessages(priceData):
                print("CONDTITONAL MARKET WITH NO TRAILING SET")

                currentPrice = float(priceData['b'])
                print("CURRENT PRICE", currentPrice)
                if float(triggerPrice) <= float(currentPrice):
                    print("conditinal trigger has been fired, now performimg initial sell")
                    twm.stop()
                    # Check trailing sell and execute inital sell, then stop socket
                    orderTemplate(configs, twm, "MARKET")

            twm.start()
            twm.start_symbol_book_ticker_socket(
                callback=handleSocketMessages, symbol=exchangeData["symbol"])

            twm.join()  # continue checking until all conditions are met execute the order and close the tasks

    if orderType == "CONDITIONAL-LIMIT":
        # This section will check the limit  price condition, if the condition is  triggered then the limit order will
        # be placed on binance directly with the predefined trigger price
        # TODO create a mechanism to check the price condition if they trigger

        def handleSocketMessages(priceData):
            # print(priceData)
            print("Conditional-Limit Order")
            currentPrice = float(priceData['b'])
            print("CURRENT PRICE", currentPrice)
            if float(triggerPrice) <= float(currentPrice):
                print("conditinal trigger has been fired, now performimg initial sell limit order")
                twm.stop()
                # Check trailing sell and execute inital sell, then stop socket
                orderTemplate(configs, twm, "LIMIT")

        twm.start()
        twm.start_symbol_book_ticker_socket(callback=handleSocketMessages, symbol=exchangeData["symbol"])

        twm.join()  # continue checking until all conditions are met execute the order and close the tasks
    
    # # twm.stop()
    # twm.join()