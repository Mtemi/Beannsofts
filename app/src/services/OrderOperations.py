from flask.json import jsonify
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src.models import OrdersModel, ExchangeModel, orders, SmartOrdersModel
from app.src import db
from time import gmtime, strftime
import json
from app.src.utils import logging
from datetime import date, datetime
import json

from app.src.services.binanceoperations import BinanceOps
logger = logging.GetLogger(__name__)

def saveOrderToDB(orderDetails):
    """
        This method save an order to the database

        :param orderdetails 
            -of type dictionary
        :return None
    """
    order = OrdersModel(**orderDetails)

    db.session.add(order)
    db.session.commit()
    
def getOrdersFormater(orders):
    result = []
                
    for i in range(len(orders)):
        order = {
            "order_id": orders[i].id,
            "binance_order_id":orders[i].binance_order_id, 
            "symbol":orders[i].symbol,
            "transactTime":orders[i].transactTime, 
            "price":orders[i].price,
            "origQty":orders[i].origQty, 
            "executedQty":orders[i].executedQty,
            "cummulativeQuoteQty":orders[i].cummulativeQuoteQty, 
            "status":orders[i].status,
            "timeInForce":orders[i].timeInForce, 
            "type":orders[i].type,
            "side":orders[i].side,
            "fills":orders[i].fills,
            "created_on":str(orders[i].created_on),
            "bot_id": orders[i].bot_id
        }
        result.append(order)
    resp = {
            "status":"ok",
            "result": result
        }
            
    return resp

def queryOrderData(user):
    orders = db.session.query(OrdersModel).filter(OrdersModel.user_id == user).all()
    db.session.commit()
    if orders is not None:
        resp = getOrdersFormaterCSV(orders)
        return resp
    else:
        return []

def getAllUserOrders(user):
    """
        This method queries the database for a list of users placed orders

        :param userid
        :return None
            -If the deos no exist in the database
        :return List
            -If the Id exist.The list contains all the bot details.
    """
    try:
        orders = db.session.query(OrdersModel).filter(OrdersModel.user_id == user).all()
        db.session.commit()
        if orders is not None:
            resp = getOrdersFormater(orders)
            logger.info("Orders Found")
            return resp, 200
        else:
            resp = {
                "status": "ok",
                "result": [],
                "message": "no orders found"            
            }
            logger.info("No Orders Found")
            return resp, 200
    except Exception as e:
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured"            
        }
        return resp, 500

def getUserOrdersBySymbol(user, symbol):
    try:
        orders = db.session.query(OrdersModel).filter(OrdersModel.user_id == user, OrdersModel.symbol == symbol).all()
        if orders is not None:
            resp = getOrdersFormater(orders)
            logger.info("Orders Found")
            return resp, 200
        else:
            resp = {
                "status": "ok",
                "result": [],
                "message": "no orders found with symbol"            
            }
            logger.info("No Orders Found")
            return resp, 200
    except Exception as e:
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured"            
        }
        return resp, 500

def getUserOrdersByDate(self, user, startDate, endDate):
    try:
        orders = db.session.query(OrdersModel).filter(OrdersModel.user_id == user, 
                (OrdersModel.created_on <= startDate, OrdersModel.created_on >= endDate))

    except Exception as e:
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured"            
        }
        return resp, 500

def getOrdersFormaterCSV(orders):
    result = []
                
    for i in range(len(orders)):
        order = [
            orders[i].id,
            orders[i].binance_order_id, 
            orders[i].symbol,
            orders[i].transactTime, 
            orders[i].price,
            orders[i].origQty, 
            orders[i].executedQty,
            orders[i].cummulativeQuoteQty, 
            orders[i].status,
            orders[i].timeInForce, 
            orders[i].type,
            orders[i].side,
            orders[i].fills,
            str(orders[i].created_on),
            orders[i].bot_id
        ]
        result.append(order)
    
            
    return result

def fetchBinanceKeys(user, exchange_name):
    return db.session.query(ExchangeModel).filter(ExchangeModel.user_id == user, ExchangeModel.exchange_name == exchange_name).first()

def ListBinanceOpenPositions(user, exchange_name):
    ApiData = fetchBinanceKeys(user, exchange_name)
    key = ApiData.key
    secret = ApiData.secret
    try:
        BinaceClient = BinanceOps(api_key=key, api_secret=secret, trade_symbol="BTCUSDT")
        openOrders = BinaceClient.checkAllOPenOrders()
        if openOrders != False:
            resp = {
                "status": "OK",
                "result": openOrders,           
            }
            return resp, 200
        else:
            resp = {
                "status": "OK",
                "result": [],           
            }
            return resp, 200
    except Exception as e:
        logger.exception("Position Exception", e)
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters"            
        }
        return resp, 500

