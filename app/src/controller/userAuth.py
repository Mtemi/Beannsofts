"""
The user operations:
***Registration
***Login

"""
from app.src.models import SubscriptionModel
from flask_restx import Resource, abort
from flask import request
import jwt
import re
import datetime
import functools
from app.src.models import UserModel
from werkzeug.security import generate_password_hash, check_password_hash
# import config
from time import gmtime, strftime
from app.src import db
from flask import current_app as app

from ..utils.dto import UserDto
from ..utils.dto import AuthDto
from app.src.utils.uidGenerator import generateUuidToken

api = UserDto.api
user = UserDto.user

# def subscription_required(method):
#     @functools.wraps(method, user)
#     def wrapper(self, user):
#         # header = request.headers.get('Authorization')
#         # _, token = header.split()
        
#         # decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
       
#         # email = decoded['email']
        
#         # user = UserModel.query.filter_by(email = email).all()[0]
#         subscription = db.session.query(SubscriptionModel).filter_by(user_id = user.id).first()
#         print(subscription)
#         if subscription:
#             if subscription.is_active == False:
#                 return {'message':'Expired Subscription', 'status':400}
#             return method(self, user, subscription)
#         return {'message':'No Subscription', 'status':400}
#     return wrapper

def login_required(method):
    @functools.wraps(method)
    def wrapper(self):
        header = request.headers.get('Authorization')
        try:
            _, token = header.split()
        except:
            return{"message": "Token is missing or invalid","status": 401}, 401
        try:
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
        except jwt.DecodeError:
            return {'message':'Token is not valid.', 'status':400}
        except jwt.ExpiredSignatureError:
            return {'message':'Token is expired.', 'status': 400}
        email = decoded['email']
        if len(UserModel.query.filter_by(email = email).all()) == 0:
            return {'message':'User is not found.', 'status':400}
        user = UserModel.query.filter_by(email = email).all()[0]
        return method(self, user)
    return wrapper

@api.route('/register')
class Register(Resource):
    @api.doc('register a user')
    @api.expect(user, validate=True)
    def post(self):
    	# get the details needed to register
    	# email, username, password, api_key, api_secret,inviter_id
        email = request.json['email']
        username = request.json['username']
        password = request.json['password']        
        # Saving RAW the data received to the db, no filtering

        data = {
            "email": email,
            "username":username,
            "password":generate_password_hash("password"),
            "telegram_token":generateUuidToken(),
            "registered_on": strftime("%Y-%m-%d %H:%M:%S", gmtime())
        }
        try:
            user = UserModel(**data)
            db.session.add(user)
            db.session.commit()

            print("lodadada")
            subscription = {
                    "start_date": datetime.datetime.utcnow(),
                    "expiry_date": None,
                    "is_active": True,
                    "plan_id": 1,
                    "user_id": user.id
                }
            subs = SubscriptionModel(**subscription)
            db.session.add(subs)
            db.session.commit()
            return {
                "results":{'username':username,'email': email}, 
                'mesage':'sucessifuly registed',
                'status':201
            },200
        except Exception as e:
            print(e)
            return {"results":str(e)}, 200
    
       
api2 = AuthDto.api
auth = AuthDto.auth

@api.route('/login')
class Login(Resource):
    @api2.doc('Login a user')
    @api2.expect(auth, validate=True)
    def post(self):
        email = request.json['email']
        password = request.json['password']
        if len(UserModel.query.filter_by(email = email).all()) == 0:
            return {'message':'User is not found.','status':400}
        user = UserModel.query.filter_by(email = email).all()[0]

        print("--------------------------user------------------------\n", user)
        
        #if not check_password_hash(user.password, password):
        #    return {'message':'Wrong Password.', 'status':400},200

        exp = datetime.datetime.utcnow() + datetime.timedelta(hours=app.config['TOKEN_EXPIRE_HOURS'])
        encoded = jwt.encode({'email': email,'userid':user.id, 'exp': exp}, app.config['SECRET_KEY'], algorithm='HS256')

        return { 'message':'login sucessifuly', "results":{'username':user.username, 'email': email, 'userID':user.id, 'telegram_bot_url':app.config['TELEGRAM_BOT_BASE_URL']+user.telegram_token, 'token': encoded.decode('utf-8')},'status':200}, 200
