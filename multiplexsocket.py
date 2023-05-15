from app.src.utils.binance.clientOriginal import Client
from app.src.utils.binance.streams import ThreadedWebsocketManager

api_key = "02eTTLVw9T6g3oEmelloLP3IGt8QlCoCOKvdWshpKU1KWOQ7sDIm2xrDOPe3X9S6 "
api_secret = "MjP6qfoCnLX8KeIFAzW0KyE3LL96xlbbTYI962pWtyaES4SBIWiJXBJ1S3uMwoS8"

twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
# client = Client(api_key=api_key, api_secret=api_secret)
# exchangeinfo = client.get_exchange_info()

# print(exchangeinfo)
# twm.stop()
streams = ['ethusdt@bookTicker']
streams1 = ['ethusdt@kline_1m', 'adausdt@kline_1m',
            'dogeusdt@kline_1m', 'btcusdt@kline_1m']

streams2 = []

klines = []


def priceFetcher(streams, twm, kliness):
    def handle_socket_message(price_data):
        # print("price data", price_data)
        kliness.append(price_data)
        print("The length of klines a", len(kliness))
        # print("The length of streams a", len(streams))

        # print(f"KLINES ------------ {klines}")
        # klines.clear()
        # print(f"cleared KLINES ------------ {klines}")
        # priceFetcher(streams1, twm, klines, socketName)
        # twm.stop()
        # twm.stop_socket(socketName)
        if len(klines) >= len(streams):
            print("Klines", klines)
            twm.stop()

    twm.start()

    twm.start_multiplex_socket(
        callback=handle_socket_message, streams=streams)
    twm.join()
    return 1


priceFetcher(streams, twm, klines)
