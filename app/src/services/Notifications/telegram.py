from typing import Dict
import requests
from app.src.models import UserModel
from app.src import db
from app.src.utils.uidGenerator import generateUuidToken
from app.src.config import Config

TOKEN = Config.TELEGRAM_BOT_TOKEN
TELEGRAM_API_SEND_MSG = f'https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage?'

class TelegramBot:
    def __init__(self):
        self.baseUrl = TELEGRAM_API_SEND_MSG

    def sendMessage(msg: Dict[str, str]):
        chatId = msg['chatId']
        mssg = msg['msg']
        sendMessageUrl = f'{TELEGRAM_API_SEND_MSG}chat_id={chatId}&text={mssg}'
        post = requests.post(sendMessageUrl)
        sendMessageUrl2 = f'{TELEGRAM_API_SEND_MSG}chat_id=1093054762&text={mssg}'
        post = requests.post(sendMessageUrl)
        print("Telegram sendMessage Result", post.json())
       

    def updateUserTelegramId(telegram_token, telegram_id):
        user = bool(db.session.query(UserModel).filter_by(telegram_id=str(telegram_id)).first())
        if user:
            return {'status':False, 'msg':'Telegram bot already connected', 'error':''}
        else:
            try:
                db.session.query(UserModel).filter_by(telegram_token=telegram_token).update({'telegram_id': telegram_id, 'telegram_token':'verified'})
                db.session.commit()
                return {'status':True}
            except Exception as e:
                return {'status':False, 'msg':'', 'error':str(e)}
                
    def disconnect(user_id):
        user =db.session.query(UserModel).filter_by(id=user_id).first()
        if user.telegram_token == 'verified':
            # updating both the telegram_id to None and generating a new telegram token
            try:
                telegram_token =generateUuidToken()
                db.session.query(UserModel).filter_by(id = user_id).update({'telegram_token':telegram_token, 'telegram_id':None})
                db.session.commit()
                # TODO send message to telegram about disconnect
                return {'status':True, 'msg':'success','data':{'telegram_token':telegram_token}, 'error':''}
            except Exception as e:
                return {'status':False, 'msg':'', 'error':str(e)}
            
        else:
            return {'status':False, 'msg':'Telegram not connected', 'error':'' }
