
from app.src import db
from .helpers import BaseClass


class OrdersModel(BaseClass, db.Model):
    __tablename__ = 'orders'

    # id =  db.Column(db.Integer, primary_key=True, autoincrement= True)
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    binance_order_id = db.Column(db.BigInteger, nullable=False)
    symbol = db.Column(db.String(50), nullable=False)
    clientOrderId = db.Column(db.String(50), nullable=True)
    transactTime = db.Column(db.BigInteger, nullable=True)
    price = db.Column(db.Float(), nullable=True)
    origQty = db.Column(db.Float(), nullable=True)
    executedQty = db.Column(db.Float(), nullable=True)
    cummulativeQuoteQty = db.Column(db.Float(), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    timeInForce = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(50), nullable=True)
    side = db.Column(db.String(50), nullable=True)
    fills = db.Column(db.PickleType(), nullable=True)
    created_on = db.Column(db.DateTime, nullable=True)
    avgPrice = db.Column(db.Float(), nullable=True)
    cumQty = db.Column(db.Float(), nullable=True)
    cumQuote = db.Column(db.Float(), nullable=True)
    reduceOnly = db.Column(db.Boolean, nullable=True)
    closePosition = db.Column(db.Boolean, nullable=True)
    positionSide = db.Column(db.String(50), nullable=True)
    stopPrice = db.Column(db.Float(), nullable=True)
    workingType = db.Column(db.String(50), nullable=True)
    priceProtect = db.Column(db.Boolean, nullable=True)
    origType = db.Column(db.String(50), nullable=True)
    updateTime = db.Column(db.BigInteger, nullable=True)
    exchange_type = db.Column(db.String(50), nullable=True)
    bot_id = db.Column(db.BigInteger, db.ForeignKey('bot.id',  ondelete="CASCADE"), nullable=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    def __init(self, binance_order_id, symbol, clientOrderId, transactTime, price, origQty,
                executedQty, cummulativeQuoteQty, status, timeInForce, type, side, fills, 
                created_on, avgPrice, cumQty, cumQuote, reduceOnly, closePosition,positionSide,
                stopPrice, workingType, priceProtect, origType, updateTime, exchange_type, bot_id, user_id):
        self.binance_order_id = binance_order_id
        self.symbol = symbol
        self.clientOrderId = clientOrderId
        self.transactTime = transactTime
        self.price = price
        self.origQty = origQty
        self.executedQty = executedQty
        self.cummulativeQuoteQty = cummulativeQuoteQty
        self.status = status
        self.timeInForce = timeInForce
        self.type = type
        self.side = side
        self.fills = fills
        self.created_on = created_on
        self.avgPrice = avgPrice
        self.cumQty = cumQty
        self.cumQuote = cumQuote
        self.reduceOnly = reduceOnly
        self.closePosition = closePosition
        self.positionSide = positionSide
        self.stopPrice = stopPrice
        self.workingType = workingType
        self.priceProtect = priceProtect
        self.origType = origType
        self.updateTime = updateTime
        self.exchange_type = exchange_type
        self.bot_id = bot_id
        self.user_id = user_id


    @classmethod
    def find_by_botId(cls, bot_id: str) -> "OrdersModel":
        return cls.query.filter_by(bot_id=bot_id).first()