def ListAllBinanceOrders(user, exchange_name, symbol):
    ApiData = fetchBinanceKeys(user, exchange_name)
    key = ApiData.key
    secret = ApiData.secret

    try:
        BinaceClient = BinanceOps(api_key=key, api_secret=secret, trade_symbol=symbol)
        openOrders = BinaceClient.checkAllOrders()
        if openOrders != False:
            resp = {
                "status": "OK",
                "result": openOrders,           
            }
            return resp, 200
        else:
            resp = {
                "status": "OK",
                "result": [],           
            }
            return resp, 200
    except Exception as e:
        logger.exception("Position Exception", e)
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters"            
        }
        return resp, 500

def CreateBinanceSpotOrder(user, exchange_name, orderDetails):
    ApiData = fetchBinanceKeys(user, exchange_name)
    key = ApiData.key
    secret = ApiData.secret

    print("key, secret", key, secret)

    try:
        BinanceSpotClient = BinanceOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
        newOrder = BinanceSpotClient.sendOrder(orderDetails)

        if newOrder != False:
            resp = {
                "status": "OK",
                "result": newOrder,           
            }
            return resp, 200
        else:
            resp = {
                "status": "OK",
                "result": [],           
            }
            return resp, 200

    except Exception as e:
        logger.exception("Create Order Exception")
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters",
            "status_code":400            
        }
        return resp, 200

# TODO Create an env file with default API Keys and Secret.
def getSymbolLastPrice1(user, exchange_name, symbol):
    # key = 'yphGuZdDbWA8xicAwZnRjVsVmN7Ofad5Vt5K8x3LrlxU2VepDa48jZXOamvekCYJ'
    # secret = 'I6hNQzpMS4pLb4cZlTc4P2n1oUVWHMe8rV5EVaFUdBDAosxWV0a1rFP2YYN27yzL'
    ApiData = fetchBinanceKeys(user, exchange_name)
    key = ApiData.key
    secret = ApiData.secret
    BinanceSpotClient = BinanceOps(api_key=key, api_secret=secret, trade_symbol=symbol)
    lastPrice = BinanceSpotClient.lastPrice
    return lastPrice



def cancelBinanceFuturesOrderSmartBuy(user, exchange_name, orderDetails):
    ApiData = fetchBinanceKeys(user, exchange_name)
    print('ApiData')
    print(ApiData)
    print("exchange_name")
    print(exchange_name)
    key = ApiData.key
    secret = ApiData.secret

    try:
        BinanceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
        cancelledOrder = BinanceFuturesClient.cancelOrder(orderDetails)
        print(cancelledOrder)

        if cancelledOrder != False:
            resp = {
                "status": "OK",
                "result": cancelledOrder,  
                "status_code" :200        
            }
            return resp
        else:
            resp = {
                "status": "OK",
                "result": [], 
                "status_code":200          
            }
            return resp

    except Exception as e:
        logger.exception("Create Order Exception")
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters",
            "status_code":400           
        }
        return resp


def CreateBinanceFuturesOrderSmartBuy(user, exchange_name, orderDetails):
    ApiData = fetchBinanceKeys(user, exchange_name)
    print('ApiData')
    print(ApiData)
    print("exchange_name")
    print(exchange_name)
    key = ApiData.key
    secret = ApiData.secret

    try:
        BinanceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
        newOrder = BinanceFuturesClient.sendOrder(orderDetails)
        print(newOrder)

        if newOrder != False:
            resp = {
                "status": "OK",
                "result": newOrder,  
                "status_code" :200        
            }
            return resp
        else:
            resp = {
                "status": "OK",
                "result": [], 
                "status_code":200          
            }
            return resp

    except Exception as e:
        logger.exception("Create Order Exception")
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters",
            "status_code":400           
        }
        return resp

def CreateBinanceFuturesOrder(user, exchange_name, orderDetails):
    ApiData = fetchBinanceKeys(user, exchange_name)
    print('ApiData')
    print(ApiData)
    print("exchange_name")
    print(exchange_name)
    key = ApiData.key
    secret = ApiData.secret

    try:
        BinanceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
        newOrder = BinanceFuturesClient.sendOrder(orderDetails)

        if newOrder != False:
            resp = {
                "status": "OK",
                "result": newOrder,  
                "status_code" :200        
            }
            return resp, 200
        else:
            resp = {
                "status": "OK",
                "result": [], 
                "status_code":200          
            }
            return resp, 200

    except Exception as e:
        logger.exception("Create Order Exception")
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters",
            "status_code":400           
        }
        return resp, 200

