from app.src.models.exchange import ExchangeEnum
from app.src.services.SubscriptionOperations import subscriptionType, filterPlanActions
from flask_restx import Resource, abort
from . import login_required
from flask import request
import datetime
from time import gmtime, strftime
from app.src.services import BinanceOps, ExchangeOperations,BinanceFuturesOps
from app.src.services import BotOperations
from app.src.models import ExchangeModel, ExchangeEnum
from app.src.models import StatusEnum
from app.src import db

from ..utils.dto import ExchangeDto

from app.src.services.Notifications.Notification import Notification
from app.src.utils.binance.clientOriginal import Client as BinanceClient
import json

api = ExchangeDto.api
# dtos 
exchange = ExchangeDto.exchange
exchange_balance_dto = ExchangeDto.exchange_balance_dto
delete_exchange_dto = ExchangeDto.delete_exchange_dto

# to be moved to another folder
# edit exchange helper
def get_exchange_by_name(exch_name):
    exchange = ExchangeModel.query.filter_by(exchange_name=exch_name).first()
    return exchange


@api.route('/add')
class AddExchange(Resource):
    @api.doc('create a new exchange')
    @api.expect(exchange, validate=True)
    @login_required
    def post(self, user):
        
        exch_name = request.json['exch_name']
        api_key = request.json['api_key']
        api_secret = request.json['api_secret']
        exchange = request.json['exchange'].lower()
        userId = user.id
        
        
        print(f"exchange name: {exch_name}, api_key: {api_key}, api_secret: {api_secret}, exchange: {exchange}, userId: {userId}")

        # check if exchange exists from exchange name
        exchange_exists = get_exchange_by_name(exch_name)
        if  exchange_exists:
            return {
                "status": 400 ,
                "message": "exchange name already exists chose another name"
            }, 400


        # subscription = subscriptionType(userId)
        # print("The subscriptions, {}".format(subscription))

        # if subscription:
        # print(subscription.plan_id)
        # planAction = filterPlanActions(subscription.plan_id)
        # print("PLan Action {}".format(planAction))
        
        totalExchanges = db.session.query(ExchangeModel).filter(ExchangeModel.user_id == userId).count()
        print("Total Exchanges, {}".format(totalExchanges))

        # if totalExchanges >= planAction['exchanges'] and planAction['exchanges'] != 0:
        #     return {"message":"Request Denied, Upgrade your subscription", "status":403}, 200
        # else:
        #verify the api_key and api_secret for binance
        if exchange == "binance":
            binance_service = BinanceOps(api_key, api_secret, trade_symbol="BTCUSDT")
            

            keys = db.session.query(ExchangeModel).filter(ExchangeModel.key == api_key).first()
            if keys == None:
                print("Keys None")
                if binance_service.authenticateKeys() == True:
                    print("Auth Keys")
                    exchange = ExchangeModel(exchange_name = exch_name, key = api_key, secret =api_secret, user_id = userId, modified_on = None, exchange_type = ExchangeEnum.SPOT.value)
                    db.session.add(exchange)
                    db.session.commit()

                    return {"message":"API data autenticated successifully", "result": {
                        "exchange_id": exchange.id,
                        "exchangeName": exchange.exchange_name,
                    }, "status":200}, 200
                else:
                    # still return a json from the services
                    return binance_service.authenticateKeys(), 200
            else:
                return {"message":"Duplicate Keys Please enter new keys", "status":200}, 200
        elif exchange == "binance-futures":
            # add new exchange here
            binance_service = BinanceFuturesOps(api_key, api_secret, trade_symbol="BTCUSDT")

            keys = db.session.query(ExchangeModel).filter(ExchangeModel.key == api_key).first()
            if keys == None:
                print("Keys None")
                if binance_service.authenticateKeys() == True:
                    print("Auth Keys")
                    exchange = ExchangeModel(exchange_name = exch_name, key = api_key, secret =api_secret, user_id = userId, modified_on = None, exchange_type = ExchangeEnum.FUTURES.value)
                    db.session.add(exchange)
                    db.session.commit()

                    return {"message":"API data autenticated successifully", "result": {
                        "exchange_id": exchange.id,
                        "exchangeName": exchange.exchange_name,
                    }, "status":200}, 200
                else:
                    # still return a json from the services
                    return binance_service.authenticateKeys(), 200
            else:
                return {"message":"Duplicate Keys Please enter new keys", "status":200}, 200
        else:
            # add new exchange here
            pass
        
