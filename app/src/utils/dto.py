from flask_restx import Namespace, fields


class UserDto:
    api = Namespace('user', description='user related operations')
    user = api.model('user', {
        'email': fields.String(required=True, description='user email address'),
        'username': fields.String(required=True, description='user username'),
        'password': fields.String(required=True, description='user password'),

    })


class AuthDto:
    api = Namespace('auth', description='authentication related operations')
    auth = api.model('auth', {
        'email': fields.String(required=True, description='The email address'),
        'password': fields.String(required=True, description='The user password '),
    })


class BotDto:
    api = Namespace('bot', description='bot realated operations')

    dcabot = api.model('dcabot', {
        'botname': fields.String(required=True, description='The bot name specified by a user. It must be unique'),
        'exchange_id': fields.Integer(required=True, description='The exchange id to link API keys'),
        'pairlist': fields.List(fields.String(), required=True, description='The list of symbols to be traded'),
        'side': fields.String(required=True, description='order side either buy, sell'),
        'ordertype': fields.String(required=True, description='the order type either Market or Limit'),
        'qty': fields.Float(required=True, description='The quantity of the symbol to be traded'),
        'leverage': fields.Float(required=False, description='The leverage to be used for the trade', default=10),
        'stoploss': fields.Integer(required=True, description='The stoploss value in percentage'),
        'trailing_stop': fields.Integer(required=True, description='The trailing stop value in percentage'),
        'takeprofit': fields.Integer(required=True, description='The takeprofit value in percentage'),
        'trailing_stop_enabled': fields.Boolean(required=True, description='The trailing stop enabled'),
        'strategy': fields.String(required=True, description='The strategy to be used'),
        'timeframe': fields.String(required=True, description='The timeframe to be used e.g 1m, 5m, 30m, 1d...'),
        'interval_between_orders': fields.Integer(required=True, description="cool down between deals"),
        'order_timeout': fields.Integer(required=True, description="Time in seconds until an order that is not executed expires and is cancelled"),
        'max_active_trade_count': fields.Integer(required=True, description="maximum number of active orders at a time")
    })
    # dcabot = api.model('dca', {
    #     'botName': fields.String(required=True, description='The bot name specified by a user. It must be unique'),
    #     'side': fields.String(required=True, description='order side either buy, sell'),
    #     'orderType': fields.String(required=True, description='the order type either Sell or Buy'),
    #     'symbol': fields.String(required=True, description='the trading symbol pair'),
    #     'baseSymbol': fields.String(required=True, description='the asset to collect profits'),
    #     'tradeAmt': fields.Float(required=True, description='the maximum price to place an order'),
    #     'interval': fields.Integer(required=True, description='intervals to place the orders'),
    #     'maxOrderAmt': fields.Float(required=True, description='the max quantity for each order'),
    #     'minOrderAmt': fields.Float(required=True, description='the minimum quantity for each order'),
    #     'price': fields.Float(required=True, description='percentage to calculate price for limit order buy or sell'),
    #     'stopLoss': fields.Integer(required=True, description='percentatage to calculate stoploss price'),
    #     'takeProfit': fields.Integer(required=True, description='percentage to calculate takeprofit price'),
    #     'maxTradeCounts': fields.Integer(required=True, description='The max orders bot should place before it terminates'),
    #     'signalType': fields.String(required=True, description="bot start signal"),
    #     'exchange_id':fields.Integer(required=True, description='The exchange id to link API keys')
    # })
    gridbot = api.model('gridbot', {
        'botName': fields.String(required=True, description='The bot name specified by a user. It must be unique'),
        'symbol': fields.String(required=True, description='the trading symbol pair'),
        'gridQty': fields.Float(required=True, description='The numnber of grid'),
        'maxTradeCounts': fields.Integer(required=True, description='The max orders bot should place before it terminates'),
        'exchange_id': fields.Integer(required=True, description='The exchange id to link API keys'),
        'upperLimitPrice': fields.Float(required=True, description='the upper limit price'),
        'lowerLimitPrice': fields.Float(required=True, description='the lower limit price'),
        'qtyPerGrid': fields.Float(required=True, description='the quantity per grid')

    })

    gridbotupdate = api.model('gridbotupdate', {
        'id':fields.Integer(required=True, description='bot id'),
        'botName': fields.String(required=True, description='The bot name specified by a user. It must be unique'),
        'symbol': fields.String(required=True, description='the trading symbol pair'),
        'gridQty': fields.Float(required=True, description='The numnber of grid'),
        'maxTradeCounts': fields.Integer(required=True, description='The max orders bot should place before it terminates'),
        'exchange_id': fields.Integer(required=True, description='The exchange id to link API keys'),
        'upperLimitPrice': fields.Float(required=True, description='the upper limit price'),
        'lowerLimitPrice': fields.Float(required=True, description='the lower limit price'),
        'qtyPerGrid': fields.Float(required=True, description='the quantity per grid')

    })
    newBot = api.model('newBot', {
        'bot_id': fields.Integer(required=True, description='The bot Id'),
        'botName': fields.String(required=True, description='New Bot name')
    })
    botId = api.model('botId', {
        'bot_id': fields.Integer(required=True, description='The bot Id')
    })
    botOrder = api.model('botOrder', {
        'userId': fields.Integer(required=True, description='The user id'),
        'bot_id': fields.Integer(required=True, description='The bot Id')
    })
    # START GRID BOT DTO
    startGridBot = api.model('startGridBot', {
        'bot_id': fields.Integer(required=True, description='bot id')
    })


