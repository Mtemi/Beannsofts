
from flask.cli import FlaskGroup
from itsdangerous import exc

from app.src.models import UserModel, ExchangeModel, ExchangeEnum, OrdersModel, BotModel, PlansModel, SubscriptionModel, InvoiceModel, TerminalOrderModel, DCABotOrderModel, GridBotModel

# ADITIONALAS

from app.src.services.BotOperations import createBotOrderWebhook
from flask_restx import Resource
from app.src.config import Config, DevelopmentConfig

import datetime
from flask import request
from flask_socketio import SocketIO, emit, send

from coinbase_commerce.client import Client
from coinbase_commerce.webhook import Webhook
from coinbase_commerce.error import SignatureVerificationError, WebhookInvalidPayload

from flask_mail import Mail, Message
from flask_cors import CORS

from app.src.models import InvoiceModel
from app.src.services import OrderOperations
from app.src.services.pnl.pnlcalculator import pnlCalcualtor
from app.src.services.pnl.utils import getBotTradeDetails


# from app.src.utils import logging
from app import app, db, blueprint

import json
import time
import asyncio
import threading

# smart trade api imports
from app.src.utils.dto import SmartTradeDto
from app.src.controller import login_required
from app.src.services.SmartTrades.SmartBuy.exchangeVerificaton import verifyExchange
from app.src.models import ExchangeModel, SmartOrdersModel, UserModel
from app.src.utils.binance.streams import ThreadedWebsocketManager


# order api imports
from app.src.utils.dto import OrderDto
import math

# api vars
api = SmartTradeDto.api
smart = SmartTradeDto.smart

api2 = OrderDto.api


# Event stream settings
event_name = 'smart-buy'
msginfo = 'info'
msgerror = 'error'


import logging
# logger = logging.GetLogger(__name__)

# configure logging
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)



# ORiginal stuff begins here

app.register_blueprint(blueprint)

app.app_context().push()

# FIXME Extra stuff needs to be refactored to meet reviewed architecture of app
mail = Mail(app)

# Instantiating websocket
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=True, logger=True)

CORS(app)

cli = FlaskGroup(app)