def ListBinancePositions(user, exchange_name):
    ApiData = fetchBinanceKeys(user, exchange_name)
    if ApiData:
        key = ApiData.key
        secret = ApiData.secret
        exchange_type = ApiData.exchange_type
        if exchange_type == "binance":
            try:
                BinanceClient = BinanceOps(api_key=key, api_secret=secret, trade_symbol="BTCUSDT")
                openOrders = BinanceClient.checkAllOPenOrders()
                if openOrders != False:
                    resp = {
                        "status": "OK",
                        "result": openOrders,           
                    }
                    return resp, 200
                else:
                    resp = {
                        "status": "OK",
                        "result": [],           
                    }
                    return resp, 200
            except Exception as e:
                logger.exception("Position Exception", e)
                resp = {
                    "status": "fail",
                    "result": str(e),
                    "message": "error occured. Check parameters"            
                }
                return resp, 400
            
        elif exchange_type == "binance-futures":
            try:
                BinaceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol="BTCUSDT")
                openOrders = BinaceFuturesClient.checkAllOPenOrders()
                if openOrders != False:
                    resp = {
                        "status": "OK",
                        "result": openOrders,           
                    }
                    return resp, 200
                else:
                    resp = {
                        "status": "OK",
                        "result": [],           
                    }
                    return resp, 200
            except Exception as e:
                logger.exception("Position Exception", e)
                resp = {
                    "status": "fail",
                    "result": str(e),
                    "message": "error occured. Check parameters"            
                }
                return resp, 400
    else:
        resp = {
            "status": "ok",
            "result": [],
            "message": "no positions"            
        }
        return resp, 400

def allBinancePlacedOrders(user):
    # from sqlalchemy.ext.declarative import DeclarativeMeta

    # TODO #FIXME implement this serializer method in future to see if it optimizes
    # class AlchemyEncoder(json.JSONEncoder):

    #     def default(self, obj):
    #         if isinstance(obj.__class__, DeclarativeMeta):
    #             # an SQLAlchemy class
    #             fields = {}
    #             for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
    #                 data = obj.__getattribute__(field)
    #                 try:
    #                     json.dumps(data) # this will fail on non-encodable values, like other classes
    #                     fields[field] = data
    #                 except TypeError:
    #                     fields[field] = None
    #             # a json-encodable dict
    #             return fields

    #         return json.JSONEncoder.default(self, obj)

    try:
        orders = db.session.query(SmartOrdersModel).filter(SmartOrdersModel.userid == user).all()
        db.session.commit()
        
        print(f"Orders : {orders}")
        print(f"Orders leverage : {orders[0].leverage_type}")

        result = []
        
        def json_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError(f'Type {type(obj)} is not serializable')
        
        now = datetime.now()
        
        for i in range(len(orders)):
            order = {
                "id":orders[i].id,
                "smart_order_type":orders[i].smart_order_type,
                "exchange_id":orders[i].exchange_id,
                "exchange_order_id":orders[i].exchange_order_id,
                "sl_steps":orders[i].sl_steps,
                "userid":orders[i].userid,
                "task_id":orders[i].task_id,
                "symbol":orders[i].symbol,
                "side":orders[i].side,
                "amt":orders[i].amt,
                "price":orders[i].price,
                "leverage_type":orders[i].leverage_type,
                "leverage_value":orders[i].leverage_value,
                "order_details_json":orders[i].order_details_json,
                # "created_on":orders[i].created_on,
                # "modified_on":orders[i].modified_on,
                "created_on":json.dumps(orders[i].created_on, default=json_serializer),
                # "modified_on":json.dumps(orders[i].modified_on, default=json_serializer),
                "status":orders[i].status,
                # "executed_on":json.dumps(orders[i].executed_on, default=json_serializer),
                "change_reason":orders[i].change_reason,
                
            }
            result.append(order)
            # openOrders = json.dumps(orders, cls=AlchemyEncoder, separators=None)

        if result != False:
            resp = {
                "status": "OK",
                "result": result,           
            }
            return resp, 200
        else:
            resp = {
                "status": "OK",
                "result": [],           
            }
            return resp, 200
    except Exception as e:
        logger.exception("Position Exception", e)
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters"            
        }
        return resp, 400

