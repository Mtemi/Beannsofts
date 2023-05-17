import time

from flask import request
from flask_restx import Resource

from app.src import db
from app.src.controller import login_required
from app.src.models import ExchangeModel, SmartOrdersModel, UserModel
from app.src.services import OrderOperations
from app.src.services.Notifications.Notification import Notification
from app.src.services.SmartTrades.dboperations import cancelOrder, updateTaskId
from app.src.services.SmartTrades.SmartBuy.exchangeVerificaton import verifyExchange
from app.src.utils import logging
from app.src.utils.binance.streams import ThreadedWebsocketManager
from app.src.utils.dto import SmartTradeDto
import sys
import os
from app.tasks import smartBuyTrade, smartCoverTrade, smartSellTrade, smartTrade
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '....')))
from flask_socketio import SocketIO
import json

socketio = SocketIO(cors_allowed_origins="*")
api = SmartTradeDto.api
smart = SmartTradeDto.smart
# Notification class instance
notifier = Notification()

logger = logging.GetLogger(__name__)
# Event stream settings
event_name = 'smart-buy'
msginfo = 'info'
msgerror = 'error'

@api.route('/trades/buy')
class SmartBuyResource(Resource):
    @api.doc("smart buy")
    @api.expect(smart, validate=True)
    @login_required
    def post(self,user):
        print(request.json)
        smart_order_type = request.json['smart_order_type']
        exchange_data = request.json['exchange_data']
        take_profit_targets = request.json['take_profit_targets']
        stop_loss_targets = request.json['stop_loss_targets']
        leverage_type = request.json['leverage_type']
        leverage_value = request.json['leverage']
        notional_amount = float(exchange_data['amount'])

        print("user", user)
        userId = user.id
        print("User ID", userId)
        telegram_id = user.telegram_id


        user = db.session.query(UserModel).filter_by(id=userId).first()
        # as you can see here, we are passing exchange name manually. That should not be the case, where we have several exhanges.  
        # we need to create Exchanges Model, with exhange name, id.  So that when a user selects an exchange name when passing an order,
        # the exchange ID is then passed and used to identify the exchange where the user is trading from 
        # this will give us a lee way to add other exchanges such as Bybit, Kucoin, OKX, Phemex, Huobi etc.
        exch_user_info = verifyExchange(user.id, "binance-futures", exchange_data['exchange_id'])
        print("smart_order_type", smart_order_type)
        trailing_take_profit = take_profit_targets['trailing_take_profit']

        exchange_name = db.session.query(ExchangeModel.exchange_name).filter_by(user_id=userId, exchange_type="binance-futures").first()
        print("exch_user_info", exch_user_info)
        print("trailing_take_profit", trailing_take_profit)

        exchangeName = str(exchange_name)[2:-3]
        print("exchangeName", exchangeName)
        print("SYMBOL PASSED", exchange_data['symbol'])
        symbol = exchange_data['symbol'].translate( { ord("/"): None } )
        print("exchange_data['symbol'].replace(}", symbol)
        
        orderDetails = {}
        exchange_order_id = ""
        dualSidePosition = False

        last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
        print(last_price)
        price  = float(last_price)
        real_quantity = int(notional_amount/price)
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print(" {} market price {} with size of {} is being posted", symbol, price, real_quantity)
        print("***********************************")

        if leverage_type == "cross":
            dualSidePosition = "CROSSED"

        if leverage_type == "isolated":
            dualSidePosition = "ISOLATED"

        orderDetails_Mode = {
            "symbol": symbol,
            "marginType": dualSidePosition,
        }

        # change position mode
        resp12 = OrderOperations.change_PositionMode(userId, exchangeName, orderDetails_Mode)
        print(resp12)
        print(resp12["status"])
        print(" ^^^^^^^^^^^CHANGING POSITION MODE^^^^^^^^^^^^^^")
        if resp12["status"] == 'ok' or resp12["status"] == 'Ok' or resp12["status"] == 'OK':
            last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
            print(last_price)

        orderDetails_Leverage = {
            "symbol": symbol,
            "leverage": leverage_value,
        }
        # set leverage
        resp12 = OrderOperations.set_Leverage(userId, exchangeName, orderDetails_Leverage)
        print(resp12)
        print(resp12["status"])
        print(" ^^^^^^^^^^^^CHANGING COIN LEVERAGE^^^^^^^^^^^^^")
        if resp12["status"] == 'ok' or resp12["status"] == 'Ok' or resp12["status"] == 'OK':
            last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
            print(last_price)

        if exch_user_info['status']:

            if take_profit_targets['take_profit_order_type'] == 'market':  
                orderDetails = {
                    "symbol": symbol,
                    "side": "Buy",
                    "type": 'MARKET',
                    "quantity": real_quantity
                }

                resp12 = OrderOperations.CreateBinanceFuturesOrderSmartBuy(userId, exchangeName, orderDetails)
                print(resp12)
                print(resp12["status"])
                if resp12["status"] == 'fail':
                    print("we add a return statement here")
                    return {"message":"Fail", "result": str(resp12["result"])}, 500
                print(" ^^^^^^^^^^^^^^^^^^^^^^^^^")
                if resp12["status"] == 'ok' or resp12["status"] == 'Ok' or resp12["status"] == 'OK':
                    last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                    print(last_price)
                    price = last_price
                    exchange_order_id = resp12["result"]["orderId"]
                    print("exchange_order_id MARKET", exchange_order_id)
                else:  
                    print(resp12)
                
            if take_profit_targets['take_profit_order_type'] == 'limit':
                orderDetails = {
                    "symbol": symbol,
                    "side": "Buy",
                    "type": 'LIMIT',
                    "quantity": real_quantity,
                    "price": float(exchange_data['amount']), #FIXME for limit you must pass the price
                    "timeInForce": "GTC"
                }

                resp12 = OrderOperations.CreateBinanceFuturesOrderSmartBuy(userId, exchangeName, orderDetails)
                print(resp12)
                print(resp12["status"])
                if resp12["status"] == 'fail':
                    print("we add a return statement here")
                    return {"message":"Fail", "result": str(resp12["result"])}, 500
                print(" ^^^^^^^^^^^^^^^^^^^^^^^^^")
                if resp12["status"] == 'ok' or resp12["status"] == 'Ok' or resp12["status"] == 'OK':
                    last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                    print(last_price)
                    price = last_price
                    exchange_order_id = resp12["result"]["orderId"]
                    print("exchange_order_id LIMIT", exchange_order_id)
                else:  
                    print(resp12)
            # we have to now proceed creating STOP/TAKE_PROFIT orders.
            # we will also pass TRAILING_STOP_MARKET to manage trailing BUY/SELL

            configs={
                    "take_profit_targets":take_profit_targets,
                    "stop_loss_targets":stop_loss_targets
                    }

            configs.update({"telegram_id": user.telegram_id})
        
            todb = {
                "smart_order_type": smart_order_type,
                "exchange_id":exchange_data['exchange_id'],
                "exchange_order_id":exchange_order_id,
                "sl_steps":stop_loss_targets['stop_steps'],
                "userid":user.id,
                "symbol":exchange_data['symbol'],
                "side":"Buy",
                "amt":exchange_data['amount'],
                "price":price,
                "order_details_json": configs
            }
            print("DATA TO BE PUSHED TO DB")
            print(todb)
            # the first order either market or limit which gave us the order ID was not saved here in the database . We only need 
            # to pick that orders, orderId and pass to the exchange_order_id parameter for the sl and tp order below.
            # order = SmartOrdersModel(**todb)
            # db.session.add(order)
            # db.session.commit()
            exchange_data.update({"temp_order_id":exchange_order_id})

            configs1 = {
                "telegram_id": telegram_id,
                "user_data": exch_user_info["user_data"],
                "exchange_data":exchange_data,
                "exchange_name":exchangeName,
                "smart_order_type": smart_order_type,
                "exchange_id":exchange_data['exchange_id'],
                "exchange_order_id":exchange_order_id,
                "sl_steps":stop_loss_targets['stop_steps'],
                "userid":user.id,
                "symbol":exchange_data['symbol'],
                "side":"Buy",
                "amt":exchange_data['amount'],
                "price":price,
                "order_details_json": configs
            }

            #   Here we will use the configs1 to activate smart order.  



            """
            consolidates all the smart buy checker units into one entity and user configurations... creating the Smart buy functionality
            """
            print("CONFIGS TO USE ON SMART TRADE")
            print(configs1)
            print("CONFIGS TO USE ON SMART TRADE")
            print("data type of the config param")
            print(type(configs1))
            user_data = configs1["user_data"]
            exchange_data = configs1["exchange_data"]
            exchange_order_id = configs1["exchange_order_id"]
            take_profit_targets= configs1["order_details_json"]["take_profit_targets"]
            stop_loss_targets= configs1["order_details_json"]["stop_loss_targets"]
            # temp_order_id = exchange_data["temp_order_id"]

            chatId = configs1["telegram_id"]
            
            {
                "msg": "Smart Trade",
                "msgType": msginfo,
                "eventName": event_name,
                "channel": user_data['user_id'],
                "chatId": chatId,
                "kwargs": {'extra':'no info'}
            }


            exchangeName = configs1['exchange_name']
            print("exchangeName", exchangeName)

            global loop_status
            loop_status = True

            try:
                twm = ThreadedWebsocketManager(api_key=user_data["api_key"], api_secret=user_data["api_secret"])
                twm1 = ThreadedWebsocketManager(api_key=user_data["api_key"], api_secret=user_data["api_secret"])
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
                twm1.start()
                print("web socket has been started and is open")

                # {'telegram_id': None, 'user_data': {'user_id': 5, 'api_key': '6rdtH7gywLNWKcicFAE5
                # RxELSx0BzIVgECSAQFuCixUj89VfREoHZqF12GJifBs7', 'api_secret': 'kFa5naWTaP9JsY5cJPxrNecO0tuK7sQf8odk
                # QD3y5o2TZUMuaJpqrLhDewF4F5G5', 'exchange_type': 'binance-futures'}, 'exchange_data': {'limit_price
                # ': 0, 'exchange_id': 2, 'symbol': 'SUI/USDT', 'amount': '10', 'temp_order_id': 16}, 'exchange_name
                # ': 'tela', 'smart_order_type': 'market', 'exchange_id': 2, 'exchange_order_id': 22703014, 'sl_step
                # s': '5', 'userid': 5, 'symbol': 'SUI/USDT', 'side': 'Buy', 'amt': '10', 'price': 1.324, 'order_det
                # ails_json': {'take_profit_targets': {'take_profit_price': 0, 'take_profit_order_type': 'market', '
                # trailing_take_profit': '10', 'trailing_stop': '10', 'take_profits': {'steps': [{'price': '10', 'qu
                # antity': '40'}, {'price': '15', 'quantity': '40'}]}}, 'stop_loss_targets': {'stop_loss_type': 'mar
                # ket', 'stop_loss_percentage': '5', 'stop_steps': '5', 'stop_loss_timeout': 0}, 'telegram_id': None
                # }}

                print("CONFIG DATA TO WORK WITH FOR THE SMART TRADES", configs)
                # for open_smart_order in open_smart_orders:
                # exchange_order_id
                resp = {
                    "orderid": configs1["exchange_order_id"],
                    "userid": configs1["userid"],
                    "amount": configs1["amt"],
                    "price": configs1["price"],
                    "exchange_order_id": configs1["exchange_id"],
                    "symbol": symbol,
                    "order_details_json": configs1["order_details_json"],
                    } 

                order_entry_price = price
                print("order_entry_price", order_entry_price)
                result1 = resp["order_details_json"]
                print(" TP AND SL order_details_json ", result1)
                take_profit_targets1 = result1["take_profit_targets"]
                stop_loss_targets1 = result1["stop_loss_targets"]

                #result1["take_profit_targets"]["take_profits"]["steps"][0] 
                print("TAKE PROFITS TARGET", take_profit_targets1)
                print("TRAILING STOP TARGETS", stop_loss_targets1)
                print("TAKE PROFITS TARGET trailing_take_profit", float(take_profit_targets1["trailing_take_profit"]))
                print("TRAILING STOP TARGETS trailing_stop", float(take_profit_targets1["trailing_stop"]))
                steps1 = take_profit_targets1["take_profits"]["steps"]
                print("steps1", steps1)

                stop_loss_targets1["trailing_stop"] = take_profit_targets1["trailing_stop"]
                print("stop_loss_targets1", stop_loss_targets1["trailing_stop"])
                global trailing_stop
                global trailing_buy
                global stop_loss_price
                trailing_stop_value = take_profit_targets1["trailing_stop"]
                trailing_tp_value = take_profit_targets1["trailing_take_profit"]
                print("trailing_stop_value", trailing_stop_value)
                print("trailing_tp_value", trailing_tp_value)

                if float(trailing_stop_value) > 0:
                    trailing_stop = float(price)-float(price)*float(trailing_stop_value)/100
                else: 
                    trailing_stop = 0

                if float(trailing_tp_value) > 0:
                    trailing_buy = float(price)+float(price)*float(trailing_tp_value)/100
                else: 
                    trailing_buy = 0
                print("the various take profits / the steps", steps1) 

                stop_loss_price = order_entry_price-(order_entry_price*float(trailing_stop_value)/100)
                stop_loss_11 = order_entry_price-(order_entry_price*float(stop_loss_targets1["stop_loss_percentage"])/100)
                sl_steps = stop_loss_targets1["stop_steps"]
                print("stop_loss_price", stop_loss_price)
                symbol=resp["symbol"].replace("/", "")
                print("symbol to querry price data", symbol) 
                floated_stop_loss_price_target = price

                def handle_socket_message1(price_data):
                    global trailing_stop
                    global trailing_buy
                    print("SET STOP LOSS PRICE", stop_loss_11)
                    print("trailing_stop init", trailing_stop)
                    print("trailing_buy init", trailing_buy)
                    price_data["s"]
                    price = float(price_data["b"])
                    floated_stop_loss_price_target = float(price)
                    trailing_stop1 = float(price)-float(price)*float(trailing_stop_value)/100
                    trailing_buy1 = float(price)+float(price)*float(trailing_tp_value)/100
                    print("NEW trailing_stop VALUE IN THE LOOP", trailing_stop1)
                    print("NEW trailing_buy VALUE IN THE LOOP", trailing_buy1)

                    if float(trailing_stop_value) > 0 and trailing_stop1 > trailing_stop:
                        trailing_stop = trailing_stop1
                        print("trailing_stop  price when price is above" , trailing_stop)

                    if float(trailing_take_profit) > 0 and trailing_buy1 < trailing_buy:
                        trailing_buy = trailing_buy1
                        print("trailing_buy when price is above" , trailing_buy)


                    # if take_profit_targets['take_profit_order_type'] == 'limit':
                    # Here we will have to update sl configs with a value of sl_steps-1
                    if float(trailing_stop_value) > 0: # trailing_buy is > 0, this means ON
                        global stop_loss_price
                        if trailing_stop == floated_stop_loss_price_target or floated_stop_loss_price_target < trailing_stop:
                        # if trailing_buy is hit, we adjust it and also adjsut sl
                            # trailing_buy = floated_stop_loss_price_target-floated_stop_loss_price_target*float(take_profit_targets1["trailing_take_profit"])/100
                            # price can reach set trailing buy or sl 
                            orderDetails = {
                                "symbol": exchange_data['symbol'].replace("/", ""),
                                "side": "Sell",
                                "type": 'LIMIT',
                                "quantity": real_quantity,
                                "price": float(floated_stop_loss_price_target), 
                                "reduceOnly": True,
                                "timeInForce": "GTC"
                            }
                            resp123l = OrderOperations.CreateBinanceFuturesOrderSmartBuy(resp['userid'], exchangeName, orderDetails)
                            print(resp123l)
                            twm.stop()
                            twm1.stop()
                            loop_status = False
                            # new_order_price = float(trailing_stop)-0.002*float(trailing_stop) # this new order price is good
                            # # above price will be used when and if we to enter  a limit order 
                            # # will clarify this from the client
                            # stop_loss_price=new_order_price-(new_order_price*float(stop_loss_11)/100)
                            # result1["stop_loss_targets"]["stop_loss_price"] = stop_loss_price
                            # resp["order_details_json"] = result1
                            # # below is a new Binance Futures Order with the new entry price as calculated above
                            # orderDetails223 = {
                            #     "symbol": exchange_data['symbol'].replace("/", ""),
                            #     "side": "Buy",
                            #     "type": 'MARKET',
                            #     "quantity": float(resp['amount'])
                            # }
                            # resp12 = OrderOperations.CreateBinanceFuturesOrderSmartBuy(resp['userid'], exchangeName, orderDetails223)
                            # print("repsonse after creating the initial stop loss",resp12)
                            # exchange_order_id = resp12["orderId"]
                            # print(resp12)

                            # if resp12: 
                            #     #the order is still open as a smart order, so we are yet to update it as filled
                            #     print("the order is still open as a smart order, so we are yet to update it as filled")
                            #     db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.sl_steps == int(sl_steps)-1, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.order_details_json == result1)
                            #     db.session.commit() 
                            #     #the new_order_price is the order price.  That will be used to place new orders
                            #     # update the order as filled so that it's not querried for filling
                            #     # print("update the order as filled so that it's not querried for filling")
                            #     # db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid']).update(SmartOrdersModel.status == 'filled')
                            #     # db.session.commit() 

                    # print("trailing_stop final", trailing_stop)
                    # print("trailing_buy final", trailing_buy)
                    # these sl steps a locking profits by  updating trailing Buy 
                    print("sl steps",sl_steps)
                    sl_stepss = int(sl_steps)
                    for i in range(sl_stepss-1):

                        # the below if is a limit order but without trailing_take_profit
                        # else: # trailing_buy is zero, this means off
                        if stop_loss_price == floated_stop_loss_price_target or floated_stop_loss_price_target < stop_loss_price :

                            orderDetails = {
                                "symbol": exchange_data['symbol'].replace("/", ""),
                                "side": "Sell",
                                "type": 'LIMIT',
                                "quantity": real_quantity,
                                "price": float(floated_stop_loss_price_target), 
                                "reduceOnly": True,
                                "timeInForce": "GTC"
                            }

                            resp123l = OrderOperations.CreateBinanceFuturesOrderSmartBuy(resp['userid'], exchangeName, orderDetails)
                            print(resp123l)

                            new_order_price = float(stop_loss_price)-0.002*float(stop_loss_price) # this new order price is good
                            stop_loss_price=new_order_price-(new_order_price*float(stop_loss_11)/100)
                            result1["stop_loss_targets"]["stop_loss_price"] = stop_loss_price
                            # resp["order_details_json"] = result1
                            # below is a new Binance Futures Order with the new entry price as calculated above
                            sl_stepss = sl_stepss-1
                            if sl_stepss == 0:
                                twm.stop()
                                twm1.stop()
                                loop_status = False
                            else:
                                orderDetails223 = {
                                    "symbol": exchange_data['symbol'].replace("/", ""),
                                    "side": "Sell",
                                    "type": 'LIMIT',
                                    "quantity": real_quantity,
                                    "price": new_order_price, 
                                    "timeInForce": "GTC"
                                }
                                resp12 = OrderOperations.CreateBinanceFuturesOrderSmartBuy(resp['userid'], exchangeName, orderDetails223)
                                print("repsonse after creating the initial stop loss",resp12)
                                # exchange_order_id = resp12["result"]["orderId"]
                                # print("exchange_order_id ", exchange_order_id)
                                # twm.start()
                                # exchange_order_id = resp12["orderId"]
                                # print(resp12)

                                # if resp12: 
                                #     #the order is still open as a smart order, so we are yet to update it as filled
                                #     print("the order is still open as a smart order, so we are yet to update it as filled")
                                #     db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.sl_steps == int(sl_steps)-1, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.order_details_json == result1)
                                #     db.session.commit() 
                                    #the new_order_price is the order price.  That will be used to place new orders
                                    # update the order as filled so that it's not querried for filling
                                    # print("update the order as filled so that it's not querried for filling")
                                    # db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid']).update(SmartOrdersModel.status == 'filled')
                                    # db.session.commit() 


                    steps2 = steps1
                    # print(f'JSON PAYLOAD TO LOOP: {steps2}')
                    size_of_tp = len(steps1)
                    # print(f'Size of data: {size_of_tp} in INT')
                    #end of checking stop loss conditions
                    # tp computations start here
                    # these tp steps a locking profits by  updating stop loss and trailing stop values/trailing buy

                    if float(stop_loss_targets1["trailing_stop"]) > 0:
                        print(f'trailing_buy PRICE: {trailing_buy} while market price is: {floated_stop_loss_price_target}')
                        # print(f'if these are equal or market prrice is greater than trailing_buy, we CLOSE PREVIOUS POSITION AND OPEN NEW POSITION ')
                        # print(f'This basically helps us BUY AT DUMPS, the size of a DUMP equals to trailing_buy % passed')
                        # print(f'This means the trailing_buy % passed MUST be greater than the stop loss or trailing stop values for this function to function efefctively')
                        if trailing_buy == floated_stop_loss_price_target or floated_stop_loss_price_target > trailing_buy:
                            
                            orderDetails = {
                                "symbol": exchange_data['symbol'].replace("/", ""),
                                "side": "Sell",
                                "type": 'LIMIT',
                                "quantity": real_quantity,
                                "price": float(floated_stop_loss_price_target), 
                                "reduceOnly": True,
                                "timeInForce": "GTC"
                            }
                            resp123l = OrderOperations.CreateBinanceFuturesOrderSmartBuy(resp['userid'], exchangeName, orderDetails)
                            print(resp123l)
                            twm.stop()
                            twm1.stop()
                            loop_status = False
                            # exchange_order_id = resp12["result"]["orderId"]
                            # print("exchange_order_id ", exchange_order_id)
                            # twm.start()
                            # exchange_order_id = resp12["orderId"]
                            # print(resp12)

                            # if resp12: 
                            #     #the order is still open as a smart order, so we are yet to update it as filled
                            #     print("the order is still open as a smart order, so we are yet to update it as filled")
                            #     db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.sl_steps == int(sl_steps)-1, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.order_details_json == result1)
                            #     db.session.commit() 
                                
                                # then after entry becoming sl, we also make entry same value as hit tp
                                # steps2.remove(i) #after removing a step from the TPs available, I will add the step2 param to 
                                # resp["order_details_json"] = result1
                                # below is a new Binance Futures Order with the new entry price as calculated above
                                #the order is still open as a smart order, so we are yet to update it as filled

                                # print("the order is still open as a smart order, so we are yet to update it as filled")
                                # db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.amt == new_order_quantity, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.order_details_json == result1)
                                # db.session.commit() 


                    for i in range(size_of_tp-1):
                        # else: 
                        # price11 = float(steps2[i]["price"])
                        price11 = floated_stop_loss_price_target+floated_stop_loss_price_target*float(steps2[i]["price"])/100  # noqa: E501
                        # but again the quntity below need be a certain % of our position value in usd 
                        quantity11 = int(real_quantity*float(steps2[i]["quantity"])/100) # was calculated during entry
                        print(f'price of takeProfit : {i} is {price11}')
                        # print("data streamed from binance streams where we want to get the price", floated_stop_loss_price_target)
                        # print("the price above will be used to compare with the set tp price")
                        # print("price fetched from the Binance futures websocket streams" , floated_stop_loss_price_target)
                        if price11 == floated_stop_loss_price_target or floated_stop_loss_price_target > price11 : # it means here that the target has been hit
                            # the res as a new config then I will update this new TP steps to the   smart order
                            result1["take_profit_targets"]["take_profits"]["steps"][0] == steps2
                            
                            orderDetails = {
                                "symbol": exchange_data['symbol'].replace("/", ""),
                                "side": "Sell",
                                "type": 'LIMIT',
                                "quantity": quantity11,
                                "price": float(floated_stop_loss_price_target), 
                                "reduceOnly": True,
                                "timeInForce": "GTC"
                            }
                            resp123l = OrderOperations.CreateBinanceFuturesOrderSmartBuy(resp['userid'], exchangeName, orderDetails)
                            print(resp123l)
                            # if resp123l: 
                            new_order_price = float(steps2[i]["price"]) # this new order price is good and thus cannot be a limit order
                            # but will be updated on the smartOrder price.  This is very necessary incase price starts going down and needs
                            # to follow the rules of the SL
                            # it automatically becomes a market order
                            #if a step is hit, I should remove it from steps and update SmartOrdersModel
                            result1["stop_loss_targets"]["stop_loss_price"] = float(resp['price']) # for tp, entry price becomes sl 
                            resp['price'] = steps2[i]["price"]  # then after entry becoming sl, we also make entry same value as hit tp
                            
                            steps2.remove(i) #after removing a step from the TPs available, I will add the step2 param to 
                            # resp["order_details_json"] = result1
                            # below is a new Binance Futures Order with the new entry price as calculated above
                            #the order is still open as a smart order, so we are yet to update it as filled
                        
                            steps2.remove(i) #after removing a step from the TPs available, I will add the step2 param to 
                            # print("the order is still open as a smart order, so we are yet to update it as filled")
                            # db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.exchange_order_id == exchange_order_id).update(SmartOrdersModel.exchange_order_id == exchange_order_id, SmartOrdersModel.amt == new_order_quantity, SmartOrdersModel.price == str(new_order_price), SmartOrdersModel.order_details_json == result1)
                            # db.session.commit() 
                            size_of_tp = size_of_tp-1
                            if size_of_tp == 0:
                                twm.stop()
                                twm1.stop()
                                loop_status = False

                        

                    #end of checking stop loss conditions
                    # tp computations start here
                    # these tp steps a locking profits by  updating stop loss and trailing stop values/trailing buy
                        
                    return floated_stop_loss_price_target
                
                @socketio.on('user_event')
                def handle_user_data(msg):
                    logger.info("_____Msg__________")
                    # print(msg) 
                    # socketio.emit(msg)
                    print(json.dumps(msg, indent=4))

                    # if msg['m'] == "True":
                    #     twm1.stop()
                    #     twm.stop()
                    #     logger.info("msg['m']")
                    #     # return {"message":"Trade Clossed Successfully", "status":400},200
                    # print(msg)

                # twm1.start_trade_socket(callback=handle_user_data, symbol=symbol)
                # twm1.start_trade_socket(callback=handle_user_data,  symbol=symbol)
                # twm1.start_user_socket(callback=handle_user_data)
                twm.start_symbol_book_ticker_socket(callback=handle_socket_message1, symbol=symbol)
                
                # twm.start()
                print("updated", floated_stop_loss_price_target)
                
                # while it's true that we have the streamed live data above 
                while loop_status:
                    print("we are in the vloop")
                    print("price within while True Loop")
                    print(price)
                    time.sleep(1)
                    # we ned to update trailing stop loss only when price is above it, for the case of Buy
                    # AND if price is below it, then our trailing stop loss algorithm takes over and 
                    # if we decide to close our trailing stop loss algorithm , then we will close the open positions
                    # if price is below sl, hence we won't see the need for the sl step algorithm
                    # if float(take_profit_targets1["trailing_stop"]) > 0 and floated_stop_loss_price_target > trailing_stop:
                    #     trailing_stop = floated_stop_loss_price_target-floated_stop_loss_price_target*float(take_profit_targets1["trailing_stop"])/100
                    #     stop_loss_price=trailing_stop

                    # below we have to only update trailing buy if price is below trailing buy price
                    # else if price is above trailing buy , then we activate our various take profits algrithms
                    # if we have to take the profits when price is above trailing take profit, then we don't need the 
                    # trailing take profit/trailing buy algorithm
                    # again if price went above trailing_buy, then we decide to take profit, we will take profit of the whole amount
                    # this again will invalidate our various partial take profits
                    # if float(take_profit_targets1["trailing_take_profit"]) > 0 and floated_stop_loss_price_target < trailing_buy:
                    #     trailing_buy = floated_stop_loss_price_target+floated_stop_loss_price_target*float(take_profit_targets1["trailing_take_profit"])/100
                    

                    # twm.start_symbol_book_ticker_socket(
                    #     callback=handle_socket_message, symbol=exchange_data["symbol"])
                    twm1.join()  
                    twm.join()  
                    # continue checking until all conditions are met execute the order and close the tasks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                
            except Exception as e:
                logger.error(f"exception hit after filtering terminal orders from db exception {str(e)}")
                return {"message":"Fail", "result": str(e)}, 500
                    

        else:
            return {"message":"Invalid exchange type, smart order is a binance futures feature", "status":400},200


