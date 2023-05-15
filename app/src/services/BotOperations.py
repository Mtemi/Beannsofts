from flask import jsonify
from app.src.models import BotModel, ExchangeModel
from app.src.utils.helpers import serializerDB
from .binanceoperations import BinanceOps
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src import db
from time import gmtime, strftime
from app.src.models.dcabot import DCABotOrderModel

from app.src.utils import logging
from app.src.services import OrderOperations

logger = logging.GetLogger(__name__)


def queryBotDetail(botId):
    """
        This method queries the database for bot details 

        :param botID
        :return None
            -If the deos no exist in the database
        :return dict
            -If the Id exist.The dictionary contains all the bot details.
    """
    bot = db.session.query(BotModel).filter(BotModel.id == botId).first()
    db.session.commit()
    if bot is not None:
        return bot
    else:
        return None


def queryBotDetailbyName(botName):
    """
        This method queries the database for bot details 
        :param botID
        :return None
            -If the deos no exist in the database
        :return dict
            -If the Id exist.The dictionary contains all the bot details.
    """
    bot = db.session.query(BotModel).filter(
        BotModel.botName == botName).first()
    db.session.commit()
    if bot is not None:
        return bot
    else:
        return None


def queryExchangeDetail(userId):
    """
        This method queries the database for exchange details (api_key and secret key)

        :param userID
        :return None
            -If the deos no exist in the database
        :return dict
            -If the Id exist.The dictionary contains all the bot details.
    """
    apiData = db.session.query(ExchangeModel).filter(
        ExchangeModel.user_id == userId).first()
    if apiData is not None:
        return apiData
    else:
        return None


def createNewBot(user, BotDetail, botName):
    """
        This method creates a new bot to the database. The parameter is a dictionary. 

        :param dict

        :return None
            -If the deos no exist in the database
        :return dict
            -If the Id exist.The dictionary contains all the bot details.
    """
    params = {
        'botName': botName,
        'side': BotDetail.side,
        'orderType': BotDetail.orderType,
        'symbol': BotDetail.symbol,
        'baseSymbol': BotDetail.baseSymbol,
        'tradeAmt': BotDetail.tradeAmt,
        'interval': BotDetail.interval,
        'maxOrderAmt': BotDetail.maxOrderAmt,
        'minOrderAmt': BotDetail.minOrderAmt,
        'price': BotDetail.price,
        'stopLoss': BotDetail.stopLoss,
        'takeProfit': BotDetail.takeProfit,
        'maxTradeCounts': BotDetail.maxTradeCounts,
        'signalType': BotDetail.signalType,
        'botType': BotDetail.botType,
        'botStatus': False,
        'user_id': user.id
    }
    bot = BotModel(**params)
    db.session.add(bot)
    db.session.commit()
    resp = {
        'botId': bot.id,
        'botName': bot.botName,
        'side': bot.side,
        'orderType': bot.orderType,
        'symbol': bot.symbol,
        'baseSymbol': bot.baseSymbol,
        'tradeAmt': bot.tradeAmt,
        'interval': bot.interval,
        'maxOrderAmt': bot.maxOrderAmt,
        'minOrderAmt': bot.minOrderAmt,
        'price': bot.price,
        'stopLoss': bot.stopLoss,
        'takeProfit': bot.takeProfit,
        'maxTradeCounts': bot.maxTradeCounts,
        'signalType': bot.signalType,
        'botStatus': bot.botStatus
    }
    print("copiedBot", bot)
    return resp


def copyBot(self, user, botId, botName):
    """
        This method replicates an existing bot for the user 
    """
    try:
        bot = queryBotDetail(botId)
        print("BOT", bot.botName)

        if bot is not None:
            if bot.botName is botName or queryBotDetailbyName(botName) != None:
                resp = {
                    'status': 'fail',
                    'message': 'DUPLICATE BOT NAME. Find another name'
                }
                logger.info("duplicate bot_name")
                return resp, 400
            else:
                copiedBot = createNewBot(user, bot, botName)
                resp = {
                    'status': 'Ok',
                    'message': 'Bot Copied',
                    'results': copiedBot
                }
                logger.info("Bot copied")
                return resp, 201
        else:
            resp = {
                'status': 'fail',
                'message': 'The bot no longer exist'
            }
            logger.error("Bot deesn't exist")
            return resp, 401
    except Exception as e:
        resp = {
            'status': 'fail',
            'error': str(e),
        }
        logger.exception("Server error, copy Bot", e)
        return resp, 500