@api.route('/trades/buy')
class SmartBuyResource(Resource):
    @api.doc("smart buy")
    @api.expect(smart, validate=True)
    @login_required
    def post(self,user):

        
        print(request.json)
        
        # socketio.emit('notification1', {'data': 'This is a test'}, broadcast=True)  
        # notification_ = {'data': 'This is a test'}
        
        limit_price = 0
        smart_order_type = request.json['smart_order_type']
        exchange_data = request.json['exchange_data']
        take_profit_targets = request.json['take_profit_targets']
        stop_loss_targets = request.json['stop_loss_targets']
        leverage_type = request.json['leverage_type']
        leverage_value = request.json['leverage']
        notional_amount = float(exchange_data['amount']) 
        if bool(exchange_data['limit_price']) is True:
            limit_price = float(exchange_data['limit_price'])
            print("limit_price", limit_price)

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
        
        
        # Emit a custom event back to the client
        # socketio.emit('custom_event1', f'Server says: leverage type is {leverage_type} \n leverage value is {leverage_value} \n Mode is {dualSidePosition}!')
        socketio.emit('custom_event6', f'Leverage Type is {leverage_type}')
        socketio.emit('custom_event7', f'Leverage Value is {leverage_value}')
        socketio.emit('custom_event8', f'Mode is {dualSidePosition}')
        
        

        # change position mode
        resp12 = OrderOperations.change_PositionMode(userId, exchangeName, orderDetails_Mode)
        # socketio.emit('change_position_result', {'message': resp12}, broadcast=True)
        print(resp12)
        
        print(resp12["status"])
        
         # Emit a custom event back to the client
        socketio.emit('custom_event2', f'Status is: {resp12["status"]}')
        
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

            if smart_order_type == 'market':  
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
                    socketio.emit('custom_event10', f'Exception message: {resp12["result"]}')
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
                
            if smart_order_type == 'limit':

                print("EXECUTING LIMIT ORDER WITH PRICE OF", limit_price)
                orderDetails = {
                    "symbol": symbol,
                    "side": "Buy",
                    "type": 'LIMIT',
                    "quantity": real_quantity,
                    "price": round(limit_price, 4),#FIXME for limit you must pass the price
                    "reduceOnly": False,
                    "timeInForce": "GTC"
                }
                print("DATA PASSED TO BINANCE FOR LIMIT ORDER", orderDetails)

                resp12 = OrderOperations.CreateBinanceFuturesOrderSmartBuy(userId, exchangeName, orderDetails)
                print(resp12)
                print(resp12["status"])
                if resp12["status"] == 'fail':
                    print("we add a return statement here")
                    # Emit a custom event back to the client
                    socketio.emit('custom_event9', f'Exception message: {resp12["result"]}')
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
            todb = {}
            if bool(stop_loss_targets) is True:
                todb = {
                    "smart_order_type": smart_order_type,
                    "exchange_id":exchange_data['exchange_id'],
                    "exchange_order_id":exchange_order_id,
                    "sl_steps":stop_loss_targets['stop_steps'],
                    "userid":user.id,
                    "symbol":exchange_data['symbol'],
                    "side":"Buy",
                    "amt":exchange_data['amount'],
                    "leverage_type":leverage_type,
                    "leverage_value":leverage_value,
                    "price":price,
                    "order_details_json": configs
                }
            else: 
                todb = {
                    "smart_order_type": smart_order_type,
                    "exchange_id":exchange_data['exchange_id'],
                    "exchange_order_id":exchange_order_id,
                    "sl_steps":0,
                    "userid":user.id,
                    "symbol":exchange_data['symbol'],
                    "side":"Buy",
                    "amt":exchange_data['amount'],
                    "leverage_type":leverage_type,
                    "leverage_value":leverage_value,
                    "price":price,
                    "order_details_json": configs
                }
            print("DATA TO BE PUSHED TO DB")
            print(todb)
            

            
            # the first order either market or limit which gave us the order ID was not saved here in the database . We only need 
            # to pick that orders, orderId and pass to the exchange_order_id parameter for the sl and tp order below.
            order = SmartOrdersModel(**todb)
            db.session.add(order)
            db.session.commit()
            exchange_data.update({"temp_order_id":exchange_order_id})
            
            print("________STOP_STEPS________________")
            print("Stop steps is: ", stop_loss_targets['stop_steps'])

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

            # global loop_status
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
                    global loop_status
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
                            if resp123l["status"] == 'fail':
                                print("we add a notofication return to the bot")
                                socketio.emit('order_creation_fail', {'reason': resp123l["result"]}, broadcast=True)
                                notification2_ = {'reason': resp123l["result"]}
                                # return {"message":"Fail", "result": str(resp123l["result"])}, 500
                            print(" ^^^^^^^^^^^^^^^^^^^^^^^^^")
                            if resp123l["status"] == 'ok' or resp123l["status"] == 'Ok' or resp123l["status"] == 'OK':
                                last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                                socketio.emit('order_creation_success', {'reason': resp123l["result"]}, broadcast=True)
                                notification3_ = {'reason': resp123l["result"]}
                                print(last_price)
                                price = last_price
                                exchange_order_id1 = resp123l["result"]["orderId"]
                                print("exchange_order_id LIMIT", exchange_order_id1)
                                db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'],  SmartOrdersModel.status == "open", SmartOrdersModel.side == "Buy", SmartOrdersModel.exchange_order_id == exchange_order_id).update({SmartOrdersModel.exchange_order_id == exchange_order_id1, SmartOrdersModel.price == str(price), SmartOrdersModel.status == 'filled'})
                                db.session.commit() 
                                twm.stop()
                                twm1.stop()
                                loop_status = False
                            else:
                                socketio.emit('failure1', {'futures_order_smartbuy_failure': resp123l["result"]}, broadcast=True)
                                notification4_ = {'futures_order_smartbuy_failure': resp123l["result"]}
                                print(resp123l)

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
                                last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                                print(last_price)
                                price = last_price
                                db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.side == "Buy", SmartOrdersModel.status == "open",  SmartOrdersModel.symbol == symbol).update({SmartOrdersModel.price == str(price), SmartOrdersModel.status == 'filled'})
                                db.session.commit() 
                                twm.stop()
                                twm1.stop()
                                 # Emit a custom event back to the client
                                socketio.emit('custom_event3', f'Server says: Order has been filled', broadcast=True) 

                                
                                # @socketio.on('disconnect')
                                # def handle_disconnect():
                                #     print('Client disconnected')
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
                                socketio.emit('create_futures_order_smartbuy', {'result': resp123l["result"]}, broadcast=True)
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

                            if resp123l["status"] == 'fail':
                                print("we add a notofication return to the bot")
                                # return {"message":"Fail", "result": str(resp123l["result"])}, 500
                            print(" ^^^^^^^^^^^^^^^^^^^^^^^^^")
                            if resp123l["status"] == 'ok' or resp123l["status"] == 'Ok' or resp123l["status"] == 'OK':
                                last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                                print(last_price)
                                price = last_price
                                exchange_order_id1 = resp123l["result"]["orderId"]
                                print("exchange_order_id LIMIT", exchange_order_id1)
                                db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'],  SmartOrdersModel.status == "open", SmartOrdersModel.side == "Buy", SmartOrdersModel.exchange_order_id == exchange_order_id).update({SmartOrdersModel.exchange_order_id == exchange_order_id1, SmartOrdersModel.price == str(price), SmartOrdersModel.status == 'filled'})
                                db.session.commit() 
                                twm.stop()
                                twm1.stop()
                                socketio.emit('custom_event4', f'Server says: Order has been filled again', broadcast=True) 
                                loop_status = False
                            else:  
                                print(resp123l)
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
                            socketio.emit('create_futures_order_smartbuy1', {'result': resp123l["result"]}, broadcast=True)
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
                                last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                                print(last_price)
                                price = last_price
                                db.session.query(SmartOrdersModel).filter(SmartOrdersModel.id == resp['userid'], SmartOrdersModel.side == "Buy", SmartOrdersModel.status == "open",  SmartOrdersModel.symbol == symbol).update({SmartOrdersModel.price == str(price), SmartOrdersModel.status == 'filled'})
                                db.session.commit() 
                                twm.stop()
                                twm1.stop()
                                loop_status = False

                        

                    #end of checking stop loss conditions
                    # tp computations start here
                    # these tp steps a locking profits by  updating stop loss and trailing stop values/trailing buy
                        
                    return floated_stop_loss_price_target
                
                @socketio.on('user_event')
                def handle_user_data(msg):
                    logging.info("_____Msg__________")
                    logging.info(msg['m'])
                    logging.info(msg['p'])
                    # print(msg) 
                    socketio.emit(msg['p'])
                    print(json.dumps(msg, indent=4))

                    # if msg['m'] == "True":
                    #     twm1.stop()
                    #     twm.stop()
                    #     logging.info("msg['m']")
                    #     # return {"message":"Trade Clossed Successfully", "status":400},200
                    # print(msg)

                # twm1.start_trade_socket(callback=handle_user_data,  symbol=symbol)
                # twm1.start_user_socket(callback=handle_user_data)
                # def start_book_ticker_socket():
                #     twm.start_symbol_book_ticker_socket(callback=handle_socket_message1, symbol=symbol)
                
                twm.start_symbol_book_ticker_socket(callback=handle_socket_message1, symbol=symbol)
                # twm.start()
                print("updated", floated_stop_loss_price_target)
                
                # async def asynchronous_while_loop():
                #     while loop_status:
                #         print("we are in the vloop")
                #         print("price within while True Loop")
                #         print(price)
                #         await asyncio.sleep(1)
                #         twm1.join()  
                #         twm.join()
                # if loop_status:
                #     async_loop = asyncio.get_event_loop()
                #     async_loop.run_until_complete(asynchronous_while_loop())

     
                    
                # def background_loop():
                #     iterations = 0
                #     while loop_status:
                #         print("we are in the vloop")
                #         print("price within while True Loop")
                #         print(price)
                #         time.sleep(1)
                #         iterations += 1
                #         logging.info(f"The loop_status is: {loop_status}")
                        
                #     print("loop status set to False")
                #     print(f"Made {iterations} iterations in the background loop.")
                #     print("Exiting background loop.")
                #         # twm1.join()  
                #         # twm.join()
                        
                    
                # def stop_loop_after_delay():
                #     time.sleep(30)  # Delay of 20 secs
                #     global loop_status
                #     loop_status = False
                #     logging.info("loop_status set to False")
                    
                
                
                # # Create a thread for the loop
                # loop_thread = threading.Thread(target=background_loop)
                # loop_thread.start()
                
                # # creating a thread for the stop_loop_after_delay
                # stop_loop_thread = threading.Thread(target=stop_loop_after_delay)
                # stop_loop_thread.start()
                
                
                # # Wait for all threads to finish
                # loop_thread.join()
                # # socket_thread.join()
                # stop_loop_thread.join()
                    
                    
                # # Clean up and stop any necessary operations
                # twm1.stop()
                # logging.info("twm1.stop() ACTIVATED")
                # twm.stop()
                # logging.info("twm.stop() ACTIVATED")
                    
                
                
                # while it's true that we have the streamed live data above 
                while loop_status:
                    print("we are in the vloop")
                    print("price within while True Loop")
                    print(price)
                    time.sleep(1)
                #     # we ned to update trailing stop loss only when price is above it, for the case of Buy
                #     # AND if price is below it, then our trailing stop loss algorithm takes over and 
                #     # if we decide to close our trailing stop loss algorithm , then we will close the open positions
                #     # if price is below sl, hence we won't see the need for the sl step algorithm
                #     # if float(take_profit_targets1["trailing_stop"]) > 0 and floated_stop_loss_price_target > trailing_stop:
                #     #     trailing_stop = floated_stop_loss_price_target-floated_stop_loss_price_target*float(take_profit_targets1["trailing_stop"])/100
                #     #     stop_loss_price=trailing_stop

                #     # below we have to only update trailing buy if price is below trailing buy price
                #     # else if price is above trailing buy , then we activate our various take profits algrithms
                #     # if we have to take the profits when price is above trailing take profit, then we don't need the 
                #     # trailing take profit/trailing buy algorithm
                #     # again if price went above trailing_buy, then we decide to take profit, we will take profit of the whole amount
                #     # this again will invalidate our various partial take profits
                #     # if float(take_profit_targets1["trailing_take_profit"]) > 0 and floated_stop_loss_price_target < trailing_buy:
                #     #     trailing_buy = floated_stop_loss_price_target+floated_stop_loss_price_target*float(take_profit_targets1["trailing_take_profit"])/100
                    

                #     # twm.start_symbol_book_ticker_socket(
                #     #     callback=handle_socket_message, symbol=exchange_data["symbol"])
                    twm1.join()  
                    twm.join()  
                #     # continue checking until all conditions are met execute the order and close the tasks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                
            except Exception as e:
                logging.error(f"exception hit after filtering terminal orders from db exception {str(e)}")
                socketio.emit('custom_event5', f'Server says: Exception type: {str(e)}', broadcast=True) 
                return {"message":"Fail", "result": str(e)}, 500
                    

        else:
            return {"message":"Invalid exchange type, smart order is a binance futures feature", "status":400},200