@api.route('/trades/cancel')
class SmartBuyResource(Resource):
    @api.doc("smart Trade cancel")
    # @api.expect(smart, validate=True)
    @login_required
    def post(self, user):
        smart_order_id = request.json['smart_order_id']
        resp = cancelOrder(smart_order_id)
        if resp['status'] is True:
            # delete the redis thread that
            smartBuyTrade.AsyncResult(resp['task_id']).revoke(terminate=True)
            return {"message":"success", "status":200},200
        else:
            return {"message":"Task not cancelled succesifully", "error":resp, "status":400},200
        
            
@api.route('/trades/sell')
class SmartSellResource(Resource):
    @api.doc("smart sell")
    @api.expect(smart, validate=True)
    @login_required
    def post(self, user):
        """"Smart Sell Order Operation"""
        userId = user.id
        smart_order_type = request.json['smart_order_type']
        exchange_data = request.json['exchange_data']
        take_profit_targets = request.json['take_profit_targets']
        stop_loss_targets = request.json['stop_loss_targets']
        user = db.session.query(UserModel).filter_by(id=userId).first()
        exch_user_info = verifyExchange(user.id, "binance-futures", exchange_id=exchange_data['exchange_id'])
        if exch_user_info['status']:
            
            configs={
                "take_profit_targets":take_profit_targets,
                "stop_loss_targets":stop_loss_targets
            }

            configs.update({"telegram_id": user.telegram_id})
                
            todb = {
                "smart_order_type": smart_order_type,
                "exchange_id":exchange_data['exchange_id'],
                "userid":user.id,
                "symbol":exchange_data['symbol'],
                "side":"Sell",
                "amt":exchange_data['amount'],
                "order_details_json": configs
            }
            order = SmartOrdersModel(**todb)
            db.session.add(order)
            db.session.commit()
            exchange_data.update({"temp_order_id":order.id})
            configs.update({
                "user_data": exch_user_info["user_data"],
                "exchange_data":exchange_data,
            })
            
            try:
                # send to celery task
                print(configs)
                smart_buy_task = smartSellTrade.apply_async(args=(configs,))
                resp = updateTaskId(order.id, smart_buy_task.id)
                if resp['status'] is True:
                    response_data ={"smart_order_id":order.id, "task_id":smart_buy_task.id}
                    return {"message":"success", "data":response_data}
                else:
                    return {"message":"Order not successifully", "error": resp["message"], "status":400}
            except Exception as e:
                return {"message":"Order not started successifully", "error":str(e), "status":400},200

            # save on the database
        else:
            return {"message":"Invalid exchange type, smart order is a binance futures feature", "status":400},200