class ExchangeDto:
    api = Namespace('exchange', description='exchnage related operations')
    exchange = api.model('exchange', {
        # 'userId': fields.Integer(required=True, description='The user id'),
        'exch_name': fields.String(required=True, description='The name of the exchange as selected by user.Must be unique'),
        'api_key': fields.String(required=True, description='the Binance Api Key'),
        'api_secret': fields.String(required=True, description='the Binance Api Secret'),
        'exchange': fields.String(required=True, description='The exchange Type either binance or binance-futures')
    })
    exchange_balance_dto = api.model('exchange_balance_dto', {
        'exch_name': fields.String(required=True, description='The exchange name')
    })
    delete_exchange_dto = api.model("delete_exchange_dto", {
        "exchange": fields.String(required=True, description="exchangeType"),
        "exch_name": fields.String(required=True, description="exch_name")
    })


class OrderDto:
    api = Namespace('orders', description="orders related operations")
    orderList = api.model('orderList', {
        'symbol': fields.String(required=False, description='the filter symbol')
    })
    createOrderSpot = api.model('createOrderSpot', {
        'exchange_name': fields.String(required=True, description='The specific exchange name to obtain binance apidata'),
        'symbol': fields.String(required=True, description='the trading pair symbol'),
        'side': fields.String(required=True, description='the order side, BUY or SELL'),
        'type': fields.String(required=True, description='the order type MARKET, LIMIT ...'),
        'quantity': fields.Float(required=True, description='the amount of asset to buy or sell'),
        'price': fields.String(required=False, description='limit price percenage for limit order'),
    })
    createOrderFutures = api.model('createOrderFutures', {
        'exchange_name': fields.String(required=True, description='The specific exchange name to obtain binance apidata'),
        'symbol': fields.String(required=True, description='the trading pair symbol'),
        'side': fields.String(required=True, description='the order side, BUY or SELL'),
        'type': fields.String(required=True, description='the order type MARKET, LIMIT ...'),
        'quantity': fields.Float(required=True, description='the amount of asset to buy or sell'),
        'price': fields.String(required=True, description='limit price percentage for limit order'),
        'takeProfit': fields.Integer(required=True, description='the takeporofit price percentage, in not available, None'),
        'stopLoss': fields.Integer(required=True, description="stoploss price percentage"),
        'callbackRate': fields.Integer(required=True, description='Used with TRAILING_STOP_MARKET orders, min 0.1, max 5 where 1 for 1%'),
        'leverage': fields.Integer(required=True, description='Leverage value integer value between 1 and 125')
    })
    getAcctBalance = api.model('getAcctBalance', {
        'exchange_name': fields.String(required=True, description='The specific exchange name to obtain binance apidata'),
        'symbol': fields.String(required=True, description='the trading pair symbol'),
    })


class InvoiceDto:
    api = Namespace(
        'subscription', description="payment and subscription related operations")
    invoice = api.model('invoice', {
        'userId': fields.Integer(required=True, description='The user id'),
        'subscription': fields.String(Required=True, description="The subscription package being paid for")
    })


class SubscriptionPlanDto:
    api = Namespace('admin', description='admin realated operations')
    plan = api.model('plan', {
        'plan': fields.String(Required=True, description="The plan name in uppercase , STARTER, ADVANCED"),
        'features': fields.String(Required=True, description="a json string containing the specific limit parameters"),
        'description': fields.String(required=True, description='The feature description for the users to see'),
        'price': fields.Float(required=True, description='The price to pay in USD')
    })


class DictItem(fields.Raw):
    def output(self, key, obj, *args, **kwargs):
        try:
            dct = getattr(obj, self.attribute)
        except AttributeError:
            return {}
        return dct or {}