def queryAllBots(userId):
    """
        This method queries the database for all bot details for a specific users

        :param user
        :return List 
            -Empty List If the user doe not have any bots
        :return List[dict]
            -LIst of dictionaries, If the Id exist.The dictionary contains all the bot details.
    """
    try:
        bots = db.session.query(BotModel).filter(
            BotModel.user_id == userId).all()
        db.session.commit()
        if bots is not None or []:
            result = []

            for i in range(len(bots)):

                bot = {
                    'botId': bots[i].id,
                    'botName': bots[i].botName,
                    'side': bots[i].side,
                    'orderType': bots[i].orderType,
                    'symbol': bots[i].symbol,
                    'baseSymbol': bots[i].baseSymbol,
                    'tradeAmt': bots[i].tradeAmt,
                    'interval': bots[i].interval,
                    'maxOrderAmt': bots[i].maxOrderAmt,
                    'minOrderAmt': bots[i].minOrderAmt,
                    'price': bots[i].price,
                    'stopLoss': bots[i].stopLoss,
                    'takeProfit': bots[i].takeProfit,
                    'maxTradeCounts': bots[i].maxTradeCounts,
                    'signalType': bots[i].signalType,
                    'botStatus': bots[i].botStatus
                }
                result.append(bot)

            resp = {
                'status': 'Ok',
                'results': result
            }
            return resp, 200
        else:
            resp = {
                'status': 'Ok',
                'message': 'No bots found. User has no bots',
                'results': []
            }
            return resp, 401
    except Exception as e:
        resp = {
            'status': 'fail',
            'error': str(e),
            'message': 'Error occured'
        }
        logger.exception("Get all bots error")
        return resp, 500


def createOrderFromBot(userId, bot_id):
    """
        This method creates order using the data from the bot. 

        :param userId
        :param bot_id

        :return dict
            for sucessiful order return a dictionary from binance.
        :return exception
            for unsuccessful orders

    """

    # get data from the bot
    apiData = queryExchangeDetail(userId)
    botData = queryBotDetail(bot_id)
    api_key = apiData.key
    api_secret = apiData.secret
    exchange_type = apiData.exchange_type

    if exchange_type == "binance":
        botTradeData = {"symbol": botData.symbol, "side": botData.side, "type": botData.orderType.upper(
        ), "quantity": botData.minOrderAmt, "stopLoss": botData.stopLoss, "takeProfit": botData.takeProfit}

        print("printing objects", botTradeData)

        binanceobj = BinanceOps(
            api_key=api_key, api_secret=api_secret, trade_symbol=botTradeData["symbol"])
        try:
            orderRes = binanceobj.sendOrder(botTradeData)
            resp = {
                "status": "Ok",
                "message": "Order created successfully",
                "result": orderRes
            }
            orderID = orderRes['orderId']
            del orderRes['orderId']
            orderRes.update({'binance_order_id': orderID, 'user_id': userId, 'bot_id': bot_id, 'created_on':strftime("%Y-%m-%d %H:%M:%S", gmtime())})
            logger.info("Order created successfully {}".format(orderRes))
            OrderOperations.saveOrderToDB(orderRes)
            logger.info("Order saved to Database")  

            return resp, 201

        except Exception as e:
            resp = {
                "status": "fail",
                "error": str(e),
            }
            logger.exception("Binance error", e)
            return resp, 400

    elif exchange_type == "binance-futures":
        botTradeData = {"symbol": botData.symbol, "side": botData.side, "type": botData.orderType, 
        "quantity": botData.minOrderAmt, "stopLoss": botData.stopLoss, "takeProfit": botData.takeProfit,
            "trailingStop": botData.trailingStop, "callbackRate": botData.callbackRate, "leverage": botData.leverage,
        }

        print("printing objects", botTradeData)

        binanceobj = BinanceFuturesOps(
            api_key=api_key, api_secret=api_secret, trade_symbol=botTradeData["symbol"])
        try:
            orderRes = binanceobj.sendOrder(botTradeData)
            resp = {
                "status": "Ok",
                "message": "Order created successfully",
                "result": orderRes
            }
            orderID = orderRes['orderId']
            del orderRes['orderId']
            orderRes.update({'binance_order_id': orderID, 'user_id': userId, 'bot_id': bot_id, 'created_on':strftime("%Y-%m-%d %H:%M:%S", gmtime())})
            logger.info("Order created successfully {}".format(orderRes))
            OrderOperations.saveOrderToDB(orderRes)
            logger.info("Order saved to Database")  

            return resp, 201

        except Exception as e:
            resp = {
                "status": "fail",
                "error": str(e),
            }
            logger.exception("Binance error", e)
            return resp, 400