@api.route('/trades/cover')
class SmartCoverResource(Resource):
    @api.doc("smart cover")
    @api.expect(smart, validate=True)
    @login_required
    def post(self, user):
        """"Smart Cover Order Operation"""
        userId = user.id
        smart_order_type = request.json['smart_order_type']
        exchange_data = request.json['exchange_data']
        take_profit_targets = request.json['take_profit_targets']
        stop_loss_targets = request.json['stop_loss_targets']
        trailing_buy = request.json['trailing_buy']
        order_type = request.json['order_type']
        trigger_price = request.json['trigger_price']

        

        user = db.session.query(UserModel).filter_by(id=userId).first()

        exch_user_info = verifyExchange(user.id, "binance")
        if exch_user_info['status']:
            configs={
                "take_profit_targets":take_profit_targets,
                "stop_loss_targets":stop_loss_targets,
                "trailing_buy": trailing_buy,
                "order_type": order_type,
                "trigger_price": trigger_price
            }

            configs.update({"telegram_id": user.telegram_id})
                
            todb = {
                "smart_order_type": smart_order_type,
                "exchange_id":exchange_data['exchange_id'],
                "userid":user.id,
                "symbol":exchange_data['symbol'],
                "side":"Sell",
                "amt":exchange_data['amount'],
                "order_details_json": configs
            }
            order = SmartOrdersModel(**todb)
            db.session.add(order)
            db.session.commit()
            exchange_data.update({"temp_order_id":order.id})
            configs.update({
                "user_data": exch_user_info["user_data"],
                "exchange_data":exchange_data,
            })
            
            try:
                # send to celery task
                smart_cover_task = smartCoverTrade.apply_async(args=(configs,))
                resp = updateTaskId(order.id, smart_cover_task.id)
                if resp['status'] is True:
                    response_data ={"smart_order_id":order.id, "task_id":smart_cover_task.id}
                    return {"message":"success", "data":response_data}
                else:
                    return {"message":"Order not successifully", "error": resp["message"], "status":400}
            except Exception as e:
                return {"message":"Order not started successifully", "error":str(e), "status":400},200

            # save on the database
        else:
            return {"message":"Invalid exchange type, smart order is a binance futures feature", "status":400},200