def getAssetBalance(userId, exchangeName, symbol):
    ApiData = fetchBinanceKeys(userId, exchangeName)
    print("---symbol----",symbol)
    if ApiData:
        key = ApiData.key
        secret = ApiData.secret
        exchange_type = ApiData.exchange_type
        if exchange_type == "binance":
            try:
                BinanceClient = BinanceOps(api_key=key, api_secret=secret, trade_symbol=symbol)
                param = {
                    "asset":symbol
                }
                balances = BinanceClient.checkWalletBalance(param)
                resp = {
                    "status": "OK",
                    "result": balances,           
                }
                return resp, 200
            except Exception as e:
                logger.exception("asset balance Exception", e)
                resp = {
                    "status": "error",
                    "result": 0,
                    "message": "no asset balances"            
                }
                return resp, 200
        elif exchange_type == "binance-futures":
            try:
                BinaceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=symbol)
                param = {
                    "asset":symbol
                }
                balances = BinaceFuturesClient.checkWalletBalance(param)
                print(f"{param}--- {balances}")

                resp = {
                    "status": "OK",
                    "result": balances,           
                }
                return resp, 200
            except Exception as e:
                logger.exception("asset balance Exception", e)
                resp = {
                    "status": "error",
                    "result": 0,
                    "message": "no asset balances"            
                }
                return resp, 200
    else:
        resp = {
            "status": "ok",
            "result": 0,
            "message": "no assets"            
        }
        return resp, 200

def fetchApiKeysBinance(exchangeId):
    try:
        ApiData =  db.session.query(ExchangeModel).filter_by(id = exchangeId).first()
        db.session.commit()
        if ApiData:
            return ApiData
        else:
            return False
    except Exception as e:
        logger.exception("fetchBinanceKeys Exception", e)
        return False

def createBinanceTerminalSpotOrder(userId, exchangeId, orderDetails):
    ApiData = fetchApiKeysBinance(exchangeId)
    if ApiData:
        key = ApiData.key
        secret = ApiData.secret

        try:
            client = BinanceOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])

            newOrder = client.sendOrder(orderDetails)

            if newOrder != False:
                resp = {
                    "status": "OK",
                    "result": newOrder,           
                }
                return resp, 200
            else:
                resp = {
                    "status": "OK",
                    "result": [],           
                }
                return resp, 200

        except Exception as e:
            logger.exception(f"Create Order Exception {e}")
            resp = {
                "status": "fail",
                "result": str(e),
                "message": "error occured. Check parameters"            
            }
            return resp, 500
    else:
        resp = {
            "status": "fail",
            "result": [],
            "message": "invalid api keys"
        }
        return resp, 200

def createBinanceTerminalFuturesOrders(userId, exchangeId, orderDetails):
    ApiData = fetchApiKeysBinance(exchangeId)
    if ApiData:
        key = ApiData.key
        secret = ApiData.secret

        try:
            client = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])

            newOrder = client.sendOrder(orderDetails)

            if newOrder != False:
                resp = {
                    "status": "OK",
                    "result": newOrder,           
                }
                return resp, 200
            else:
                resp = {
                    "status": "OK",
                    "result": [],           
                }
                return resp, 200

        except Exception as e:
            logger.exception(f"Create Order Exception {e}")
            resp = {
                "status": "fail",
                "result": str(e),
                "message": "error occured. Check parameters"            
            }
            return resp, 500
    else:
        resp = {
            "status": "fail",
            "result": [],
            "message": "invalid api keys"
        }
        return resp, 200


def set_Leverage(user, exchange_name, orderDetails):
    ApiData = fetchBinanceKeys(user, exchange_name)
    print('ApiData')
    print(ApiData)
    print("exchange_name")
    print(exchange_name)
    key = ApiData.key
    secret = ApiData.secret

    try:
        BinanceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
        newOrder = BinanceFuturesClient.setLeverage(orderDetails)
        print(newOrder)

        if newOrder != False:
            resp = {
                "status": "OK",
                "result": newOrder,  
                "status_code" :200        
            }
            return resp
        else:
            resp = {
                "status": "OK",
                "result": [], 
                "status_code":200          
            }
            return resp

    except Exception as e:
        logger.exception("Create Order Exception")
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters",
            "status_code":400           
        }
        return resp
    

def change_PositionMode(user, exchange_name, orderDetails):
    ApiData = fetchBinanceKeys(user, exchange_name)
    print('ApiData')
    print(ApiData)
    print("exchange_name")
    print(exchange_name)
    key = ApiData.key
    secret = ApiData.secret

    try:
        BinanceFuturesClient = BinanceFuturesOps(api_key=key, api_secret=secret, trade_symbol=orderDetails['symbol'])
        newOrder = BinanceFuturesClient.changePositionMode(orderDetails)
        print(newOrder)

        if newOrder != False:
            resp = {
                "status": "OK",
                "result": newOrder,  
                "status_code" :200        
            }
            return resp
        else:
            resp = {
                "status": "OK",
                "result": [], 
                "status_code":200          
            }
            return resp

    except Exception as e:
        logger.exception("Create Order Exception")
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured. Check parameters",
            "status_code":400           
        }
        return resp