class SmartTradeDto:
    api = Namespace('smart trades',
                    description='All smart trade related operations')
    smart = api.model('smart', {
        # "userId": afields.Integer(required=True, description='The user id'),
        'smart_order_type': fields.String(Required=True, description="smart order type"),
        "exchange_data": DictItem({
            # "temp_market_price": "float",
            "exchange_id": "int",
            "symbol": "string",
            "amount": "float",
            # "side": "string",
            # "entry_sell_price": "float"
            }),

        "take_profit_targets": DictItem({
            "take_profit_price": "float",
            "take_profit_order_type": "string",
            "trailing_take_profit": "float",
            "take_profits": {
                "steps":[
                    {
                    "price":"float",
                    "percentQty":"float"
                    }
                ]
            }
        }),
        "stop_loss_targets": DictItem({
            "stop_loss_type": "string",
            "stop_loss_price": "float",
            "stop_loss": "float",
            "stop_loss_timeout": "int",
            "trailing_stop": "float"
        })
    })


class TerminalOrderDto:
    api = Namespace('Terminal Orders',
                    description='terminal orders realted operations')
    terminalOrder = api.model('terminalOrder', {
        # 'exchange_id': fields.Integer(required=True, description='The binance exchange id to place an order'),
        'exchange_name': fields.String(required=True, description='unique exchange name'),
        'symbol': fields.String(required=True, description='The trade pair'),
        'side': fields.String(required=True, description="either BUY or SELL"),
        'type': fields.String(required=True, description="The order type either Market or Limit"),
        "amt": fields.Float(required=True, description="The amount of funds to spend on trade, its unit*current prcie"),
        "unit": fields.Float(required=True, description="the amount of token to buy"),
        "price": fields.Float(required=False, description="The price of token.This is required for limit order, but for Market Order not required"),
        "timeinforce": fields.String(required=False, description="Time in force, required for limit order"),
        "leverage": fields.Integer(required=False, description="Required for futures trading orders else for spot order don't pass"),
        "targetprice": fields.Float(required=False, description="price for conditional orders, both market and Limit. If order is not conditinal, not required"),
        "triggerprice": fields.Float(required=False, description="price for conditional orders, both market and Limit. If order is not conditinal, not required"),
        "timeout": fields.Integer(required=False, description="This field take timeout in seconds, for conditional orders else don't pass"),
        "trailing": fields.Float(required=False, description="passed for market order with condition enabled, either percentage or Float price, else don't pass")
    })
    terminalOrderEdit = api.model('terminalOrderEdit', {
        'orderid': fields.Integer(required=True, description="The order ID"),
        # 'exchange_name': fields.String(required=True, description='unique exchange name'),
        'exchange_id': fields.Integer(required=True, description='The binance exchange id to place an order'),
        'symbol': fields.String(required=True, description='The trade pair'),
        'side': fields.String(required=True, description="either BUY or SELL"),
        'type': fields.String(required=True, description="The order type either Market or Limit"),
        "amt": fields.Float(required=True, description="The amount of funds to spend on trade, its unit*current prcie"),
        "unit": fields.Float(required=True, description="the amount of token to buy"),
        "price": fields.Float(required=False, description="The price of token.This is required for limit order, but for Market Order not required"),
        "timeinforce": fields.String(required=False, description="Time in force, required for limit order"),
        "leverage": fields.Integer(required=False, description="Required for futures trading orders else for spot order don't pass"),
        "targetprice": fields.Float(required=False, description="price for conditional orders, both market and Limit. If order is not conditinal, not required"),
        "triggerprice": fields.Float(required=False, description="price for conditional orders, both market and Limit. If order is not conditinal, not required"),
        "timeout": fields.Integer(required=False, description="This field take timeout in seconds, for conditional orders else don't pass"),
        "trailing": fields.Float(required=False, description="passed for market order with condition enabled, either percentage or Float price, else don't pass")
    })
    cancelTermOrder = api.model('cancelTermOrder', {
        'orderid': fields.Integer(required=True, description="The order ID")
    })


class TelegramNotifierDto:
    api = Namespace(
        'Telegram Bot', description="Telegram Bot related operations")
    telegramDto = api.model('telegramDto', {
        'user_id': fields.Integer(required=True, description="The user ID random number generated")
    })


class LogsDto:
    api = Namespace('Notificatios logs', description='Log related operations')
    logStatusDto = api.model('updateStatusDto', {
        'channel': fields.Integer(required=True, description="message channel(user id)"),
        'eventName': fields.String(required=True, description="eventName"),
        'timestamp': fields.Float(required=True, description="timestamp"),
        'status': fields.String(required=True, description="status")
    })


class StrategiesDto:
    api = Namespace('Strategies', description="Strategy related operations")


class WebhookDto:
    api = Namespace('WebhookSignal', description="Webhook signals")

    userBotId = api.model('userBotId', {
        'userId': fields.Integer(required=True, description='The user id'),
        'botId': fields.Integer(required=True, description='The bot Id'),
        'symbol': fields.String(required=True, description='The trade pair symbol eg ETHUSDT'),
    })

class AccountsDto:
    api = Namespace('Accounts', description="Account related operations")
