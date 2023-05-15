from app.src.utils import logging
from app.tasks import startConditionalTerminalOrder
from app.src.models import TerminalOrderModel
from app.src.controller.userAuth import login_required
from flask_restx import Resource
from flask import request
from app.src.services.TerminalOrders.dto import TerminalOrderDto
from app.src.services.TerminalOrders.terminalorderservices import OrderOps
from app.src import db


api = TerminalOrderDto.api
terminalOrder = TerminalOrderDto.terminalOrder

logger = logging.GetLogger(__name__)

@api.route('/order')
class TerminalOrder(Resource):
    @login_required
    @api.doc('Create Terminal orders')
    @api.expect(terminalOrder, validate=True)
    def post(self, user):
        """Create a new order from the trading terminal"""
        order = request.json
        order.update({"userid": user.id, "modified_on": None, "status": "open", "executed_on": None, "change_reason": None})
        try:
            orderToDB = TerminalOrderModel(**order)
            db.session.add(orderToDB)
            db.session.commit()
        except Exception as e:
            return {"message":"Fail: Order Failed To submit", "result":f"errror occured {e}"}, 400

        resp = order
        exchangeInfo = OrderOps.getExchangeInfo(order["exchange_id"])

        resp.update({"orderid":orderToDB.id, "exchangeInfo": {"exchangeType":exchangeInfo.exchange_type, "key": exchangeInfo.key, "secret": exchangeInfo.secret} })
        
        terminalOrder = startConditionalTerminalOrder.apply_async(args=(resp,))

        logger.info(f"Terminal Order task started, ID: {terminalOrder.id}")

        return {"message":"Success", "result":resp}, 200

    @login_required
    @api.doc('Get a list of all user terminal orders')
    def get(self, user):
        """Returns a list of all terminal orders specific to a user"""
        try:
            orders = db.session.query(TerminalOrderModel).filter(TerminalOrderModel.userid == user.id).all()
        except Exception as e:
            return {"message":"Fail", "result": str(e)}, 500
        
        resp =[ {
            "orderid": order.id,
            "exchange_id": order.exchange_id,
            "userid": order.userid,
            "symbol": order.symbol,
            "side": order.side,   
            "type": order.type,
            "unit": order.unit,
            "amt": order.amt,
            "price": order.price,
            "leverage": order.leverage,
            "targetprice": order.targetprice,
            "timeout": order.timeout,
            "trailing": order.trailing,
            "created_on": str(order.created_on),
            "modified_on": str(order.modified_on),
            "status": order.status,
            "executed_on": str(order.executed_on),
            "change_reason": order.change_reason,
        } for order in orders]

        return {"message":"Ok", "result":resp}, 200

    def put(self):
        """Edit a terminal order before it has executed"""
        pass

    def delete(self):
        """Delete a terminal orders"""
        pass
