from flask_restx import Resource
from app.src.services import ExchangeOperations
from app.src.utils import logging
from app.src.utils.dto import AccountsDto
from app.src import db
from app.src.models.exchange import ExchangeModel
from app.src.utils.binance.clientOriginal import Client as BinanceClient

from flask import request

logger = logging.GetLogger(__name__)

api = AccountsDto.api

@api.route('/balances')
class AccountBalanceApi(Resource):
    @api.doc('Get the balance of an account based on connected exchanges')
    @api.doc(params={'userId': 'user id', 'exchangeId':'exchange id'})
    @api.response(200, 'Success')
    @api.response(500, 'Internal Server Error')
    def get(self):
        """Get the balance of an account based on connected exchanges"""
        try:
            userId = request.args.get('userId')
            exchangeId = request.args.get('exchangeId')
            if userId is None or exchangeId is None:
                resp = {
                    "status": "fail",
                    "result": "userId and exchangeId are required",
                    "message": "userId and exchangeId are required"            
                }
                return resp, 500
            else:
                exchange = ExchangeModel.query.filter_by(id=exchangeId).first()
                if exchange is None:
                    resp = {
                        "status": "fail",
                        "result": "exchange not found",
                        "message": "exchange not found"            
                    }
                    return resp, 500
                else:
                    if exchange.exchange_type == 'binance':
                        client = BinanceClient(exchange.key, exchange.secret)
                        balances = client.get_account()
                        balances = balances['balances']
                        balances = ExchangeOperations.spotAssetBalancesFilter(balances)
                        resp = {
                            "status": "ok",
                            "result": balances,
                            "message": "balances found"            
                        }
                        return resp, 200

                    elif exchange.exchange_type == 'binance-futures':
                        client = BinanceClient(exchange.key, exchange.secret)
                        balances = client.get_account()
                        balances = balances['balances']
                        balances = ExchangeOperations.futuresAssetBalancesFilter(balances)
                        resp = {
                            "status": "ok",
                            "result": balances,
                            "message": "balances found"            
                        }
                        return resp, 200
                    else:
                        resp = {
                            "status": "fail",
                            "result": "exchange not supported",
                            "message": "exchange not supported"            
                        }
                        return resp, 500

        except Exception as e:
            logger.exception(f"Get Balances Error: {str(e)}")
            resp = {
                "status": "fail",
                "result": str(e),
                "message": "error occured"            
            }
            return resp, 500


@api.route('/asset/precision')
class AssetPrecisionApi(Resource):
    @api.doc('Get asset symbol precision')
    @api.doc(params={'symbol': 'the asset symbol pair', 'exchangeId':'the selected exchange id'})
    @api.response(200, 'Success')
    @api.response(500, 'Internal Server Error')
    def get(self):
        """Get asset symbol precision"""
        try:
            
            pair = request.args.get('symbol')
            exchangeId = request.args.get('exchangeId')

            print(f"pair: {pair} exchnageId: {exchangeId}")

            symbol = pair.upper()

            if symbol is None:
                resp = {
                    "status": "fail",
                    "result": "symbol is required",
                    "message": "symbol is required"            
                }
                return resp, 500
            else:
                precision = ExchangeOperations.getAssetPrecision(symbol, exchangeId)
                resp = {
                    "status": "ok",
                    "result": precision,
                    "message": "precision found"            
                }
                return resp, 200

        except Exception as e:
            logger.exception(f"Get Asset Precision Error: {str(e)}")
            resp = {
                "status": "fail",
                "result": str(e),
                "message": "error occured"            
            }
            return resp, 500