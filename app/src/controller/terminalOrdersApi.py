import datetime
from os import abort
from app.src.utils import logging
from app.tasks import startConditionalTerminalOrder
from app.src.models import TerminalOrderModel
from app.src.controller.userAuth import login_required
from flask_restx import Resource, abort
from flask import request
from app.src.utils.dto import TerminalOrderDto
from app.src.services.TerminalOrders.terminalorderservices import OrderOps
from app.src import db
from app.src.models.exchange import ExchangeModel
import math


api = TerminalOrderDto.api
terminalOrder = TerminalOrderDto.terminalOrder
terminalOrderEdit = TerminalOrderDto.terminalOrderEdit
cancelTermOrder = TerminalOrderDto.cancelTermOrder

logger = logging.GetLogger(__name__)


def get_exchange_from_name(exchange_name, userId):
     # get exchange from exchange_name
    exchange = ExchangeModel.query.filter_by(user_id=userId, exchange_name=exchange_name).first()
    return exchange
    

@api.route('/conditional/order')
class TerminalOrder(Resource):
    @login_required
    @api.doc('Create Terminal orders')
    @api.expect(terminalOrder, validate=True)
    def post(self, user):
        """Create a new order from the trading terminal"""
        order = request.json
        userId = user.id
        exchange = get_exchange_from_name(exchange_name=order["exchange_name"], userId=userId)

        if exchange:
            order.update({"exchange_id": exchange.id})
            order.pop("exchange_name")
        else:
            return {
                "status": 404,
                "message": "exchange provided was not found"
        }
        
        order.update({"userid": userId, "modified_on": None, "status": "open", "executed_on": None, "change_reason": None, "taskid":None, "unit": 1})
        try:
            logger.warning(f"exchange_name {exchange.exchange_name} found exchange_id {exchange.id}")
            orderToDB = TerminalOrderModel(**order)
            db.session.add(orderToDB)
            db.session.commit()
        except Exception as e:
            return {"message":"Fail: Order Failed To submit", "result":f"errror occured {e}"}, 400

        resp = order
        exchangeInfo = OrderOps.getExchangeInfo(order["exchange_id"])
        # exchangeInfo = OrderOps.getExchangeInfoByName(order["exchange_name"])

        

        resp.update({"orderid":orderToDB.id, "exchangeInfo": {"exchangeType":exchangeInfo.exchange_type, "key": exchangeInfo.key, "secret": exchangeInfo.secret} })
        
        terminalOrder = startConditionalTerminalOrder.apply_async(args=(resp,))
        logger.info(f"Terminal Order task started, ID: {terminalOrder.id}")
        db.session.query(TerminalOrderModel).filter(TerminalOrderModel.id == orderToDB.id).update({"taskid": terminalOrder.id})
        db.session.commit()
        return {"message":"Success", "result":resp}, 200

    @login_required
    @api.doc('Get a list of all user terminal orders')
    @api.doc(params={'exchange_name': 'The exchange name', 'page': 'page to be rendered'})
    def get(self,user):
        """Returns a list of all terminal orders specific to a user"""
        logger.info(f"{user.email} requesting list of terminal orderss")
        userId = user.id
        
        try:
            page = int(request.args.get('page'))
        except TypeError:
            return {
                "status": 200,
                "message": "error page must be an integer"
            }

        
        exchange_name = request.args.get("exchange_name")
        if not exchange_name:
            return {
                "status": 400,
                "message": "exchange_name is a required param"
            }

        exchange = get_exchange_from_name(exchange_name=exchange_name, userId=user.id)

        if not exchange:
            return {
                "status": 404,
                "message": "exchange does not exist"
            }

        try:
            orders = db.session.query(TerminalOrderModel).filter(TerminalOrderModel.userid == userId, TerminalOrderModel.exchange_id == exchange.id).all()
        except Exception as e:
            logger.error(f"{user.email} exception hit after filtering terminal orders from db exception {str(e)}")

            return {"message":"Fail", "result": str(e)}, 500

        resp = [{
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
        } for order in orders ]

        result = resp
        if len(result) == 0:
            return {
                "status": 200,
                "result": result
            }

        # current page
        # orders per page
        per_page = 10
        # total number of orders
        total_number = len(result)
        # total number of pages
        total_pages = math.ceil(total_number / per_page)

        # check validity of the page
        if page > total_pages:
            return {
                "status": 200,
                "message": "page number out of range"
            }

        # start index and end index for list slicing
        # check if is page 1
        if page == 1:
            start_index = 0
        else:
            start_index = ((page - 1) * per_page) 

        # check end index
        end_index = start_index + (per_page - 1)

        # initialize page data starting with none
        data_in_page = None

        # check if end index is not less than total
        if not ((end_index) < total_number):
            end_index = total_number - 1
        
        end_index += 1
        data_in_page = result[start_index:end_index]

        print(f"start index {start_index} endindex {end_index}")
        return {
            "status": 200,
            "total_items": len(result),
            "total_pages": total_pages,
            "current_page": page,
            "result" : data_in_page
            }, 200

    @login_required
    @api.doc('Edit a terminal orders')
    @api.expect(terminalOrderEdit, validate=True)
    def put(self, user):
        """Edit a terminal order before it has executed"""
        params = request.json
        
        userId = user.id
        

        try:
            order = db.session.query(TerminalOrderModel).filter(TerminalOrderModel.id == params["orderid"]).first()
        except Exception as e:
            abort(code=404, message="Error editing order, Order Not Found")
        
        try:
            if order is not None:
                params.update({"userid": userId, "modified_on": datetime.datetime.utcnow().strftime("%d-%b-%Y (%H:%M:%S.%f)"), "status": "open", "executed_on": None, "change_reason": "Order Details Updated"})
                new_params = params.copy()
                new_params.pop("orderid")

                # Cancel old terminal order celery task
                taskID = order.taskid
                task = startConditionalTerminalOrder.AsyncResult(taskID).revoke(terminate=True)
                # Restart the terminal order task
                exchangeInfo = OrderOps.getExchangeInfo(order.exchange_id)

                params.update({"exchangeInfo": {"exchangeType":exchangeInfo.exchange_type, "key": exchangeInfo.key, "secret": exchangeInfo.secret} })
        
                terminalOrder = startConditionalTerminalOrder.apply_async(args=(params,))
                logger.info(f"Terminal Order task started, ID: {terminalOrder.id}")
                newTaskId = {"taskid": terminalOrder.id}
                # TODO update the taskid in the DB
                # logger.warning(f"exchange_name {exchange.exchange_name} found exchange_id {exchange.id}")

                db.session.query(TerminalOrderModel).filter(TerminalOrderModel.id == order.id).update(new_params)
                db.session.commit()
                return {"message":"Ok", "result":params}
            else:
                return {"message":"fail", "result":"orderid does not exist"}
        except Exception:
            abort(code=500, message="Error saving the order")

    @login_required
    @api.doc('Cancel a conditional terminal order')
    @api.param('orderId', 'The order id')
    def delete(self, user):
        """Cancel a conditional terminal orders"""
        orderId = request.args.get('orderId')
        try:
            order = db.session.query(TerminalOrderModel).filter(TerminalOrderModel.id == orderId, TerminalOrderModel.userid == user.id).first()
        except Exception as e:
            logger.exception("Cancel Conditional Order Error, {}".format(str(e)))
            abort(code=404, message="Order Not Found")

        if order:
            try:
                # Camce; TASK
                taskID = order.taskid
                task = startConditionalTerminalOrder.AsyncResult(taskID).revoke(terminate=True)
                # update DB
                db.session.query(TerminalOrderModel).filter(TerminalOrderModel.id == orderId).update({"modified_on": datetime.datetime.utcnow().strftime("%d-%b-%Y (%H:%M:%S.%f)"), "status": "closed", "executed_on": None, "change_reason": "Cancelled Order"})
                db.session.commit()
                return {"message":"Ok", "result": "Order Cancelled, Succesfully"}, 200
            except Exception as e:
                logger.exception("Cancel Conditional Order Error, {}".format(str(e)))
                abort(500, "Order Upddate Error")
        
        else:
            return {
                "message": "order with this order id not found"
            }, 404
