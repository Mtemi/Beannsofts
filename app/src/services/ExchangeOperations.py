from logging import log
from typing import Dict
from app.src import db 
from app.src.models import ExchangeModel
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src.services.binanceoperations import BinanceOps
from app.src.utils import logging
from app.src.utils.binance.clientOriginal import Client as BinanceClient

logger = logging.GetLogger(__name__)

def queryDBForUserExchanges(user):
    return db.session.query(ExchangeModel).filter(ExchangeModel.user_id == user).all()

def exchangesSerializer(exchanges):
    return [{
        "exchange_id": exchange.id,
        "exchange_name": exchange.exchange_name,
        "key": exchange.key,
        "secret": exchange.secret,
        "exchange_type": exchange.exchange_type
    } for exchange in exchanges ]

def getAllExchanges(user):
    try:
        exchanges = queryDBForUserExchanges(user)
        print("EXCHNAGES", exchanges)
        if exchanges is not None:
            result = exchangesSerializer(exchanges)
            logger.info("Exchnages Found")
            resp = {
                "status": "ok",
                "result": result,
                "message": "exchanges found"
            }
            return resp, 200
        else:
            resp = {
                "status": "ok",
                "result": [],
                "message": "no exchanges found"            
            }
            logger.info("No exchanges Found")
            return resp, 200
    except Exception as e:
        logger.exception("List Exchanges Error: {}", e)
        resp = {
            "status": "fail",
            "result": str(e),
            "message": "error occured"            
        }
        return resp, 500


def spotAssetBalancesFilter(assetsList):
    balances =[]

    for asset in assetsList:
        if float(asset['free']) > 0.0000000:
            balances.append(asset)
    return balances


def futuresAssetBalancesFilter(assetsList):
    balances =[]

    for asset in assetsList:
        if float(asset['free']) > 0.0000000:
            balances.append(asset)
    return balances 


# to be moved to another folder
# edit exchange helper
def get_exchange_by_name(exch_name):
    exchange = ExchangeModel.query.filter_by(exchange_name=exch_name).first()
    return exchange

# add get exchanges by user 
def get_all_user_exchanges(user):
    exchanges =  ExchangeModel.query.filter_by(user_id=user.id).all()
    return exchanges
def getAssetPrecision(symbol: str, exchangeId: int) -> Dict[str, str]:
        logger.debug(f"Getting asset precisin for {symbol}")
        assetSymbol = symbol
        exchange = ExchangeModel.query.filter_by(id=exchangeId).first()
        if exchange.exchange_type == 'binance':
            client = BinanceOps(api_key=exchange.key, api_secret=exchange.secret, trade_symbol=symbol)
            
            info = client.get_exchange_info()

            stepSize = ''
            tickSize = ''

            for i in range(len(info['symbols'])):
                if assetSymbol == info['symbols'][i]['symbol']:
                    for x in range(len(info['symbols'][i]['filters'])):
                        if info['symbols'][i]['filters'][x]['filterType'] == 'LOT_SIZE':
                            stepSize = info['symbols'][i]['filters'][x]['stepSize']

                        if info['symbols'][i]['filters'][x]['filterType'] == 'PRICE_FILTER':
                            tickSize = info['symbols'][i]['filters'][x]['tickSize']

            pricePrecision = client.precisionValueCalc(float(tickSize))
            qtyPrecision = client.precisionValueCalc(float(stepSize))

            logger.debug(f"Found the price precision: {pricePrecision} and quantity precision: {qtyPrecision}")

            return {"pricePrecision": pricePrecision, "qtyPrecision": qtyPrecision}
            
        elif exchange.exchange_type == 'binance-futures':
            client = BinanceFuturesOps(api_key=exchange.key, api_secret=exchange.secret, trade_symbol=symbol)  

            info = client.futures_exchange_info()

            pricePrecision = 0
            quantityPrecision = 0

            for i in range(len(info['symbols'])):
                if assetSymbol == info['symbols'][i]['symbol']:
                    pricePrecision = int(info['symbols'][i]['pricePrecision'])
                    quantityPrecision = int(info['symbols'][i]['quantityPrecision'])
            
            logger.debug(f"Found the price precision: {pricePrecision} and quantity precision: {quantityPrecision}")

            return {"pricePrecision": pricePrecision, "qtyPrecision": quantityPrecision}
