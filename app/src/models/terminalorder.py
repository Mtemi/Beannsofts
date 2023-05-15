from app.src import db
from enum import Enum
import datetime
from app.src.models.helpers import BaseClass

class TerminalOrderStatus(Enum):
    OPEN = "open"
    CANCELED = "cancelled"
    FILLED = "filled"

class TerminalOrderModel(BaseClass, db.Model):
    """
    Trade database model.
    Also handles updating and querying trades
    """
    __tablename__ = 'terminal_trades'

    id = db.Column(db.Integer, primary_key=True)
    exchange_id = db.Column(db.BigInteger, db.ForeignKey("exchange.id"), nullable=False)
    userid = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    symbol = db.Column(db.String(25), nullable=False)
    side = db.Column(db.String(), nullable=False)   
    type = db.Column(db.String(25), nullable=False)
    unit = db.Column(db.Float(), nullable=False) 
    amt = db.Column(db.Float(),nullable=False)
    price = db.Column(db.Float(),nullable=False)
    timeinforce = db.Column(db.String(25),nullable=True)
    leverage = db.Column(db.Integer, nullable=True)
    targetprice = db.Column(db.Float(), nullable=True)
    triggerprice = db.Column(db.Float(), nullable=True)
    timeout = db.Column(db.Integer, nullable=True)
    trailing = db.Column(db.Float(), nullable=True)
    created_on = db.Column(db.DateTime, nullable=False)
    modified_on = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(255), nullable=False, default=TerminalOrderStatus.OPEN.value)
    executed_on = db.Column(db.DateTime, nullable=True, default=None)
    change_reason =db.Column(db.String(255), nullable=True, default=None)
    taskid = db.Column(db.String(255), nullable=True, default=None)


    def __init__(self, exchange_id, userid, symbol, type, side, amt, unit, price, timeinforce, leverage, targetprice, triggerprice, timeout, trailing, modified_on, status, executed_on, change_reason, taskid):
        self.exchange_id = exchange_id
        self.userid = userid
        self.symbol = symbol
        self.type = type
        self.side = side
        self.amt = amt
        self.unit = unit
        self.price = price
        self.timeinforce = timeinforce
        self.leverage = leverage
        self.targetprice = targetprice
        self.triggerprice = triggerprice
        self.timeout = timeout
        self.trailing = trailing
        self.created_on = datetime.datetime.utcnow()
        self.modified_on = modified_on
        self.status = status
        self.executed_on = executed_on
        self.change_reason = change_reason
        self.taskid = taskid

    @classmethod
    def getOpenOrder(self):
        openOrders = db.session.guery(self).filter(self.status == "open").all()
        return openOrders

    









