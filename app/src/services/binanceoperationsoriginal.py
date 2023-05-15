from app.src.utils.binance.clientOriginal import Client as BinanceClient
import math


class BinanceOps(BinanceClient):
    def __init__(self, api_key=None, api_secret=None, requests_params=None, tld='com', trade_symbol=None):
        super().__init__(api_key=None, api_secret=None, requests_params=None, tld='com')

        self.API_URL = self.API_URL.format(tld)
        self.MARGIN_API_URL = self.MARGIN_API_URL.format(tld)
        self.WEBSITE_URL = self.WEBSITE_URL.format(tld)
        self.FUTURES_URL = self.FUTURES_URL.format(tld)

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
        self._requests_params = requests_params
        self.response = None

        # init DNS and SSL cert
        self.ping()
        # authentication stored in is_authentic
        self.is_authentic = self.authenticateKeys()
        self.trade_symbol = trade_symbol

        self.base_asset = self.symbolInfo()["baseAsset"]
        self.quote_asset = self.symbolInfo()["quoteAsset"]

        self.pricePrecision = self.getAssetPrecision()["pricePrecision"]
        self.qtyPrecision = self.getAssetPrecision()["qtyPrecision"]

        self.lastPrice = self.getLastPrice()

        self.timeInForce = 'GTC'

    def symbolInfo(self):
        exchange_info = self.get_exchange_info()
        for exchange in exchange_info['symbols']:
            if exchange["symbol"] == self.trade_symbol:
                base_asset = exchange["baseAsset"]
                quote_asset = exchange["quoteAsset"]

                return {"baseAsset": base_asset, "quoteAsset": quote_asset}
                break

    def precisionValueCalc(self, x):
        max_digits = 14
        int_part = int(abs(x))
        magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
        if magnitude >= max_digits:
            return (magnitude, 0)
        frac_part = abs(x) - int_part
        multiplier = 10 ** (max_digits - magnitude)
        frac_digits = multiplier + int(multiplier * frac_part + 0.5)
        while frac_digits % 10 == 0:
            frac_digits /= 10
        count = int(math.log10(frac_digits))
        return count

    def round_decimals_down(self, number: float, decimals: int = 2):
        """
        Returns a value rounded down to a specific number of decimal places.
        """
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)

        factor = 10 ** decimals
        return math.floor(number * factor) / factor

    def authenticateKeys(self):
        # authenticating the api_keys
        try:
            params = {'symbol': 'LTCBTC', 'recvWindow': 60000}
            self.get_open_orders(**params)
            return True
        except Exception as e:
            # the prints here for development purposes irrelevant on production stage
            # error responses
            # print(e)

            # print(e.message)
            # print ("Eror in line: {}".format(e))
            # print ("{}".format(e.status_code ))
            # print ("{}".format(e.response))
            # print ("{}".format(e.code))
            # print ("{}".format(e.message))
            # print ("{}".format(e.request))

            return {"message": e.message, "status": e.status_code}

    # check open orders for a specific symbol
    def checkOpenOrders(self):
        params = {'symbol': self.trade_symbol}

        if self.is_authentic == True:
            res = self.get_open_orders(**params)
            if res == None or res == []:
                return False
            else:
                # {
                #     "symbol": "LTCBTC",
                #     "orderId": 1,
                #     "clientOrderId": "myOrder1",
                #     "price": "0.1",
                #     "origQty": "1.0",
                #     "executedQty": "0.0",
                #     "status": "NEW",
                #     "timeInForce": "GTC",
                #     "type": "LIMIT",
                #     "side": "BUY",
                #     "stopPrice": "0.0",
                #     "icebergQty": "0.0",
                #     "time": 1499827319559
                # }

                return res
        else:
            return self.is_authentic

    def checkAllOPenOrders(self):
        # params={'symbol':self.trade_symbol}

        if self.is_authentic == True:
            res = self.get_open_orders()
            if res == None or res == []:
                return False
            else:
                # {
                #     "symbol": "LTCBTC",
                #     "orderId": 1,
                #     "clientOrderId": "myOrder1",
                #     "price": "0.1",
                #     "origQty": "1.0",
                #     "executedQty": "0.0",
                #     "status": "NEW",
                #     "timeInForce": "GTC",
                #     "type": "LIMIT",
                #     "side": "BUY",
                #     "stopPrice": "0.0",
                #     "icebergQty": "0.0",
                #     "time": 1499827319559
                # }

                return res
        else:
            return self.is_authentic

    def checkAllOrders(self):
        params = {'symbol': self.trade_symbol}

        if self.is_authentic == True:
            res = self.get_all_orders(**params)
            if res == None or res == []:
                return False
            else:
                # {
                #     "symbol": "LTCBTC",
                #     "orderId": 1,
                #     "clientOrderId": "myOrder1",
                #     "price": "0.1",
                #     "origQty": "1.0",
                #     "executedQty": "0.0",
                #     "status": "NEW",
                #     "timeInForce": "GTC",
                #     "type": "LIMIT",
                #     "side": "BUY",
                #     "stopPrice": "0.0",
                #     "icebergQty": "0.0",
                #     "time": 1499827319559
                # }

                return res
        else:
            return self.is_authentic

    def checkWalletBalance(self, params):
        # params= { 'asset':'BTC'}
        if self.is_authentic == True:
            if params['asset'] == self.quote_asset:
                params = {"asset": self.quote_asset}
                res = self.get_asset_balance(**params)
                return res

            if params['asset'] == self.base_asset:
                params = {"asset": self.base_asset}
                res = self.get_asset_balance(**params)
                return res
            # {
            #     "asset": "BTC",
            #     "free": "4723846.89208129",
            #     "locked": "0.00000000"
            # }

        else:
            return self.is_authentic

    def getLastPrice(self):
        # params= { 'symbol':'BTC'}
        params = {'symbol': self.trade_symbol}
        if self.is_authentic == True:
            try:
                res = self.get_symbol_ticker(**params)
                return float(res['price'])
            except Exception as e:
                return e
        else:
            return self.is_authentic

    def getAssetPrecision(self):
        assetSymbol = self.trade_symbol
        info = self.get_exchange_info()

        stepSize = ''
        tickSize = ''

        for i in range(len(info['symbols'])):
            if assetSymbol == info['symbols'][i]['symbol']:
                for x in range(len(info['symbols'][i]['filters'])):
                    if info['symbols'][i]['filters'][x]['filterType'] == 'LOT_SIZE':
                        stepSize = info['symbols'][i]['filters'][x]['stepSize']

                    if info['symbols'][i]['filters'][x]['filterType'] == 'PRICE_FILTER':
                        tickSize = info['symbols'][i]['filters'][x]['tickSize']

        pricePrecision = self.precisionValueCalc(float(tickSize))
        qtyPrecision = self.precisionValueCalc(float(stepSize))

        return {"pricePrecision": pricePrecision, "qtyPrecision": qtyPrecision}

    def getOrderQuantity(self, walletBalance, lastPrice):
        ticks = {}
        for filt in self.get_symbol_info(self.trade_symbol)['filters']:
            if filt['filterType'] == 'LOT_SIZE':
                ticks[self.quote_asset] = filt['stepSize'].find('1') - 2
                break

        orderQuantity = ((math.floor(float(walletBalance)) *
                          10**ticks[self.quote_asset] / lastPrice)/float(10**ticks[self.quote_asset]))

        return self.round_decimals_down(orderQuantity, self.qtyPrecision)

    def getTakeProfit(self, percentVal):
        '''
        This method generates:-
        1. TakeProfit for takeprofit order SELL
        2. StopPrice for STOP_LOSS_LIMIT_ORDER BUY and STOP_LOSS_ORDER BUY
        3. StopPrice for TAKE_PROFIT_LIMIT_ORDER SELL
        '''
        takeProfit = self.lastPrice + ((percentVal / 100) * self.lastPrice)
        return (self.round_decimals_down(takeProfit, self.pricePrecision))

    def getLimitPrice(self, percentVal):
        '''
        This method generates:-
        1. LimitPrice for Limit order
        2. TakeProfit for takeprofit order BUY
        2. StopPrice for STOP_LOSS_LIMIT_ORDER SELL and STOP_LOSS_ORDER SELL
        3. StopPrice for TAKE_PROFIT_LIMIT_ORDER BUY
        '''
        limitPrice = round(
            self.lastPrice - (float(percentVal)/100) * self.lastPrice, 8)
        return float(self.round_decimals_down(limitPrice, self.pricePrecision))

    def stopLossLimitOrder(self, params):
        """Process the values of Limit order"""
        if params["side"] == 'buy':
            stopPrice = self.getTakeProfit(float(params['stopLoss']))
        if params["side"] == "sell":
            stopPrice = self.getLimitPrice(float(params['stopLoss']))

        price = self.getLastPrice()
        quantity = params["quantity"]
        print("STOP PRICES", stopPrice)
        return {"timeInForce": self.timeInForce, "stopPrice": stopPrice, "price": price, "quantity": quantity}

    def takeProfitLimitOrder(self, params):
        """Process the values of take profit Limit order"""
        if params["side"] == 'buy':
            stopPrice = self.getLimitPrice(params['takeProfit'])
        if params["side"] == "sell":
            stopPrice = self.getTakeProfit(params['takeProfit'])

        price = self.getLastPrice()
        quantity = params["quantity"]

        return {"timeInForce": self.timeInForce, "stopPrice": stopPrice, "price": price, "quantity": quantity}

    def limitMaker(self, params):
        if params['side'] == 'buy':
            price = self.getLimitPrice(float(params['price']))
        if params['side'] == 'sell':
            price = self.getTakeProfit(float(params['price']))
        print("price", price)
        return {"quantity": params['quantity'], "price": price}

    def sendOrder(self, params):
        # params in is json/dictionary
        # params = {'symbol':trade_symbol, 'side':'None', 'type':'None', timeInForce':'None','quantity':'None','quoteOrderQty':'None','price':'None' }
        # This function takes all order types
        if self.is_authentic == True:
            orderDetails = self.orderToPlaceProcessor(params)
            res = self.create_order(**orderDetails)
            return res
        else:
            return self.is_authentic

    def limitOrderData(self, params):
        # processes the specific details for limit type

        limitPrice = self.getLimitPrice(params["price"])

        return {"timeInForce": self.timeInForce, "quantity": params['quantity'], "price": limitPrice}

    def stopLossData(self, params):
        # processes the specific details for stopLoss order type
        stopPrice = 0
        if params['side'] == 'buy':
            stopPrice = self.getTakeProfit(float(params["stopLoss"]))

        if params['side'] == 'sell':
            stopPrice = self.getLimitPrice(float(params["stopLoss"]))

        return {"quantity": params['quantity'], "stopPrice": stopPrice}

    def takeProfitData(self, params):
        # processes the specific details for Takeprofit order type
        stopPrice = 0
        if params['side'] == 'buy':
            stopPrice = self.getLimitPrice(float(params["takeProfit"]))

        if params['side'] == 'sell':
            stopPrice = self.getTakeProfit(float(params["takeProfit"]))

        return {"quantity": params['quantity'], "stopPrice": stopPrice}

    # FIXME This method needs a serious rethink. and redesign

    def orderToPlaceProcessor(self, params):
        # TODO check previous positions
        order_basics = {"symbol": params["symbol"], "type": params['type'],
                        "side": params["side"], "quantity": params["quantity"]}
        open_orders = self.checkOpenOrders()
        print('Open Order', open_orders)
        if open_orders == False:
            if params["type"] == 'MARKET':
                pass
            elif params["type"] == 'LIMIT':
                order_basics.update(self.limitOrderData(params))

            elif params["type"] == 'STOP_LOSS':
                order_basics.update(self.stopLossData(params))

            elif params["type"] == 'STOP_LOSS_LIMIT':
                order_basics.update(self.stopLossLimitOrder(params))

            elif params["type"] == 'TAKE_PROFIT':
                order_basics.update(self.takeProfitData(params))

            elif params["type"] == 'TAKE_PROFIT_LIMIT':
                order_basics.update(self.takeProfitLimitOrder(params))

            elif params["type"] == 'LIMIT_MAKER':
                order_basics.update(self.limitMaker(params))
            print("paramsssssssssss", order_basics)
            return order_basics
        else:
            print("This code executed")
            # extract side
            # extract quantity
            # leverage
            positionQty = open_orders[0]['origQty']
            positionSide = open_orders[0]['side']
            positionOrderId = open_orders[0]['orderId']

            # buy quote_asset
            # if params['side'] == "buy":
            #     assetparams = {'asset':self.base_asset}
            #     if self.checkWalletBalance(assetparams) != False:
            #         wallet_balance = float(self.checkWalletBalance(assetparams)['free'])
            #         last_price = self.getLastPrice()
            #         quantity = self.getOrderQuantity(wallet_balance, last_price)

            #         return {"quantity":quantity, "last_price": last_price, "wallet_ballance": wallet_balance}
            # # sell base_asset
            # if params['side'] == "sell":
            #     assetparams = {'asset':self.base_asset}
            #     if self.checkWalletBalance(assetparams) != False:
            #         wallet_balance = float(self.checkWalletBalance(assetparams)['free'])
            #         last_price = self.getLastPrice()
            #         quantity = self.getOrderQuantity(wallet_balance, last_price)

            #         return {"quantity":quantity, "last_price": last_price, "wallet_ballance": wallet_balance}
        # TODO if yes and same side add amount --- and resend the order
        # TODO if opp position cancel the previous position


