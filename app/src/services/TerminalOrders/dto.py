from flask_restx import Namespace, fields

class TerminalOrderDto:
    api = Namespace('Terminal Orders', description='terminal orders realted operations')
    terminalOrder = api.model('terminalOrder', {
        'exchange_id': fields.Integer(required=True, description='The binance exchange id to place an order'),
        'symbol': fields.String(required=True, description='The trade pair'),
        'side': fields.String(required=True, description="either BUY or SELL"),
        'type':fields.String(required=True, description="The order type either Market or Limit"),
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