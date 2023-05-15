from app.src.models import ExchangeModel
from app.src import db

def verifyExchange(user_id,exchange_type, exchange_id):
    exchange = db.session.query(ExchangeModel).filter_by(user_id=user_id, id=exchange_id, exchange_type=exchange_type).first()
    if exchange:
        user_data ={
            "user_id":user_id,
            "api_key": exchange.key,
            "api_secret":exchange.secret,
            "exchange_type": exchange_type
        }
        
        return {"status":True, "user_data":user_data}
    else:
        return {"status":False, "user_data":None}