# FUTURES METHODS b
class PnlCalculator():
    def spotLongUnrealizedPnl(self, markingPrice, intialBuyRate, positionSize):
        """ Long spot unrealized pnl"""
        unrealizedPnl = (markingPrice - intialBuyRate)*positionSize
        return unrealizedPnl

    def spotShortUnrealizedPnl(self, intialSellRate, markingPrice, positionSize):
        """Short spot unrealized pnl"""
        unrealizedPnl = (intialSellRate - markingPrice)*positionSize
        return unrealizedPnl

    def marginUnrealizedPnl(self, intialBuyRate, markingPrice, positionSize, leverage):
        """ Margin unrealized pnl"""
        unrealizedPnl = (((markingPrice - intialBuyRate)
                         * positionSize)/leverage)*leverage
        return unrealizedPnl

    def futuresLongUnrealizedPnl(self, markingPrice, intialBuyRate, positionSize):
        """ Futures short unrealized pnl"""
        unrealizedPnl = (markingPrice - intialBuyRate)*positionSize
        return unrealizedPnl

    def futuresShortUnrealized(self, markingPrice, intialSellRate, positionSize):
        """Futures short unrealized pnl"""
        unrealizedPnl = (intialSellRate - markingPrice)*positionSize
        return unrealizedPnl
