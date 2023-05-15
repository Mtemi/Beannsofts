import pickle
import redis
from app.src.config import Config
from app.src.services.binanceoperations import PnlCalculator
redisConn = redis.from_url(Config.REDIS_URL)

markingPrice = 110
intialBuyRate = 35130
positionSize = 10
leverage = 10
pnlcalc = PnlCalculator()
resp = pnlcalc.spotLongUnrealizedPnl(markingPrice, intialBuyRate, positionSize)

resp2 = pnlcalc.marginUnrealizedPnl(
    intialBuyRate, markingPrice, positionSize, leverage)
print(resp)

print(resp2)

resp3 = pnlcalc.futuresLongUnrealizedPnl(
    markingPrice, intialBuyRate, positionSize)
print(resp3)

while True:

    price_data = redisConn.get('BTCUSDT')

    intialBuyRate = 35130
    positionSize = 10

    if price_data is None:
        print("none")
    else:
        price_data = pickle.loads(price_data)
        current_price = float(price_data['b'])
        markingPrice = current_price

        print("[X] {0} data:{1}".format(price_data['s'], current_price))

        resp3 = pnlcalc.futuresLongUnrealizedPnl(
            markingPrice, intialBuyRate, positionSize)
        print(resp3)