@api.route('/trades/trade')
class SmartCoverResource(Resource):
    @api.doc("smart cover")
    @api.expect(smart, validate=True)
    @login_required
    def post(self, user):
        """"Smart Trade Order Operation"""
        userId = user.id
        
        # print("request on smart Buy is below")
        # print(request)
        # print("request on smart Buy is above")
        smart_order_type = request.json['smart_order_type']
        exchange_data = request.json['exchange_data']
        take_profit_targets = request.json['take_profit_targets']
        stop_loss_targets = request.json['stop_loss_targets']
        trailing_buy = request.json['trailing_buy']
        order_type = request.json['order_type']
        trigger_price = request.json['trigger_price']

        user = db.session.query(UserModel).filter_by(id=userId).first()
        exch_user_info = verifyExchange(user.id, "binance")
        if exch_user_info['status']:
            configs={
                "take_profit_targets":take_profit_targets,
                "stop_loss_targets":stop_loss_targets,
                "trailing_buy": trailing_buy,
                "order_type": order_type,
                "trigger_price": trigger_price
            }

            configs.update({"telegram_id": user.telegram_id})
                
            todb = {
                "smart_order_type": smart_order_type,
                "exchange_id":exchange_data['exchange_id'],
                "userid":user.id,
                "symbol":exchange_data['symbol'],
                "side":"Buy",
                "amt":exchange_data['amount'],
                "order_details_json": configs
            }
            order = SmartOrdersModel(**todb)
            db.session.add(order)
            db.session.commit()
            exchange_data.update({"temp_order_id":order.id})
            configs.update({
                "user_data": exch_user_info["user_data"],
                "exchange_data":exchange_data,
            })
            
            try:
                # send to celery task
                smart_trade_task = smartTrade.apply_async(args=(configs,))
                resp = updateTaskId(order.id, smart_trade_task.id)
                if resp['status'] is True:
                    response_data ={"smart_order_id":order.id, "task_id":smart_trade_task.id}
                    return {"message":"success", "data":response_data}
                else:
                    return {"message":"Order not successifully placed", "error": resp["message"], "status":400}
            except Exception as e:
                return {"message":"Order not started successifully", "error":str(e), "status":400},200
            # save on the database
        else:
            return {"message":"Invalid exchange type, smart order is a binance futures feature", "status":400},200