def createBotOrderWebhook(botId):
    botData = queryBotDetail(botId)

    apiData = queryExchangeDetail(botData.user_id)

    api_key = apiData.key
    api_secret = apiData.secret
    exchange_type = apiData.exchange_type

    if exchange_type == "binance":
        botTradeData = {"symbol": botData.symbol, "side": botData.side, "type": botData.orderType.upper(
            ), "quantity": botData.minOrderAmt, "stopLoss": botData.stopLoss, "takeProfit": botData.takeProfit}

        binanceobj = BinanceOps(
            api_key=api_key, api_secret=api_secret, trade_symbol=botTradeData["symbol"])

        orderRes = binanceobj.sendOrder(botTradeData)

        orderID = orderRes['orderId']
        del orderRes['orderId']
        orderRes.update({'binance_order_id': orderID, 'user_id': botData.user_id, 'bot_id': botData.id, 'created_on':strftime("%Y-%m-%d %H:%M:%S", gmtime())})
        logger.info("Order created successfully {}".format(orderRes))
        OrderOperations.saveOrderToDB(orderRes)
        logger.info("Order saved to Database")  

        OrderOperations.saveOrderToDB(orderRes)
        logger.info("Bot Order from Webhook saved to Database")

        return orderRes

    elif exchange_type == "binance-futures":
        botTradeData = {"symbol": botData.symbol, "side": botData.side, "type": botData.orderType.upper(), 
            "quantity": botData.minOrderAmt, "stopLoss": botData.stopLoss, "takeProfit": botData.takeProfit,
            "trailingStop": botData.trailingStop, "callbackRate": botData.callbackRate, "leverage": botData.leverage,
        }

        binanceobj = BinanceFuturesOps(
            api_key=api_key, api_secret=api_secret, trade_symbol=botTradeData["symbol"])

        orderRes = binanceobj.sendOrder(botTradeData)

        orderID = orderRes['orderId']
        del orderRes['orderId']
        orderRes.update({'binance_order_id': orderID, 'user_id': botData.user_id, 'bot_id': botData.id, 'created_on':strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'exchange_type': exchange_type})
        logger.info("Order created successfully {}".format(orderRes))
        OrderOperations.saveOrderToDB(orderRes)
        logger.info("Order saved to Database")  

        return orderRes

def queryAllDcaBotOrders(botId):
    try:
        botOrders = db.session.query(DCABotOrderModel).filter_by(bot_id=botId).all()
        logger.info(f"Bot orders for bot Id {botId} fetched successfully {botOrders}")
    except Exception as e:
        logger.exception("Error in querying all bot orders", e)
        resp = {
            "status": "fail",
            "message": "Error in querying all bot orders",
            "result": []
        }
        return resp, 400

    if botOrders:
        serializedOrders = serializerDB(jsonify(botOrders))
        logger.info(f"Bot orders for bot Id {botId} fetched successfully {serializedOrders}")
        resp = {
                "status": "Ok",
                "message": "Orders found successfully",
                "result": serializedOrders
            }
        return resp, 200
    else:
        resp = {
            "status": "Ok",
            "message": "No Orders found successfully",
            "result": []
        }
        return resp, 404
    