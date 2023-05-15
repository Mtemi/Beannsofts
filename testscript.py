# test open positions
from app.src.utils.binance.clientOriginal import Client


def get_open_positions(api_key, api_secret):
    client = Client(api_key=api_key, api_secret=api_secret)
    orders = client.futures_get_all_orders()
    return orders



api_key = "BmJFXm7w97TeTX9pZIBdFXZIwVpApm3euePlCD86tEfqnjTDhoAPfu253nOGv49B"
api_secret = "5NRO5vkBxT5SLo13YoRHWdIYD8E0ohsBJKRMUl5Cspjo1BaTiKXn4yScOISfm72g"
# data = get_open_positions(api_key=api_key, api_secret=api_secret)

# futures_get_all_orders
# print(data)



# open positions implementation
from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps

def CheckOpenPositions(api_key, api_secret):

    # ApiData = fetchBinanceKeys(user, exchange_name)
    # key = ApiData.key
    # secret = ApiData.secret
    # exchangeType = ApiData.exchange_type

    client = BinanceFuturesOps(
        api_key=api_key, api_secret=api_secret, trade_symbol="BTCUSDT")
    position = client.checkPositionInfo()
    # print(position)
    if not position:
        return "You have no open positions"
    processed = []
    # print(position)
    for pos in position:
        if float(pos['unRealizedProfit']) != float("0.00000000"):
            print("positon response", pos)
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

positions = CheckOpenPositions(api_key=api_key, api_secret=api_secret)

print(positions)