@api2.route('/all/filled/orders')
class All_Filled_Orders(Resource):
    #all orders saved in the database
    # @api.doc(params={'userId':'user id'})
    @login_required
    def get(self, user):
        
        # @socketio.on("filled_orders")
        # def filled_orders():
        #     """event listener when client connects to the server"""
        #     data_= "Francis"
        #     print("Message Sent to clinet")
        #     socketio.emit('custom_event_filled_orders', f'Server says: Message {data_} received!')
     
        userId = user.id
        
        try:
            page = int(request.args.get('page'))
        except TypeError:
            return {
                "status": 200,
                "message": "error page must be an integer"
            }
            
        data =  OrderOperations.filledBinancePlacedOrders(userId)
        
        
        print("__________BINANCE_ORDERS_DATA________________")
        print(data)
        

        result = data[0]['result']

        if len(result) == 0:
            return {
                "status": 200,
                "result": result
            }

        # current page
        # orders per page
        per_page = 5
        # total number of orders
        total_number = len(result)
        # total number of pages
        total_pages = math.ceil(total_number / per_page)
        
        socketio.emit('custom_event_filled_orders', f'Server says: You have {total_number} number of filled Orders!')

        # check validity of the page
        if page > total_pages:
            return {
                "status": 200,
                "message": "page number out of range"
            }

        # start index and end index for list slicing
        # check if is page 1
        if page == 1:
            start_index = 0
        else:
            start_index = ((page - 1) * per_page) 

        # check end index
        end_index = start_index + (per_page - 1)

        # initialize page data starting with none
        data_in_page = None

        # check if end index is not less than total
        if not ((end_index) < total_number):
            end_index = total_number - 1
        
        end_index += 1
        data_in_page = result[start_index:end_index]

        print(f"start index {start_index} endindex {end_index}")
        final_data = {
            "status": 200,
            "total_pages": total_pages,
            "current_page": page,
            "result" : data_in_page
        }

        return final_data



# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')

#     # Emit a custom event back to the client
#     socketio.emit('custom_event1', f'Server says: Message {test_} received!')
#     socketio.emit('custom_event2', f'Server says: Message {notification_} received!')
#     socketio.emit('custom_event3', f'Server says: Message {notification1_} received!')
#     socketio.emit('custom_event4', f'Server says: Message {notification2_} received!')
#     socketio.emit('custom_event5', f'Server says: Message {notification3_} received!')
#     socketio.emit('custom_event6', f'Server says: Message {notification4_} received!')
#     socketio.emit('custom_event7', f'Server says: Message {notification5_} received!')

# @socketio.on('message')
# def handle_message(message):
#     print('Received message:', message)
#     # result = calculation(int(message))
#     result = message
#     send(f'You said: {message} and the calculation is: {result}', broadcast=True)
    
#     data = OrderOperations.filledBinancePlacedOrders(5)

#     # Emit a custom event back to the client
#     socketio.emit('custom_event', f'Message: {data}')





def listen():
    """This method queries get symbolData and filters last BTC Price"""
    """THe method emits realtime BTC lastprice to the clientside UI"""
    while True:
        lastPrice = OrderOperations.getSymbolLastPrice()
        socketio.emit('BTCPrice', {'price': lastPrice}, broadcast=True)
        socketio.sleep(1)


