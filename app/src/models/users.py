from app.src import db
from .helpers import BaseClass
from sqlalchemy.orm import relationship


class UserModel(BaseClass, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    registered_on = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    # phone_no = db.Column(db.String(80), unique=True, nullable=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    telegram_token = db.Column(db.String(80),nullable=False)
    telegram_id = db.Column(db.String(80))
    exchange = relationship("ExchangeModel",
                            backref="users",
                            cascade="all, delete",
                            passive_deletes=True
                            )
    
    bots = relationship("BotModel",
                        backref="users",
                        cascade="all, delete",
                        passive_deletes=True
                        )

    orders = relationship("OrdersModel",
                          backref="users",
                          cascade="all, delete",
                          passive_deletes=True
                          )

    subscription = relationship(
        'SubscriptionModel', backref='users', cascade="all, delete", uselist=False, lazy=True)
    
    terminalorder = relationship(
        'TerminalOrderModel', backref='users', cascade="all, delete", uselist=False, lazy=True)

    dcabot = relationship("DcaBotModel",
                            backref="users",
                            cascade="all, delete",
                            passive_deletes=True
    )
    
    def __init__(self,registered_on, email, username, password, telegram_token, telegram_id=None):
        self.registered_on = registered_on
        self.email = email
        self.username = username
        self.password = password
        self.telegram_token = telegram_token
        self.telegram_id = telegram_id

    @classmethod
    def find_by_username(cls, username: str) -> "UserModel":
        return cls.query.filter_by(username=username).first()
