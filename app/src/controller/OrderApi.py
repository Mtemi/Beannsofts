from ast import Pass
from flask_restx import Resource
from flask import request, send_from_directory, send_file
from numpy import broadcast

from app.src.models.exchange import ExchangeModel
from app.src.models.smartorders import SmartOrdersModel
from app.src.models.users import UserModel

from . import login_required
from app.src import db, app
import csv

from app.src.utils.dto import OrderDto

from app.src.utils import logging

from app.src.services import OrderOperations

from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps

from app.src.utils.binance.streams import ThreadedWebsocketManager

from pprint import pprint
from app.src.utils.binance.clientOriginal import Client as BinanceClient
from app.src.services.SmartTrades.SmartBuy.exchangeVerificaton import verifyExchange
from flask_socketio import SocketIO, emit, send
from flask_cors import CORS

import math


# Instantiating websocket
socketio = SocketIO(app, cors_allowed_origins="*")

logger = logging.GetLogger(__name__)

api = OrderDto.api
orderList = OrderDto.orderList
createOrderSpot = OrderDto.createOrderSpot
createOrderFutures = OrderDto.createOrderFutures
getAcctBalance = OrderDto.getAcctBalance



test_ = "James"

@api.route('/list_orders/', endpoint='list_orders')
class ListTrades(Resource):
    @api.doc(params={'symbol': 'trading symbol', 'startDate': 'startDate', 'endDate': 'the end date'})
    @login_required
    def get(self, user):
        symbol = request.args.get('symbol')
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
        userId = user.id

        if symbol == None:
            return OrderOperations.getAllUserOrders(userId)
        elif symbol != None and (startDate == None or endDate == None):
            return OrderOperations.getUserOrdersBySymbol(userId, symbol)
        elif startDate != None and endDate != None or startDate != None:
            return OrderOperations.getUserOrdersByDate(userId, startDate, endDate)
        else:
            return OrderOperations.getAllUserOrders(userId)


