from app.src import db
from enum import Enum
import datetime
from .helpers import BaseClass

class SmartOrderStatus(Enum):
    OPEN = "open"
    CANCELED = "cancelled"
    FILLED = "filled"

class SmartOrdersModel(BaseClass, db.Model):
    """
    Trade database model.
    Also handles updating and querying trades
    """
    tablename = 'smart_orders'

    id = db.Column(db.Integer, primary_key=True)
    smart_order_type = db.Column(db.String(25), nullable=False)
    exchange_id = db.Column(db.BigInteger, db.ForeignKey("exchange.id"), nullable=False)
    exchange_order_id = db.Column(db.BigInteger, nullable=False)
    sl_steps = db.Column(db.BigInteger, nullable=False)
    userid = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    task_id = db.Column(db.String(255), nullable=True)
    symbol = db.Column(db.String(25), nullable=False)
    side = db.Column(db.String(), nullable=False)   
    # order_type = db.Column(db.String(25), nullable=False)
    amt = db.Column(db.Float(),nullable=False)
    price = db.Column(db.Float(),nullable=False)
    order_details_json = db.Column(db.PickleType())
    created_on = db.Column(db.DateTime, nullable=False)
    modified_on = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(255), nullable=False, default=SmartOrderStatus.OPEN.value)
    executed_on = db.Column(db.DateTime, nullable=True, default=None)
    change_reason =db.Column(db.String(255), nullable=True, default=None)


    def __init__(self,smart_order_type, exchange_id, exchange_order_id, sl_steps, userid, symbol,side, amt,price, order_details_json, task_id=None, modified_on=None, status="open", executed_on=None, change_reason=None):
        self.smart_order_type = smart_order_type
        self.exchange_id = exchange_id
        self.exchange_order_id = exchange_order_id
        self.sl_steps = sl_steps
        self.userid = userid
        self.task_id = task_id
        self.symbol = symbol
        self.side = side
        # self.order_type = order_type
        self.amt = amt
        self.price = price
        self.order_details_json = order_details_json
        self.created_on = datetime.datetime.utcnow()
        self.modified_on = modified_on
        self.status = status
        self.executed_on = executed_on
        self.change_reason = change_reason

    @classmethod
    def getOpenOrder(self):
        openOrders = db.session.guery(self).filter(self.status == "open").all()
        return openOrders
