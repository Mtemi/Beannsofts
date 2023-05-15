from app.src.models.subscription import SubscriptionModel
import datetime
from datetime import timedelta
from app.src import db

def setExpiryDate(startDate):
    """Returns the subscripion expiry date. Subscritip expires after 30 days"""
    return startDate + timedelta(days=+30)

def subscriptionReminder(subscriptionEndDate):
    """ Returns TRUE if 3 days are remaining before expiry else FALSE"""
    today = datetime.datetime.utcnow()
    remainder = subscriptionEndDate - today
    if remainder > timedelta(days=0) and remainder < timedelta(days=+3):
        return True
    else:
        return False

def querySubscriptionExpiry():
    """Returns subscriptions details that have expired"""
    today = datetime.datetime.utcnow()
    return db.session.query(SubscriptionModel).filter(SubscriptionModel.expiry_date <= today, SubscriptionModel.is_active == True).all()

def changeSubscriptionStatus(subscriptionId):
    """Changes the subscription status IS_ACTIVE from True to False"""
    db.session.query(SubscriptionModel).filter(SubscriptionModel.id == subscriptionId).update(SubscriptionModel.is_active == False)
    db.session.commit()

def subscriptionType(userId):
    sub = db.session.query(SubscriptionModel).filter(SubscriptionModel.user_id == userId, SubscriptionModel.is_active == True).first()
    db.session.commit()
    return sub

def filterPlanActions(planId):
    if planId == 1:
        return {
            'plan': "FREE",
            'bots': 1,
            'exchanges': 1
        }
    elif planId == 2:
        return {
            'plan': "STARTER",
            'bots': 1,
            'exchanges': 5
        }
    elif planId == 3:
        return {
            'plan': "ADVANCED",
            'bots': 0,
            'exchanges': 10
        }
    elif planId == 4:
        return {
            'plan': "PREMIUM",
            'bots': 0,
            'exchanges': 0
        }
    else: 
        return {
            'plan': "INVALID PLAN"
        }
