from app.src import db
from .helpers import BaseClass
from sqlalchemy.orm import relationship

import datetime

class PlansModel(BaseClass, db.Model):
    __tablename__ = "subscription_plans"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    plan =  db.Column(db.String(50), nullable=False, unique=True)
    features = db.Column(db.PickleType(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    price = db.Column(db.Float(), nullable=False)


    subscription = relationship(
        'SubscriptionModel', backref='subscriptions', cascade="all, delete", uselist=False, lazy=True)
    
    def __init__(self, plan, features, description, price):
        self.plan = plan
        self.features = features
        self.description = description
        self.price = price

class SubscriptionModel(BaseClass, db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow())
    expiry_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    plan_id = db.Column(db.BigInteger, db.ForeignKey('subscription_plans.id', ondelete="CASCADE"), nullable=False)
    user_id =  db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)