@api.route('/edit')
class EditExchange(Resource):
    @api.doc('edit an exchange')
    @api.expect(exchange, validate=True)
    @login_required
    def post(self, user):

        exch_name = request.json['exch_name']
        api_key = request.json['api_key']
        api_secret = request.json['api_secret']
        exchange = request.json['exchange'].lower()
        userId = user.id


        #verify the api_key and api_secret for binance

        # dry to be refactored
        # check if exchange exists from exchange name
        exchange_exists = get_exchange_by_name(exch_name)
        if not exchange_exists:
            return {
                "status": 404,
                "message": "exchange not found"
            }

        # verify the api_key and api_secret for binance
        if exchange == "binance":
            binance_service = BinanceOps(api_key, api_secret, trade_symbol="BTCUSDT")

            if binance_service.authenticateKeys() == True: 

                db.session.query(ExchangeModel).filter(ExchangeModel.user_id ==userId, ExchangeModel.exchange_name == exch_name).update({ExchangeModel.key:api_key, ExchangeModel.secret:api_secret, ExchangeModel.modified_on:datetime.datetime.now(), ExchangeModel.exchange_type: ExchangeEnum.SPOT.value})
                db.session.commit()

                return {"message":"API data modified successifully","result": {
                                "exchangeName": exch_name,
                                "api_key": api_key,
                                "api_secret":api_secret,
                                "exchange_type":exchange
                            },"status":200}
            else:
                # still return a json from the services
                return binance_service.authenticateKeys()
        elif exchange == "binance-futures":
            # add new exchange here
            binance_service = BinanceFuturesOps(api_key, api_secret, trade_symbol="BTCUSDT")

            if binance_service.authenticateKeys() == True: 

                db.session.query(ExchangeModel).filter(ExchangeModel.user_id ==userId, ExchangeModel.exchange_name == exch_name).update({ExchangeModel.key:api_key, ExchangeModel.secret:api_secret, ExchangeModel.modified_on:datetime.datetime.now(), ExchangeModel.exchange_type: ExchangeEnum.FUTURES.value})
                db.session.commit()

                return {"message":"API data modified successifully","result": {
                                "exchangeName": exch_name,
                                "api_key": api_key,
                                "api_secret":api_secret,
                                "exchange_type":exchange.lower()
                            },"status":200}
            else:
                # still return a json from the services
                return binance_service.authenticateKeys()
            pass
        else:
            # add new exchange here
            pass


# @api.route('/delete1')
# class Add_Exchange(Resource):
#     @api.doc('create a new exchange')
#     @api.expect(exchange)
#     @login_required
#     def delete(self, user):
        
#         exch_name = request.json['exch_name']
#         api_key = request.json['api_key']
#         api_secret = request.json['api_secret']
#         exchange = request.json['exchange'].lower()
#         userId = user.id
        
        
#         print(f"exchange name: {exch_name}, api_key: {api_key}, api_secret: {api_secret}, exchange: {exchange}, userId: {userId}")

#         # check if exchange exists from exchange name
#         exchange_exists = get_exchange_by_name(exch_name)
#         if  exchange_exists:
#             return {
#                 "status": 400 ,
#                 "message": "exchange name already exists chose another name"
#             }, 400


#         # subscription = subscriptionType(userId)
#         # print("The subscriptions, {}".format(subscription))

#         # if subscription:
#         # print(subscription.plan_id)
#         # planAction = filterPlanActions(subscription.plan_id)
#         # print("PLan Action {}".format(planAction))
        
#         totalExchanges = db.session.query(ExchangeModel).filter(ExchangeModel.user_id == userId).count()
#         print("Total Exchanges, {}".format(totalExchanges))

#         # if totalExchanges >= planAction['exchanges'] and planAction['exchanges'] != 0:
#         #     return {"message":"Request Denied, Upgrade your subscription", "status":403}, 200
#         # else:
#         #verify the api_key and api_secret for binance
#         if exchange == "binance":
#             binance_service = BinanceOps(api_key, api_secret, trade_symbol="BTCUSDT")
            

#             keys = db.session.query(ExchangeModel).filter(ExchangeModel.key == api_key).first()
#             if keys == None:
#                 print("Keys None")
#                 if binance_service.authenticateKeys() == True:
#                     print("Auth Keys")
#                     exchange = ExchangeModel(exchange_name = exch_name, key = api_key, secret =api_secret, user_id = userId, modified_on = None, exchange_type = ExchangeEnum.SPOT.value)
#                     db.session.add(exchange)
#                     db.session.commit()

