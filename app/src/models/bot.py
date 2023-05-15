from sqlalchemy.orm import relationship
from app.src import db
from .helpers import BaseClass
from dataclasses import dataclass
class BotModel(BaseClass, db.Model):
    __tablename__ = "bot"

    id =  db.Column(db.Integer, primary_key=True, autoincrement= True)
    botName = db.Column(db.String(50), nullable=False, unique=True)
    symbol = db.Column(db.String(50), nullable=False)
    baseSymbol = db.Column(db.String(50), nullable=True)
    side = db.Column(db.String(50), nullable=True)
    orderType = db.Column(db.String(50), nullable=True)
    tradeAmt = db.Column(db.Float(), nullable=False)
    interval = db.Column(db.Integer, nullable=True)
    maxTradeCounts = db.Column(db.Integer, nullable=True)
    maxOrderAmt = db.Column(db.Float(), nullable=True)
    minOrderAmt = db.Column(db.Float(), nullable=True)
    price = db.Column(db.Float(), nullable=False)
    takeProfit = db.Column(db.Integer, nullable=True)
    stopLoss = db.Column(db.Integer, nullable=True)
    trailingStop = db.Column(db.Integer, nullable=True)
    callbackRate = db.Column(db.Float, nullable=True)
    leverage = db.Column(db.Integer, nullable=True)
    signalType = db.Column(db.String(50), nullable=True)
    botStatus = db.Column(db.Boolean, nullable=False, default=False)
    botType = db.Column(db.String(50), nullable=False)
    task_id = db.Column(db.String, nullable=True)
    
    # relationship with the user is one to many
    user_id = db.Column(db.Integer, db.ForeignKey("users.id",  ondelete="CASCADE"), nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchange.id"), nullable=True)
    # one to many relationship with the orders
    orders = relationship("OrdersModel", 
        backref="bot",
        cascade="all, delete",
        passive_deletes=True
        )

    def __init(self, botName, symbol, baseSymbol, side, orderType, tradeAmt, interval, maxTradeCounts, maxOrderAmt, minOrderAmt, price, takeProfit, stopLoss, trailingStop, callbackRate, leverage, signalType, botStatus, botType):
        self.boName = botName
        self.symbol = symbol
        self.baseSymbol = baseSymbol
        self.side = side
        self.orderType = orderType
        self.tradeAmt = tradeAmt
        self.interval = interval
        self.maxTradeCounts = maxTradeCounts
        self.maxOrderAmt = maxOrderAmt
        self.minOrderAmt = minOrderAmt
        self.price = price
        self.takeProfit = takeProfit
        self.stopLoss = stopLoss
        self.trailingStop = trailingStop
        self.callbackRate = callbackRate
        self.leverage = leverage
        self.signalType = signalType
        self.botStatus = botStatus
        self.botType = botType

    @classmethod
    def find_by_botname(cls, bot_name: str) -> "BotModel":
        return cls.query.filter_by(bot_name=bot_name).first()


@dataclass
class GridBotModel(BaseClass, db.Model):
    __tablename__="grid_bot"

    id:int
    botName:str
    symbol:str
    gridQty:float
    maxTradeCounts:int
    upperLimitPrice:float
    lowerLimitPrice:float
    gridQty:int
    qtyPerGrid:float
    exchange_id:int
    user_id:int
    is_running:bool
    task_id:str

     
    id = db.Column(db.Integer, primary_key=True)
    botName = db.Column(db.String(50))
    botType = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(50))
    gridQty = db.Column(db.Float)
    maxTradeCounts = db.Column(db.Integer)
    upperLimitPrice = db.Column(db.Float)
    lowerLimitPrice = db.Column(db.Float)
    is_running = db.Column(db.Boolean, nullable=False, default=False)
    gridQty =db.Column(db.Integer)
    qtyPerGrid = db.Column(db.Float)
    task_id = db.Column(db.String, nullable=True)
    gridPoints = db.Column(db.PickleType())
    exchange_id = db.Column(db.Integer, db.ForeignKey("exchange.id"), nullable=True)

    # relationship with the user is odddddddne to many
    user_id = db.Column(db.Integer, db.ForeignKey("users.id",  ondelete="CASCADE"), nullable=False)
    # botConfigs = db.Column(db.PickleType())
    @classmethod
    def create(cls, **kw):
        obj = cls(**kw)
        db.session.add(obj)
        db.session.commit()