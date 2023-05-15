import pickle
from typing import Dict
import redis
from app.src.config import Config
from app.src.services.pnl.utils import Pnl

redisConn = redis.from_url(Config.REDIS_URL)
positionData = {

    'markingPrice': 110,
    'intialBuyRate': 35130,
    'positionSize': 10,
    'leverage': 10,
    'orderType': '',
    'side': '',
    'symbol':  ''

}


# Gather all the information needed


def pnlCalcualtor(positionData: Dict, botId: int, userId: int):

    pnl = Pnl()
    userBotDetails = {'botId': botId, 'userId': userId}
    intialRate = positionData['intialRate']
    positionSize = positionData['positionSize']
    leverage = positionData['leverage']
    symbol = positionData['symbol']
    exchangeType = positionData['exchangeType']
    side = positionData['side']
    price_data = redisConn.get(symbol)

    if price_data is None:
        print("none")
    else:
        price_data = pickle.loads(price_data)
        current_price = float(price_data['b'])
        markingPrice = current_price

        print("[X] {0} data:{1}".format(price_data['s'], current_price))
        if exchangeType == 'binance':
            if side == 'BUY':
                resp = pnl.spotLongUnrealizedPnl(
                    markingPrice, intialRate, positionSize)
                print("The response", resp)
                return resp

            if side == 'SELL':
                resp = pnl.spotShortUnrealizedPnl(
                    markingPrice, intialRate, positionSize)
                print("The response", resp)
                return resp
        if exchangeType == 'binance-futures':
            if side == 'BUY':
                resp = pnl.futuresLongUnrealizedPnl(
                    markingPrice, intialRate, positionSize)
                return resp
            if side == 'SELL':
                resp = pnl.futuresShortUnrealized(
                    markingPrice, intialRate, positionSize)
                return resp

        if exchangeType == 'margin':
            resp = pnl.marginUnrealizedPnl(
                intialRate, markingPrice, positionSize, leverage)
            return resp