@socketio.on('getBTCPrice')
def handle_connect():
    """Each time a websocket event getBtcPrice is passed it emits BTC lastprice"""
    listen()


def listenPnlData(botId, userId, botType, exchangeId):

    openOrders = getBotTradeDetails(
        botId=botId, userId=userId, botType=botType, exchangeId=exchangeId)

    print(openOrders)
    pnl = 0
    while True:
        pnl = 0
        for open_order in openOrders:
            resp = pnlCalcualtor(positionData=open_order,
                                 botId=botId, userId=userId)

            pnl += float(resp['unrealizedPnl'])
        # resp = pnlCalcualtor()
        socketname = "pnl"+botType+str(botId)

        print(resp)

        print(socketname)
        socketio.emit(socketname,
                      {'data': pnl}, broadcast=True)
        socketio.sleep(1)


@socketio.on('pnl')
def handlePnlData(data):
    print(data)
    botId = data['botId']
    userId = data['userId']
    botType = data['botType']
    exchangeId = data['exchangeId']

    print(botId, userId)

    if botType == 'grid':
        # TODO
        pass
    if botType == 'dca':
        # Get all the dca method
        listenPnlData(botId, userId, botType, exchangeId)


@app.route('/bot/webhook', methods=['POST'])
def respond():
    data = request.json

    botID = data['bot_id']
    userID = data['user_id']

    print(request.json)
    try:
        createBotOrderWebhook(botID)
    except Exception as e:
        error = {
            "msg": "DCA WEbhook order error",
            "error": str(e),
            "user_id": userID,
            "bot_id": botID
        }
        socketio.emit(error['user_id'], {'error': error}, broadcast=True)

    return "success", 200