#                     return {"message":"API data autenticated successifully", "result": {
#                         "exchange_id": exchange.id,
#                         "exchangeName": exchange.exchange_name,
#                     }, "status":200}, 200
#                 else:
#                     # still return a json from the services
#                     return binance_service.authenticateKeys(), 200
#             else:
#                 return {"message":"Duplicate Keys Please enter new keys", "status":200}, 200
#         elif exchange == "binance-futures":
#             # add new exchange here
#             binance_service = BinanceFuturesOps(api_key, api_secret, trade_symbol="BTCUSDT")

#             keys = db.session.query(ExchangeModel).filter(ExchangeModel.key == api_key).first()
#             if keys == None:
#                 print("Keys None")
#                 if binance_service.authenticateKeys() == True:
#                     print("Auth Keys")
#                     exchange = ExchangeModel(exchange_name = exch_name, key = api_key, secret =api_secret, user_id = userId, modified_on = None, exchange_type = ExchangeEnum.FUTURES.value)
#                     db.session.add(exchange)
#                     db.session.commit()

#                     return {"message":"API data autenticated successifully", "result": {
#                         "exchange_id": exchange.id,
#                         "exchangeName": exchange.exchange_name,
#                     }, "status":200}, 200
#                 else:
#                     # still return a json from the services
#                     return binance_service.authenticateKeys(), 200
#             else:
#                 return {"message":"Duplicate Keys Please enter new keys", "status":200}, 200
#         else:
#             # add new exchange here
#             pass


@api.route('/delete')
class DeleteExchange(Resource):
    @api.doc('(Modified) delete an exchange, requires exchange_name and exchange')
    # @api.expect(delete_exchange_dto, validate=True)
    @login_required
    def delete(self, user):
        # exchange_name = request.json['exchange_name']
        # exchange = request.json['exchange']
        # userId = user.id
        
        exchange_name = request.args.get('exchange_name')
        exchange = request.args.get('exchange')
        
        print(exchange, exchange_name)
        # print(f"exchange name: {exchange_name}, exchange: {exchange}, user_id: {userId}")   

        exchange = ExchangeModel.query.filter_by(user_id=user.id, exchange_name=exchange_name).first()

        if exchange:
            if exchange.status == StatusEnum.DELETED.value:
                return {
                "status": 404,
                "message": "Order status already set to deleted"
            }, 404
               
            else:
                exchange.status = StatusEnum.DELETED.value
                db.session.commit()
                return {
                "status": 200,
                "message": "Exchange deleted successfully(status set to deleted)"
            }, 200
             
        
        else:
            return {
                "status": 404,
                "message": "Exchange not found"
            }, 404
          
        



@api.route('/list')
class ListExchanges(Resource):
    @api.doc('list all user exchanges', params={'userId':'User ID'})
    @login_required
    def get(self, user):
        userId = user.id
        print("user id", userId)
        return ExchangeOperations.getAllExchanges(userId)

# add get exchanges by user 
def get_all_user_exchanges(user):
    exchanges =  ExchangeModel.query.filter_by(user_id=user.id).all()
    return exchanges

@api.route('/assets/balances')
class ListAssetBalances(Resource):
    @api.doc('get all the asset balances')
    @api.expect(exchange_balance_dto, validate=True)
    @login_required
    def post(self, user):
        exch_name = request.json['exch_name']
        # check if exchange exists before proceed
        exchange = get_exchange_by_name(exch_name)
        if not exchange:
            return {
                "status": 404,
                "message": "exchange not found"
            }, 404
        
    
        print(exchange.exchange_type)
        if exchange.exchange_type.lower() == "binance":
            try:
                binanceClient = BinanceClient(
                    api_key=exchange.key, api_secret=exchange.secret)
                account_info = binanceClient.get_account()
                future_account_info = binanceClient.futures_account()

                spotAssetBalances = account_info["balances"]
                futuresAssetBalances = future_account_info["assets"]


                spotBalances = ExchangeOperations.spotAssetBalancesFilter(
                    spotAssetBalances)
                # futureBalances = ExchangeOperations.futuresAssetBalancesFilter(
                #     futuresAssetBalances)

                return {
                    "status": 200,
                    "data": {
                        "exchangeName": exchange.exchange_name,
                        "exchangeType": exchange.exchange_type,
                        "exchangeId": exchange.id,
                        "spot": spotBalances,
                        # "futures": futureBalances
                        },
                    "message": "sucess"
                }

            except Exception as e:
                return {
                    "status": 400,
                    "message": "fail",
                    "error": str(e)
                }
            
        elif exchange.exchange_type.lower() == "other exchange":
            # add other exchange support here
            pass

        else:
            return {
                "status": 400,
                "message": "exchange type not supported"
            }, 400

