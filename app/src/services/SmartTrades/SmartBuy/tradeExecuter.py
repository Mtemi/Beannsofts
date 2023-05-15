"""
Handle the actual execution
    - smart buy entity merge
    - future order creator
    -#TODO db operations
"""

from app.src.services.SmartTrades.SmartBuy.conditionalMonitors import take_profit_monitor
from app.src.utils.binance.streams import ThreadedWebsocketManager
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src.utils import logging

from app.src.services import OrderOperations
from app.src.models import SmartOrdersModel, UserModel, ExchangeModel
from app.src import db
from app.src.services.SmartTrades.SmartBuy.conditionalMonitors import (
    take_profit_monitor,
    stop_loss_monitor, 
    trailing_stop_monitor,
    trailing_take_profit_monitor,
)
from app.src.services.SmartTrades.dboperations import modifyOrder
from app.src.services.Notifications.Notification import Notification

import threading
import datetime

# Notification class instance
notifier = Notification()

logger = logging.GetLogger(__name__)

# Event stream settings
event_name = 'smart-buy'
msginfo = 'info'
msgerror = 'error'


def createFuturesSmartBuy(user_data, orderDetails):
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
    startTime = threading.Timer(timeout, cancel())
    startTime.start()
    
def smartBuyExecutor(configs):

    """
    consolidates all the smart buy checker units into one entity and user configurations... creating the Smart buy functionality
    """
    print("CONFIGS TO USE ON SMART TRADE")
    print(configs)
    print("CONFIGS TO USE ON SMART TRADE")
    user_data = configs["user_data"]
    exchange_data = configs["exchange_data"]
    take_profit_targets= configs["order_details_json"]["take_profit_targets"]
    stop_loss_targets= configs["order_details_json"]["stop_loss_targets"]
    temp_order_id = exchange_data["exchange_data"]["temp_order_id"]

    chatId = configs["telegram_id"]
    
    notificationMessage = {
        "msg": "Smart Trade",
        "msgType": msginfo,
        "eventName": event_name,
        "channel": user_data['user_id'],
        "chatId": chatId,
        "kwargs": {'extra':'no info'}
    }
    price1 = 0.0


    exchangeName = configs['exchange_name']
    print("exchangeName", exchangeName)
    try:
        twm = ThreadedWebsocketManager(api_key=user_data["api_key"], api_secret=user_data["api_secret"])
        # I only need the price at this level 
        # since this is a bot, smart bot, active orders reside on the bot itself .
        # this is to allow changes to the smart orders as well as manage computations
        # 
        # then I will crate a linked list , within this loop that's appended with any new take profits
        # or 
        #if stop_loss_targets['Stop_loss_timeout']==0 or stop_loss_targets['Stop_loss_timeout']=='':
            #print("stop_loss_targets['stop_loss_timeout'] is Not set, so we pass")
            #pass
        #else:
            #stop_loss_timeout_checker(twm, stop_loss_targets['Stop_loss_timeout'])
            #print("stop_loss_targets['stop_loss_timeout'] IS SET, so we DONT PASS")
        twm.start()
        print("web socket has been started and is open")

        # open_smart_orders = db.session.query(SmartOrdersModel).filter_by(id=user_data['user_id'], status="open").all()
        
        print("CONFIG DATA T WORK WITH FOR THE SMART TRADES", configs)
        # for open_smart_order in open_smart_orders:
        # exchange_order_id
        resp = {
            "orderid": configs["exchange_order_id"],
            "userid": configs["userid"],
            "amount": configs["amt"],
            "price": configs["price"],
            "exchange_order_id": configs["exchange_order_id"],
            "symbol": exchange_data['symbol'],
            "order_details_json": configs["order_details_json"],
            } 

        order_entry_price = resp["price"]
        result1 = resp["order_details_json"]
        print(" TP AND SL order_details_json ", result1)
        take_profit_targets1 = result1["take_profit_targets"]
        stop_loss_targets1 = result1["stop_loss_targets"]
        #result1["take_profit_targets"]["take_profits"]["steps"][0] 
        print("take_profit_targets", take_profit_targets1)
        print("stop_loss_targets", stop_loss_targets1)
        steps1 = take_profit_targets1["take_profits"]["steps"]
        print("the various take profits / the steps", steps1) 
        # result["stop_loss_targets"]["stop_loss_price"]
        # {'take_profit_price': 0, 't
        # ake_profit_order_type': 'market', 'trailing_take_profit': '10', 'take_profits': {'steps': [{'price
        # ': '10', 'quantity': '40'}, {'price': '15', 'quantity': '40'}]}}

        # {'stop_loss_type': 'market'
        # , 'stop_loss_percentage': '1', 'stop_steps': '3', 'stop_loss_timeout': 0, 'trailing_stop': 0}

        stop_loss_price = order_entry_price-(order_entry_price*float(stop_loss_targets1["stop_loss_percentage"])/100)
        stop_loss_11 = stop_loss_targets1["stop_loss_percentage"]
        sl_steps = stop_loss_targets1["stop_steps"]
        print("stop_loss_price", stop_loss_price)
        symbol=resp["symbol"].replace("/", "")
        print("symbol to querry price data", symbol) 
        # I can create code for stop loss here before we embark on take profits
        # when first tp is hit, sl is adjusted to the first order entry
        # question is ? how do we determine the entry price of the first order  ?
        # we can use the % value of this sl, to calculate our initial entry price
        def handle_socket_message1(price_data):
            print("STREAMED PRICE DATA", price_data)
            return price_data["b"]
        
        stop_loss_price_target = twm.start_symbol_book_ticker_socket(callback=handle_socket_message1, symbol=symbol)
        
        # stop_loss_price_target= twm.symbol_ticker_socket(symbol=resp["symbol"].replace("/", ""))
        # stop_loss_price_target= twm.start_symbol_mark_price_socket(symbol=resp["symbol"].replace("/", ""))
        print(")(((((((((((((((((((((((((((((((((((((())))))))))))))))))))))))))))))))))))))")
        print("stop_loss_price_target", stop_loss_price_target)
        print("the stop_loss_price_target price above will be used to compare with the set tp price")
        floated_stop_loss_price_target = float(stop_loss_price_target)
        print("floated_stop_loss_price_target" , floated_stop_loss_price_target)
        if stop_loss_price == floated_stop_loss_price_target or stop_loss_price > floated_stop_loss_price_target:
            orderDetailsa = {
                    "symbol": exchange_data['symbol'].replace("/", ""),
                    # "side": "Buy",
                    "type": 'STOP',
                    "quantity": float(resp['amount']), #this is a stop order and so all total amount need be closed 
                    "price": float(stop_loss_price),
                    "stopPrice": float(stop_loss_price)
                    }
            for i in int(sl_steps):
                if i>0: # Here we will have to update sl configs with a value of sl_steps-1
                    resp123l = OrderOperations.CreateBinanceFuturesOrder(resp['userid'], exchangeName, orderDetailsa)
                    print("repsonse after creating the initial stop loss",resp123l)
                    print(resp123l)
                    exchange_order_id = resp123l['orderId'] #this is a new orderId.
                    new_order_price = float(stop_loss_price)-0.002*float(stop_loss_price) # this new order price is good
                    new_stop_loss_price = new_order_price-stop_loss_price*new_order_price # stop_loss_price is % of sl below entry
                    result1["stop_loss_targets"]["stop_loss_price"] = new_stop_loss_price
                    # resp["order_details_json"] = result1
                    # below is a new Binance Futures Order with the new entry price as calculated above
                    if take_profit_targets1['take_profit_order_type'] == 'market':  
                        orderDetails222 = {
                            "symbol": exchange_data['symbol'].replace("/", ""),
                            "side": "Buy",
                            "type": 'MARKET',
                            "quantity": float(resp['amount'])
                        }
                        resp12 = OrderOperations.CreateBinanceFuturesOrder(resp['userid'], exchangeName, orderDetails222)
                        print(resp12)
                        exchange_order_id = resp12["orderId"]
                    if take_profit_targets1['take_profit_order_type'] == 'limit':
                        orderDetails223 = {
                            "symbol": exchange_data['symbol'].replace("/", ""),
                            "side": "Buy",
                            "type": 'LIMIT',
                            "quantity": float(resp['amount'])
                        }
                        resp12 = OrderOperations.CreateBinanceFuturesOrder(resp['userid'], exchangeName, orderDetails223)
                        print("repsonse after creating the initial stop loss",resp12)
                        exchange_order_id = resp12["orderId"]
                        print(resp12)

                    if resp12: 
                        #the order is still open as a smart order, so we are yet to update it as filled
                        print("the order is still open as a smart order, so we are yet to update it as filled")
                        db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == open_smart_order.exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.sl_steps == int(sl_steps)-1, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.order_details_json == result1)
                        db.session.commit() 
                        #the new_order_price is the order price.  That will be used to place new orders
                        # update the order as filled so that it's not querried for filling
                        # print("update the order as filled so that it's not querried for filling")
                        # db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid']).update(SmartOrdersModel.status == 'filled')
                        # db.session.commit() 
                if i ==0: # since here we have no more steps, we can mark the smart order as filled and will be eliminated from the loop
                    resp123l = OrderOperations.CreateBinanceFuturesOrder(resp['userid'], exchangeName, orderDetailsa)
                    print("repsonse after creating the initial stop loss",resp123l)
                    print(resp123l)
                    exchange_order_id = resp123l['orderId'] #this is a new orderId.
                    if resp123l: 
                        #the order is still open as a smart order, so we are yet to update it as filled
                        print("the order is still open as a smart order, so we are yet to update it as filled")
                        db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == open_smart_order.exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.sl_steps == int(sl_steps)-1, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.status == "filled")
                        db.session.commit()
                    #     #update the order as filled so that it's not querried for filling
                    #     print("update the order as filled so that it's not querried for filling")
                    #     db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid']).update(SmartOrdersModel.status == 'filled')
                    #     db.session.commit() 

        #end of checking stop loss conditions
        # tp computations start here
        print("tp steps1", steps1)
        steps2 = steps1[0]
        for i in len(steps2):
            if i > 0:
                price11 = float(steps2[i]["price"])
                quantity11 = float(steps2[i]["quantity"])
                print("price of the takeProfits", price1)
                price221= twm.start_symbol_mark_price_socket(symbol=resp["symbol"].replace("/", ""))
                print("data streamed from binance streams where we want to get the price", price221)
                print("the price above will be used to compare with the set tp price")
                floated_price = float(price221['p'])
                print("price fetched from the Binance futures websocket streams" , floated_price)
                if price11 == floated_price or floated_price > price11 : # it means here that the target has been hit
                    steps2.remove(i) #after removing a step from the TPs available, I will add the step2 param to 
                    # the res as a new config then I will update this new TP steps to the   smart order
                    result1["take_profit_targets"]["take_profits"]["steps"][0] == steps2
                    orderDetailsata = {
                            "symbol": exchange_data['symbol'].replace("/", ""),
                            # "side": "Buy",
                            "type": 'TAKE_PROFIT',
                            "quantity": float(resp['amount']), #this is a stop order and so all total amount need be closed 
                            "price": float(price11),
                            "stopPrice": float(price11)
                            }
            
                    resp123l = OrderOperations.CreateBinanceFuturesOrder(resp['userid'], exchangeName, orderDetailsata)
                    print("repsonse after creating the initial stop loss",resp123l)
                    print(resp123l)
                    exchange_order_id = resp123l['orderId'] #this is a new orderId.
                    new_order_price = float(steps2[i]["price"]) # this new order price is good and thus cannot be a limit order
                    # but will be updated on the smartOrder price.  This is very necessary incase price starts going down and needs
                    # to follow the rules of the SL
                    # it automatically becomes a market order
                    #if a step is hit, I should remove it from steps and update SmartOrdersModel
                    new_stop_loss_price = float(resp['price']) # for tp, entry price becomes sl 
                    result1["stop_loss_targets"]["stop_loss_price"] = new_stop_loss_price
                    # resp["order_details_json"] = result1
                    # below is a new Binance Futures Order with the new entry price as calculated above

                    new_order_quantity = float(resp['amount'])-float(quantity11)/100*float(resp['amount'])

                    orderDetails222 = {
                        "symbol": exchange_data['symbol'].replace("/", ""),
                        "side": "Buy",
                        "type": 'MARKET',
                        "quantity": new_order_quantity
                    }
                        
                    resp12 = OrderOperations.CreateBinanceFuturesOrder(resp['userid'], exchangeName, orderDetails222)
                    print(resp12)
                    exchange_order_id = resp12["orderId"]
                    result1["stop_loss_targets"]["stop_loss_price"] = new_stop_loss_price
                    #we now have to update sl details. 
                    if resp12: 
                        #the order is still open as a smart order, so we are yet to update it as filled
                        print("the order is still open as a smart order, so we are yet to update it as filled")
                        db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == open_smart_order.exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.amt == new_order_quantity, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.order_details_json == result1)
                        db.session.commit() 
            if i ==0:
                #Here we need to fill place a tp order of the same amount as in the quantity
                # so here below we need to pull the size from our order
                new_order_quantity = float(resp['amount'])
                    
                orderDetails222 = {
                    "symbol": exchange_data['symbol'].replace("/", ""),
                    "side": "Buy",
                    "type": 'MARKET',
                    "quantity": new_order_quantity
                }
                    
                resp12 = OrderOperations.CreateBinanceFuturesOrder(resp['userid'], exchangeName, orderDetails222)
                print(resp12)
                exchange_order_id = resp12["orderId"]
                result1["stop_loss_targets"]["stop_loss_price"] = new_stop_loss_price
                #we now have to update sl details. 
                if resp12: 
                    print("the tp is only one and we need to pass an ampout equal to the balance, so it gets filled")
                    db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == open_smart_order.exchange_order_id).update(SmartOrdersModel.status == "filled")
                    db.session.commit() 
                    

        result = resp
        print("result for all open_smart_orders ")
        print(result)

        if len(result) == 0:
            print("user has no open take profit orders")
        else: 
            print("User has open orders and once price is equal , they will be closed and translate to open positions")
            


        # twm.start_symbol_book_ticker_socket(
        #     callback=handle_socket_message, symbol=exchange_data["symbol"])

        twm.join()  
        # continue checking until all conditions are met execute the order and close the tasks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
        
    except Exception as e:
        logger.error(f"exception hit after filtering terminal orders from db exception {str(e)}")
        return {"message":"Fail", "result": str(e)}, 500
            

    def handle_socket_message(price_data):
            print(price_data)
        
            current_price = float(price_data['b'])

            print("[X] {0} data:{1}".format(price_data['s'],current_price ))
            print("[X] Started to check Smart buy triggers")
            
            # Checking Takeprofits triggers
            resp = take_profit_monitor(exchange_data, current_price, take_profit_targets)
            if resp["on_target"]==True:
                
                msg ='[X] Order has reached the set take profit place now'
                print(msg)
                # Send notification to user
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)

                print("[X] Order params {0}".format(resp))

                if resp["terminate_tp_checks"]==True:
                    orderDetails = resp['order_params']
                    twm.stop()
                    # placing order on binance futures
                    response = createFuturesSmartBuy(user_data,orderDetails)
                    executed_on = datetime.datetime.utcnow()
               
                    if response['status'] =='OK':
                        modify_order = modifyOrder(temp_order_id, "open",'OK', executed_on, modified_on=datetime.datetime.utcnow())
                        msg = "db modification status",str(modify_order)

                        print(msg)
                        # Send notification to user
                        notificationMessage.update({"msg":msg})
                        notifier.sendNotification(notificationMessage)
                        
                    else:
                        modify_order = modifyOrder(temp_order_id,"closed", response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                        msg="db modification status",str(modify_order)

                        print(msg)

                        # Send notification to user
                        notificationMessage.update({"msg":msg})
                        notifier.sendNotification(notificationMessage)
                    

                if resp["terminate_tp_checks"]==False:
                    orderDetails = resp['order_params']
                    # placing a market order on binance with the takeProfit as the key trigger
                    response = createFuturesSmartBuy(user_data,orderDetails)
                    print(response)
                    executed_on = datetime.datetime.utcnow()
                
                    if response['status'] =='OK':
                        modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                        msg = "db modification status",str(modify_order)

                        print(msg)
                        # Send notification to user
                        notificationMessage.update({"msg":msg})
                        notifier.sendNotification(notificationMessage)
                        
                    else:
                        modify_order = modifyOrder(temp_order_id,'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                        msg = "db modification status",str(modify_order)

                        print(msg)
                        # Send notification to user
                        notificationMessage.update({"msg":msg})
                        notifier.sendNotification(notificationMessage)
            
            else:
                print("[X] No TakeProfit target reached yet. Still checking ...")

            # Checking stop loss triggers
            resp = stop_loss_monitor(exchange_data, current_price, stop_loss_targets)
            if resp["on_target"] == True:
                msg="[x] Price has reached the stop Loss target sending a smart buy"
                
                print(msg)
                # Send notification to user
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)

                orderDetails = resp['order_params']
                twm.stop()
                # Placing a Market order using the stop loss 
                response = createFuturesSmartBuy(user_data,orderDetails)
                print(response)
                executed_on = datetime.datetime.utcnow()
                print(response)
                if response['status'] =='OK':
                    modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    # Send notification to user
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
                
                else:
                    modify_order = modifyOrder(temp_order_id, 'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    # Send notification to user
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
            else:
                print("[X] Still checking the stop loss triggers ---")

            
            # checking trailings stops

            resp = trailing_stop_monitor(exchange_data, current_price, stop_loss_targets)
            if resp["on_target"] == True:
                msg="[x] Price has reached the stop Loss target sending a smart buy"


                print(msg)
                # Send notification to user
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)

                orderDetails = resp['order_params']
                twm.stop()
                # Placing a Market order using the stop loss 
                response = createFuturesSmartBuy(user_data,orderDetails)
                print(response)
                executed_on = datetime.datetime.utcnow()
                print(response)
                if response['status'] =='OK':
                    modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    # Send notification to user
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
                    
                else:
                    modify_order = modifyOrder(temp_order_id,'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    # Send notification to user
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
            else:
                print("[X] Still checking the trailing stop loss triggers ---")
            
            # trailing takeprofit
            resp = trailing_take_profit_monitor(exchange_data, current_price, take_profit_targets)
            if resp["on_target"] == True:
                msg ="[x] Price has reached the take profit target sending a smart buy"
                
                print(msg)
                # Send notification to user
                notificationMessage.update({"msg":msg})
                notifier.sendNotification(notificationMessage)

                orderDetails = resp['order_params']
                twm.stop()
                # Placing a Market order using the stop loss 
                response = createFuturesSmartBuy(user_data,orderDetails)
                executed_on = datetime.datetime.utcnow()
                print(response)
                if response['status'] =='OK':
                    modify_order = modifyOrder(temp_order_id,'open', 'OK', executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)
                    
                    # Send notification to user
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
                    
                else:
                    modify_order = modifyOrder(temp_order_id,'closed', response['result'], executed_on, modified_on=datetime.datetime.utcnow())
                    msg = "db modification status",str(modify_order)

                    print(msg)

                    # Send notification to user
                    notificationMessage.update({"msg":msg})
                    notifier.sendNotification(notificationMessage)
                
            else:
                print("[X] Still checking the Trailing take profit triggers ---")

    
 
