"""
Handle the actual execution
    - smart sell entity merge
    - future order creator
    -#TODO db operations
"""

from app.src.services.SmartTrades.SmartSell.conditionalMonitors import take_profit_monitor
from app.src.utils.binance.streams import ThreadedWebsocketManager
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src.utils import logging

from app.src.services.SmartTrades.SmartSell.conditionalMonitors import (
    take_profit_monitor,
    stop_loss_monitor, 
    trailing_stop_monitor,
    trailing_take_profit_monitor,
)

from app.src.services.SmartTrades.dboperations import modifyOrder
from app.src.services.Notifications.Notification import Notification

import threading
import datetime

notifier = Notification()

logger = logging.GetLogger(__name__)

# Event stream settings
event_name = 'smart-sell'
msginfo = 'info'
msgerror = 'error'


def createFuturesSmartSell(user_data, orderDetails):
    print("-----order details----",orderDetails)

    """
    Handle sending the orders to binance and returning user responses
    """
    
    key = user_data['api_key']
    secret = user_data['api_secret']

    try:
        BinanceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
        newOrder = BinanceFuturesClient.sendOrder(orderDetails)

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

def stop_loss_timeout_checker(twm, timeout):
    """Handle timeouts"""
    def cancel():
        print("++++++++CANCELED TASK+++++++++")
        twm.stop()        
        return "Done"
    
    print("TimeOut Clock has started")
    startTime = threading.Timer(timeout, cancel)
    startTime.start()

def smartSellExecutor(configs):
    """
    consolidates all the smart sell checker units into one entity and user configurations... creating the Smart sell functionality
    """
    user_data = configs["user_data"]
    exchange_data = configs["exchange_data"]
    # update here
    print("-----------", configs["exchange_data"])

    take_profit_targets= configs["take_profit_targets"]
    stop_loss_targets= configs["stop_loss_targets"]
    temp_order_id = exchange_data['temp_order_id']

    chatId = configs["telegram_id"]

    notificationMessage = {
        "msg": "Smart Sell",
        "msgType": msginfo,
        "eventName": event_name,
        "channel": user_data['user_id'],
        "chatId": chatId,
        "kwargs": {'extra':'no info'}
    }
    
    twm = ThreadedWebsocketManager(api_key=user_data["api_key"], api_secret=user_data["api_secret"])

    if stop_loss_targets['stop_loss_timeout']==0 or stop_loss_targets['stop_loss_timeout']=='':
        pass
    else:
        stop_loss_timeout_checker(twm, stop_loss_targets['stop_loss_timeout'])

    def handle_socket_message(price_data):
        print(price_data)
    
        current_price = float(price_data['b'])

        print("[X] {0} data:{1}".format(price_data['s'],current_price ))
        print("[X] Started to check Smart sell triggers")
        
        # Checking Takeprofits triggers
        resp = take_profit_monitor(exchange_data, current_price, take_profit_targets)
       

        if resp["on_target"]==True:
            
            msg ='[X] Order has reached the set take profit place now'
            print(msg)

            notificationMessage.update({"msg":msg})
            notifier.sendNotification(notificationMessage)

            print("[X] Order params {0}".format(resp))


            if resp["terminate_tp_checks"]==True:
                orderDetails = resp['order_params']
                twm.stop()
                # placing order on binance futures
                print("------order details----before create", orderDetails)
                response = createFuturesSmartSell(user_data, orderDetails)
                executed_on = datetime.datetime.utcnow()
            
                if response['status'] =='OK':
                    modify_order = modifyOrder(temp_order_id, "open",'OK', executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
                   
                else:
                    modify_order = modifyOrder(temp_order_id,"closed", response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                    msg="db modification status",str(modify_order)

                    print(msg)
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
                

            if resp["terminate_tp_checks"]==False:
                orderDetails = resp['order_params']
                # placing a market order on binance with the takeProfit as the key trigger
                response = createFuturesSmartSell(user_data,orderDetails)
                print(response)
                executed_on = datetime.datetime.utcnow()
            
                if response['status'] =='OK':
                    modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
                    
                else:
                    modify_order = modifyOrder(temp_order_id,'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
        
        else:
            print("[X] No TakeProfit target reached yet. Still checking ...")

        # Checking stop loss triggers
        resp = stop_loss_monitor(exchange_data, current_price, stop_loss_targets)
        if resp["on_target"] == True:
            msg="[x] Price has reached the stop Loss target sending a smart sell"
            
            print(msg)
            notificationMessage.update({"msg":msg})
            notifier.sendNotification(notificationMessage)

            orderDetails = resp['order_params']
            twm.stop()
            # Placing a Market order using the stop loss 
            response = createFuturesSmartSell(user_data,orderDetails)
            print(response)
            executed_on = datetime.datetime.utcnow()
            print(response)
            if response['status'] =='OK':
                modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                msg = "db modification status",str(modify_order)

                print(msg)
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)
            
            else:
                modify_order = modifyOrder(temp_order_id, 'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                msg = "db modification status",str(modify_order)

                print(msg)
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)
        else:
            print("[X] Still checking the stop loss triggers ---")

        
        # checking trailings stops

        resp = trailing_stop_monitor(exchange_data, current_price, stop_loss_targets)
        if resp["on_target"] == True:
            msg="[x] Price has reached the stop Loss target sending a smart sell"


            print(msg)
            # Send Notifications
            notificationMessage.update({"msg":msg})
            notifier.sendNotification(notificationMessage)

            orderDetails = resp['order_params']
            twm.stop()
            # Placing a Market order using the stop loss 
            response = createFuturesSmartSell(user_data,orderDetails)
            print(response)
            executed_on = datetime.datetime.utcnow()
            print(response)
            if response['status'] =='OK':
                modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                msg = "db modification status",str(modify_order)

                print(msg)
                # Send Notifications
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)
                
            else:
                modify_order = modifyOrder(temp_order_id,'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                msg = "db modification status",str(modify_order)

                print(msg)
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)
        else:
            print("[X] Still checking the trailing stop loss triggers ---")
        
        # trailing takeprofit
        resp = trailing_take_profit_monitor(exchange_data, current_price, take_profit_targets)
        if resp["on_target"] == True:
            msg ="[x] Price has reached the take profit target sending a smart sell"
            
            print(msg)
        
            # Send Notifications
            notificationMessage.update({"msg":msg})
            notifier.sendNotification(notificationMessage)

            orderDetails = resp['order_params']
            twm.stop()
            # Placing a Market order using the stop loss 
            response = createFuturesSmartSell(user_data,orderDetails)
            executed_on = datetime.datetime.utcnow()
            print(response)
            if response['status'] =='OK':
                modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                msg = "db modification status",str(modify_order)

                print(msg)
                # Send Notifications
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)
                
            else:
                modify_order = modifyOrder(temp_order_id,'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                msg = "db modification status",str(modify_order)

                print(msg)

                # Send Notifications
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)

            
        else:
            print("[X] Still checking the Trailing take profit triggers ---")



    twm.start()
    twm.start_symbol_book_ticker_socket(
        callback=handle_socket_message, symbol=exchange_data["symbol"])

    twm.join()  # continue checking until all conditions are met execute the order and close the tasks