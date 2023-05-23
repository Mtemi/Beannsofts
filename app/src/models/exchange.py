import enum
from .helpers import BaseClass
from app.src import db
import datetime

class ExchangeEnum(enum.Enum):
    SPOT = 'binance'
    FUTURES = 'binance-futures'
    
class StatusEnum(enum.Enum):
    ACTIVE = 'active'
    DELETED = 'deleted'
    
class ExchangeModel(BaseClass, db.Model):
    __tablename__ = "exchange"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_on = db.Column(db.DateTime, nullable=False)
    modified_on = db.Column(db.DateTime)
    exchange_name = db.Column(db.String(50), unique=True, nullable=False)
    key = db.Column(db.String(255), nullable=False)
    secret = db.Column(db.String(255), nullable=False)
    exchange_type = db.Column(db.String(), nullable=True, default=ExchangeEnum.SPOT.value)
    status = db.Column(db.String(50), nullable=True, default = StatusEnum.ACTIVE.value)

    # # relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',  ondelete="CASCADE"), nullable=False)
    # user = db.relationships('users', backref('exchange', lazy=True))

    def __init__(self, exchange_name, key, secret, user_id, modified_on, exchange_type, status):
        self.created_on = datetime.datetime.now()
        self.exchange_name = exchange_name
        self.key = key
        self.secret = secret
        self.user_id = user_id
        self.modified_on = modified_on
        self.exchange_type = exchange_type
        self.status = status

    @classmethod
    def find_by_exchange_name(cls, exchange_name: str) -> "ExchangeModel":
        return cls.query.filter_by(usernexchange_nameame=exchange_name).first()