@api.route('/get_trade_csv/')
class ListTradesCSV(Resource):
    @api.doc(params={'userId':'the user id'})
    def get(self):
        userId = request.args.get('userId')
        orders = OrderOperations.queryOrderData(userId)
        try:
            with open('orders.csv', "w", newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=' ',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(orders)

            return send_file('orders.csv', attachment_filename='export.csv', mimetype='text/csv', as_attachment=True)
        except FileNotFoundError:
            logger.exception("file not found")


@api.route('/get_positions_binance/')
class OpenOrders(Resource):
    @api.doc(params={'exchange_name': 'the exchange name to get api data from'})
    @login_required
    def get(self, user):
        userId: str = user.id
        exchange_name = request.args.get('exchange_name')
        return OrderOperations.ListBinanceOpenPositions(userId, exchange_name)

# add pagination
@api.route('/all_binance_orders/')
class AllOrders(Resource):
    """
    Order History for specific symbol
    """
    @api.doc('Get order history for specific symbol')
    @api.doc(params={'exchange_name': 'the exchange name to get api data from', 'symbol': 'trading pair symbol', 'page': 'page to be rendered'})
    @login_required
    def get(self, user):
        exchange_name = request.args.get('exchange_name')
        userId= user.id
        symbol = request.args.get('symbol')

        try:
            page = int(request.args.get('page'))
        except TypeError:
            return {
                "status": 200,
                "message": "error page must be an integer"
            }

        data = OrderOperations.ListAllBinanceOrders(userId, exchange_name, symbol)
        
        result = data[0]['result']

        print(f"The result of listBinanceOrders: {result}")
        
        if len(result) == 0:
            return {
                "status": 200,
                "result": result
            }

        # current page
        # orders per page
        per_page = 10
        # total number of orders
        total_number = len(result)
        # total number of pages
        total_pages = math.ceil(total_number / per_page)

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

@api.route('/binance/create/spot')
class CreateBinanceSpotOrder(Resource):
    @api.doc('create a binance spot order from the terminal windows')
    @api.expect(createOrderSpot, validate=True)
    @login_required
    def post(self, user):
        exchangeName = request.json['exchange_name']
        userId = user.id
        # orderDetails = {
        #     "symbol": request.json['symbol'],
        #     "side": request.json['side'],
        #     "type": request.json['type'],
        #     "quantity": request.json['quantity'],
        #     "price": request.json['price'],
            
        # }
        orderDetails = request.json
        if 'price' in orderDetails:
            orderDetails['price'] = float(orderDetails['price'])
            orderDetails['quantity'] = float(orderDetails['quantity'])
        return OrderOperations.CreateBinanceSpotOrder(userId, exchangeName, orderDetails)


@api.route('/binance/create/futures')
class CreateBinanceFuturesOrder(Resource):
    @api.doc('create a binance Futures order from the terminal windows')
    @api.expect(createOrderFutures, validate=True)
    @login_required
    def post(self, user):
        exchangeName = request.json['exchange_name']
        userId = user.id
        orderDetails = {
            "symbol": request.json['symbol'],
            "side": request.json['side'],
            "type": request.json['type'],
            "quantity": request.json['quantity'],
            "price": request.json['price'],
            "takeProfit": request.json['takeProfit'],
            "stopLoss": request.json['stopLoss'],
            "callbackRate": request.json['callbackRate'],
            "leverage": request.json['leverage']
        }

        return OrderOperations.CreateBinanceFuturesOrder(userId, exchangeName, orderDetails)



# same functionality but added with getting balance
@api.route('/open_orders/binance')
class OpenOrders(Resource):
    @api.doc("Get all open orders from binance")
    @api.doc(params={'exchange_name': 'the exchange name to get api data from'})
    @login_required
    def get(self,user):
        exchange_name = request.args.get('exchange_name')
        userId =user.id

        def fetchBinanceKeys(user, exchange_name):
            return db.session.query(ExchangeModel).filter(ExchangeModel.user_id == user, ExchangeModel.exchange_name == exchange_name).first()

        ApiData = fetchBinanceKeys(user, exchange_name)
        key = ApiData.key
        secret = ApiData.secret

        bm = ThreadedWebsocketManager(api_key=key, api_secret=secret)

        def handle_user_data(msg):
            logger.info("_____Msg__________")
            print(msg)
            if msg['e'] == 'outboundAccountInfo':
                # Parse the balance data from the WebSocket message
                balances = []
                for balance in msg['B']['b']:
                    balances.append({
                        'asset': balance['a'],
                        'balance': float(balance['f']),
                        'available': float(balance['f']) - float(balance['l'])
                    })
                logger.info("_______Balances:_____________")
                print(balances)
            elif msg['e'] == 'outboundAccountPosition':
                # Parse the position data from the WebSocket message
                positions = []
                for asset in msg['B']:
                    positions.append({
                        'symbol': asset['a'],
                        'amount': float(asset['f']),
                        'available': float(asset['f']) - float(asset['l'])
                    })
                logger.info("_______Po_____________")
                print(positions)

        # Subscribe to the user data WebSocket
        bm.start_user_socket(callback=handle_user_data)

        # Wait for WebSocket events
        bm.join()

        # Get the open orders from the Binance API
        orders = OrderOperations.ListBinancePositions(userId, exchange_name)

        # Get the balances from the Binance API
        # balances = []
        # account_info = BinanceClient.get_account(api_key=key, api_secret=secret)
        # for balance in account_info['balances']:
        #     if float(balance['free']) > 0 or float(balance['locked']) > 0:
        #         balances.append({
        #             'asset': balance['asset'],
        #             'balance': float(balance['free']) + float(balance['locked']),
        #             'available': float(balance['free'])
        #         })

        # Combine the open orders and balances into a single response
        # response = {
        #     'open_orders': orders,
        #     'balances': balances
        # }


        return orders



@api.route('/positions/binance')
class OpenPositions(Resource):
    @api.doc(params={'exchange_name': 'the exchange name to get api data from'})
    @login_required
    def get(self,user):
        exchange_name = request.args.get('exchange_name')
        userId =user.id
        # query exchange for api keys
        # check if exchange_name exists
        exchange = ExchangeModel.query.filter_by(exchange_name=exchange_name, user_id=userId).first()
        print(f"exchange found---{exchange}")

       
        if exchange:
            try:
                client = BinanceFuturesOps(
                api_key=exchange.key, api_secret=exchange.secret, trade_symbol="BTCUSDT")
            except Exception as e:
                return {
                "status": "400",
                "message": str(e)
            }
            
            position = client.checkPositionInfo()
            # print(position)
            if not position:
                return "You have no open positions"
            processed = []
            # print(position)
            for pos in position:
                if float(pos['unRealizedProfit']) != float("0.00000000"):
                    # print("positon response", pos)
                    side = "SELL" if float(pos['positionAmt']) < 0 else "BUY"
                    data = {
                        "symbol": pos["symbol"],
                        "positionSide": pos["positionSide"],
                        "unRealizedProfit": pos["unRealizedProfit"],
                        "liquidationPrice": pos['liquidationPrice'],
                        "positionAmt": pos['positionAmt'],
                        "side": side
                    }
                    processed.append(data)

            # if processed == []:
            #     return "You have no open positions"

            return {
                "status": "OK",
                "result": processed
            }, 200
        else:
            return {
                "status": "400",
                "message": "exchange does not exist"
            }
            
        # ApiData = fetchBinanceKeys(user, exchange_name)
        # key = ApiData.key
        # secret = ApiData.secret
        # exchangeType = ApiData.exchange_type

        
@api.route('/all/orders')
class All_Orders(Resource):
    
    # def calculation(self, test):
    #     global test_
    #     test_ = test
    #     return test
    
    #all orders saved in the database
    # @api.doc(params={'userId':'user id'})
    @login_required
    def get(self, user):
        # global test_
        userId = user.id
       
        try:
            page = int(request.args.get('page'))
        except TypeError:
            return {
                "status": 200,
                "message": "error page must be an integer"
            }
            
        data =  OrderOperations.allBinancePlacedOrders(userId)
        # test_ = "Hello"
        # self.calculation(test)
        
        
        
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

@api.route('/account/balance')
class AssetBalances(Resource):
    @api.expect(getAcctBalance, validate=True)
    @login_required
    def post(self, user):
        """Get all the user asset balances"""
        exchangeName = request.json['exchange_name']
        userId = user.id
        symbol = request.json['symbol']
        return OrderOperations.getAssetBalance(userId, exchangeName, symbol)
    
    
@api.route('/close/order')
class CloseOrders(Resource):
    @login_required
    def delete(self, user):
        socketio.emit('close_order', {'data': 'close order'})
        exchange_order_id = request.args.get('exchange_order_id')
        unfiltered_symbol = request.args.get('symbol')
        smart_order_type = request.args.get('smart_order_type')
        quantity = request.args.get('amt')
        # exchange_order_id = request.json['exchange_order_id']
        # symbol = request.json['symbol']
        # smart_order_type = request.json['smart_order_type']
        # quantity = request.json['amt']
        userId =user.id
        
        print(f"Unfiltered symbol: {unfiltered_symbol}, quantity:{quantity} ")
        # edit symbol
        filtered_symbol = unfiltered_symbol.replace("/", "")
        symbol = filtered_symbol.upper()
        
        print(f"Filtered symbol: {symbol} ")
        
        user = db.session.query(UserModel).filter_by(id=userId).first()
        # exch_user_info = verifyExchange(user.id, "binance-futures", exchange_order_id)
        
        exchange_name = db.session.query(ExchangeModel.exchange_name).filter_by(user_id=userId, exchange_type="binance-futures").first()
        

        exchangeName = str(exchange_name)[2:-3]
        print("exchangeName: ", exchangeName)
        
        
        last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
        print("Symbol Last Price: ",last_price)
        price  = float(last_price)
        
        if smart_order_type == 'market':  
            orderDetails = {
                "symbol": symbol,
                "side": "Sell",
                "type": 'LIMIT',
                "quantity": quantity,
                "price": price, 
                "reduceOnly": True,
                "timeInForce": "GTC"
            }
            print("__________________here1________________________")
            resp123l = OrderOperations.CreateBinanceFuturesOrderSmartBuy(userId, exchangeName, orderDetails)
            print(resp123l)
            print("__________________here2________________________")
            if resp123l["status"] == 'fail':
                print("we add a notification return to the bot")
                # return {"message":"Fail", "result": str(resp123l["result"])}, 500
            print(" ^^^^^^^^^^^^^^^^^^^^^^^^^")
            if resp123l["status"] == 'ok' or resp123l["status"] == 'Ok' or resp123l["status"] == 'OK':
                # last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                # print(last_price)
                # price = last_price
                exchange_order_id1 = resp123l["result"]["orderId"]
                print("exchange_order_id LIMIT", exchange_order_id1)
            
        
        
        if smart_order_type == 'limit':
            orderDetails_Mode = {
            "symbol": symbol,
            "orderId": exchange_order_id,
            }
            # closing limit order
            
            resp12 = OrderOperations.cancelBinanceFuturesOrderSmartBuy(userId, exchangeName, orderDetails_Mode)
            logger.info("The response is: \n",resp12)
            logger.info("The response status is: \n", resp12["status"])

            logger.info(" ^^^^^^^^^^^CLOSING AN OPEN POSITION^^^^^^^^^^^^^^")
            if resp12["status"] == 'ok' or resp12["status"] == 'Ok' or resp12["status"] == 'OK':
                last_price = OrderOperations.getSymbolLastPrice1(userId, exchangeName, symbol)
                print(last_price)
        
        
        
        print("Exchange id: ",exchange_order_id, "User ID: ", userId)
        
        # Will print info when either exchange_order_id or userId is not passed
        if not exchange_order_id or not userId:
            logger.exception("Exchange order id or user id not passed")
            
            if not exchange_order_id and userId:
                logger.info("Exchange order id is not passed, User id is :", userId)
                
            elif not userId and exchange_order_id:
                logger.info("User id is not passed, Exchange order id is :", exchange_order_id)
                
            else:
                logger.exception("Neither Exchange order id and user id are passed")
        
        
        try:
            
            print("__________________Change_Status______________________")
            # Query the record based on user_id and exchange_order_id
            order = SmartOrdersModel.query.filter_by(userid=userId, exchange_order_id=str(exchange_order_id)).first()

            if order:
                # Update the status to 'filled'
                order.status = 'filled'
                db.session.commit()
                
                resp = {
                    "status": "OK",
                    "result": "Order status updated successfully to 'filled.'",           
                }
                
                return resp, 200
            
            else:
                
                logger.error("_________Order not found__________")
                resp = {
                    "status": "NOT FOUND",
                    "result": "Order not found.",           
                }
                
                return resp, 404
            
            
        except Exception as e:
            return {
                "status": "400",
                "message": str(e)
            }   
        
        
# filtered orders
# @api.route('/all/filled/orders')
# class All_Filled_Orders(Resource):
#     #all orders saved in the database
#     # @api.doc(params={'userId':'user id'})
#     @login_required
#     def get(self, user):
#         global test_
#         @socketio.on("message")
#         def connected():
#             """event listener when client connects to the server"""
#             print(user.id)
#             print("client has connected")
#             emit("message",{"data":f"user of id: {user.id} is connected"}, broadcast= True)
#         # socketio.emit('testing1', {'data': 'This is a test'}, broadcast=True)  
#         userId = user.id
        
#         try:
#             page = int(request.args.get('page'))
#         except TypeError:
#             return {
#                 "status": 200,
#                 "message": "error page must be an integer"
#             }
            
#         data =  OrderOperations.filledBinancePlacedOrders(userId)
#         test_ = "Hello"
#         print(f"__________GLOAL_VARIABLE_CHANGE_TO_{test_}________________")
       
        
#         print("__________BINANCE_ORDERS_DATA________________")
#         print(data)
        

#         result = data[0]['result']

#         if len(result) == 0:
#             return {
#                 "status": 200,
#                 "result": result
#             }

#         # current page
#         # orders per page
#         per_page = 5
#         # total number of orders
#         total_number = len(result)
#         # total number of pages
#         total_pages = math.ceil(total_number / per_page)

#         # check validity of the page
#         if page > total_pages:
#             return {
#                 "status": 200,
#                 "message": "page number out of range"
#             }

#         # start index and end index for list slicing
#         # check if is page 1
#         if page == 1:
#             start_index = 0
#         else:
#             start_index = ((page - 1) * per_page) 

#         # check end index
#         end_index = start_index + (per_page - 1)

#         # initialize page data starting with none
#         data_in_page = None

#         # check if end index is not less than total
#         if not ((end_index) < total_number):
#             end_index = total_number - 1
        
#         end_index += 1
#         data_in_page = result[start_index:end_index]

#         print(f"start index {start_index} endindex {end_index}")
#         final_data = {
#             "status": 200,
#             "total_pages": total_pages,
#             "current_page": page,
#             "result" : data_in_page
#         }

#         return final_data
    
@api.route('/all/open/market/orders')
class All_Open_Market_Orders(Resource):
    #all orders saved in the database
    # @api.doc(params={'userId':'user id'})
    @login_required
    def get(self, user):
        userId = user.id
        
        try:
            page = int(request.args.get('page'))
        except TypeError:
            return {
                "status": 200,
                "message": "error page must be an integer"
            }
            
        type = 'market'
            
        data =  OrderOperations.SmartOrderTypeBinancePlacedOrders(userId, type)
        
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
    
@api.route('/all/open/limit/orders')
class All_Open_Limit_Orders(Resource):
    #all orders saved in the database
    # @api.doc(params={'userId':'user id'})
    @login_required
    def get(self, user):
        userId = user.id
        
        try:
            page = int(request.args.get('page'))
        except TypeError:
            return {
                "status": 200,
                "message": "error page must be an integer"
            }
            
        type = 'limit'
        data =  OrderOperations.SmartOrderTypeBinancePlacedOrders(userId, type)
        
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