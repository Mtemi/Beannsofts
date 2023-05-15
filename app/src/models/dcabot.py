from dataclasses import dataclass
from app.src import db
from .helpers import BaseClass
from datetime import datetime
from sqlalchemy.orm import relationship

@dataclass
class DcaBotModel(BaseClass, db.Model):
    __tablename__ = 'dca_bot'

    id: int = db.Column(db.Integer, primary_key=True)
    botname: str = db.Column(db.String(255), nullable=False)
    botType: str = db.Column(db.String(), nullable=False)
    side: str = db.Column(db.String(50), nullable=True)
    pairlist: str = db.Column(db.PickleType(), nullable=False)
    ordertype: str = db.Column(db.String(50), nullable=True)
    qty: int = db.Column(db.Integer, nullable=False) 
    leverage: int = db.Column(db.Integer, nullable=True, default=10)
    stoploss: float = db.Column(db.Float, nullable=True)
    takeprofit: float = db.Column(db.Float, nullable=True)
    trailing_stop: float = db.Column(db.Float, nullable=True)
    takeprofit: float = db.Column(db.Float, nullable=True)
    trailing_stop_enabled: bool = db.Column(db.Boolean, nullable=True)
    strategy: str = db.Column(db.String(255), nullable=False)
    timeframe:str = db.Column(db.String(255), nullable=False)
    interval_between_orders: int = db.Column(db.Integer, nullable=True, default=None)
    order_timeout: int = db.Column(db.Integer, nullable=True)
    max_active_trade_count: int = db.Column(db.Integer,nullable=True, default=1)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    deleted_at: datetime = db.Column(db.DateTime, default=None, nullable=True)
    is_running: bool = db.Column(db.Boolean, nullable=False, default=False)
    started_at: datetime = db.Column(db.DateTime, default=None, nullable=True)
    stopped_at: datetime = db.Column(db.DateTime, default=None, nullable=True)
    is_deleted: bool = db.Column(db.Boolean, nullable=False, default=False)
    task_id: str = db.Column(db.String, nullable=True, default=None)

    # relationship with the user is one to many
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id",  ondelete="CASCADE"), nullable=False)
    exchange_id: int  = db.Column(db.Integer, db.ForeignKey("exchange.id"), nullable=True)
    # one to many relationship with the orders
    
    dca_orders = relationship("DCABotOrderModel", 
        backref="dca_bot",
        cascade="all, delete",
        passive_deletes=True
    )

    @classmethod
    def create(cls, **kw):
        obj = cls(**kw)
        db.session.add(obj)
        db.session.commit()

    @classmethod
    def find_by_botId(cls, bot_id: int) -> "DcaBotModel":
        return cls.query.filter_by(id=bot_id).first()

    @classmethod 
    def find_by_botname(cls, botname: str) -> "DcaBotModel":
        return cls.query.filter_by(botname=botname).first()
        
@dataclass
class  DCABotOrderModel(BaseClass, db.Model):
    __tablename__ = 'dca_orders'

    id: int
    order_id: int
    bot_id: int
    user_id: int
    symbol: str
    price: float
    order_type: str
    side: str
    qty: float
    leverage: int
    price: float
    status: str
    is_open: bool
    filled_amt: float
    remaining_amt: float
    order_date: str
    order_filled_date: str
    order_update_date: str

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.BigInteger, nullable=True)
    bot_id = db.Column(db.BigInteger, db.ForeignKey('dca_bot.id',  ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    symbol = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    order_type = db.Column(db.String(50), nullable=False)
    qty = db.Column(db.Float(), nullable=False)
    leverage = db.Column(db.Integer, nullable=True, default=10)
    side = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=True)
    is_open = db.Column(db.Boolean, nullable=False, default=False)
    filled_amt = db.Column(db.Float(), nullable=True)
    remaining_amt = db.Column(db.Float(), nullable=True)
    order_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow())
    order_filled_date = db.Column(db.DateTime, nullable=True)
    order_update_date = db.Column(db.DateTime, nullable=True)
    order_timeout = db.Column(db.DateTime, nullable=True)

    @classmethod
    def create(cls, **kw):
        obj = cls(**kw)
        db.session.add(obj)
        db.session.commit()

    @classmethod
    def find_by_botId(cls, bot_id: int) -> "DCABotOrderModel":
        return cls.query.filter_by(bot_id=bot_id).first()

    @classmethod
    def find_by_open_order(cls, bot_id: int) -> "DCABotOrderModel":
        return cls.query.filter_by(is_open = True, bot_id=bot_id).all()

    @classmethod
    def find_by_userId(cls, user_id: int) -> "DCABotOrderModel":
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def cancel_order(cls, order_id:int) -> "DCABotOrderModel":
        db.session.query.filter_by(order_id= order_id).update({"is_open":False, "status":"Timeout Cancelled" })
        db.session.commit()

    @classmethod
    def cancel_bot_open_orders(cls, bot_id:int) -> "DCABotOrderModel":
        cls.query.filter_by(bot_id=bot_id).update({"is_open":False})
        # db.session.add(records)
        db.session.commit()

    @classmethod
    def get_open_bot_orders(cls, bot_id:int):
        records = cls.query.filter_by(bot_id=bot_id, is_open=True).all()
        return records