@app.route('/invoices/webhook', methods=['POST'])
def invoiceWebhook():
    # event payload
    request_data = request.data.decode('utf-8')
    # webhook signature
    request_sig = request.headers.get('X-CC-Webhook-Signature', None)

    try:
        # signature verification and event object construction
        event = Webhook.construct_event(
            request_data, request_sig, Config.COINBASE_WEBHOOK_SECRET)
    except (WebhookInvalidPayload, SignatureVerificationError) as e:
        return str(e), 400

    logging.info("Received event: id={id}, type={type}".format(
        id=event.id, type=event.type))

    if "created" in event.type:
        invoiceUpdate = {
            "invoice_status":  event.type,
            "modified_on": datetime.datetime.utcnow(),
        }
        logging.info("paid invoice event")
        invoice = db.session.query(InvoiceModel).filter(
            InvoiceModel.invoice_id == event.data['id']).first()
        # print(invoice)
        if invoice is not None:
            print("inside invoice")
            db.session.query(InvoiceModel).filter(
                InvoiceModel.invoice_id == event.data['id']).update(invoiceUpdate)
            db.session.commit()

            # INITIATLIZE AND ACTIVATE THE SUBSCRIPTION
            subscriptionStartDate = datetime.datetime.utcnow(),
            subscriptionExpiryDate = datetime.datetime.utcnow() + datetime.timedelta(days=+30)

            subscription = {
                "start_date": subscriptionStartDate,
                "expiry_date": subscriptionExpiryDate,
                "is_active": True,
                "plan_id": invoice.plan_id
            }

            db.session.query(SubscriptionModel).filter(
                SubscriptionModel.user_id == invoice.user_id).update(subscription)
            # subscription = SubscriptionModel(**subscription)
            # db.session.add(subscription)
            db.session.commit()

            emailData = {
                "subject": "Payment Successfully Verified",
                "to": event.data.customer_email,
                #"body": f"Subscription Expiry Date: {subscriptionExpiryDate}, Plan: {invoice.plan}"
            }
            # Send acknowledgeent of Payment
            sendAsyncMail(emailData)

    return 'success', 200


# @api.route('/bot/record/error')
# class BotError(Resource):
#     def post(self):
#         error = request.json
#         logging.info("Bot error emited")
#         socketio.emit(error['userId'], {'error': error}, broadcast=True)
#         return 200

# Cronjobs for background tasks
# TODO create a cronjob/ celery task from this method


def sendAsyncMail(emailData):
    """Background task to send an email with Flask-Mail."""
    msg = Message(emailData['subject'],
                  sender=Config.MAIL_DEFAULT_SENDER,
                  recipients=[emailData['to']])
    msg.body = emailData['body']
    with app.app_context():
        logging.info("async background email sent")
        mail.send(msg)


def sendMail(emailData, app):
    """Background task to send an email with Flask-Mail."""
    msg = Message(emailData['subject'],
                  sender=Config.MAIL_DEFAULT_SENDER,
                  recipients=[emailData['to']])
    msg.body = emailData['body']
    with app.app_context():
        logging.info("email sent")
        mail.send(msg)


if __name__ == '__main__':
    # cli()
    socketio.run(app, host='0.0.0.0', port=3020)   
     

