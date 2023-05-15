from flask import jsonify, request
from flask_restx import Resource
from app.src.config import Config
from app.src.services.webhook.operations import WebhookOps
from app.src.utils import logging
from app.src.utils.dto import WebhookDto
from app.src.services.DCABot.DCABot import DCABot
from app.src.models import DcaBotModel, UserModel, ExchangeModel
from app.src.utils.helpers import serializerDB
from app.src import db
import datetime
import json
import ast

logger = logging.GetLogger(__name__)

api = WebhookDto.api

userBotId = WebhookDto.userBotId


@api.route('/<string:token>/signal')
class WebhookSignal(Resource):
    def post(self, token):
        """
        TradingView Webhook to process the Signal for DCA Bot
        """
        webhookops = WebhookOps()
        data = webhookops.decodeToken(token)
       
        userID =  data['userId']
        botID = data['botId']
        tradingPair = data['symbol']


        logger.debug(f"WebhookSignal: for userID {userID}, BotID {botID}")

        bot =  DcaBotModel.find_by_botId(botID)
 
        if bot is not None:
            pairs = bot.pairlist
      
            user = db.session.query(UserModel).filter_by(id=userID).first()
            params = serializerDB(jsonify(bot))
            configs = json.loads(params)
            
            pairs = ast.literal_eval(configs["pairlist"]) #convert string list to list
        
            # print("pairs SINGLE, {}".format(pairs[1]))
            exchange = db.session.query(ExchangeModel).filter(ExchangeModel.id == bot.exchange_id).first()

            if exchange is not None:
                configs.update({'exchangename': exchange.exchange_name,
                                'key': exchange.key,
                                'secret': exchange.secret,
                                'operation': exchange.exchange_type,
                                'userid': user.id,
                                'chatid':user.telegram_id,
                                'pairlist':pairs
                                })
                # print("Configs, {}".format(configs))
            else:
                return {"message": "The exchange you tried to start the bot on is not active", "status": 400}, 400
            
            dcaBot = DCABot(configs)

            # CREATE ORDER USING THE CONFIGS FOR A SINGLE PAIR
            qty = dcaBot._config['qty']


            # Getting trading pair precision for both quantiy and price
            assetPrecision = dcaBot.getAssetPrecision(tradingPair)
            logger.debug(f"The asset precisions found {assetPrecision}")

            # Calculating the current price for asset
            lastPrice = dcaBot.exchange.round_decimals_down(dcaBot.getSymbolLastPrice(tradingPair), assetPrecision['pricePrecision'])

            # Calculating the correct quantity for use in binance order
            stakeAmt = dcaBot.exchange.round_decimals_down(dcaBot.getQuantityInQuoteAsset(qty, lastPrice), assetPrecision['qtyPrecision'])
            
            # Execute Order
            ordertype = dcaBot._config['ordertype']
            side = dcaBot._config['side']
            logger.debug(f"Executing buy from signal")
            nowtime = datetime.datetime.now()
            createStatus = dcaBot.executeOrder(tradingPair, side, ordertype, stakeAmt, nowtime)
            logger.debug(f"Executed order from TradingView signal botID: {botID}, userID: {userID}, side: {side}, ordertype: {ordertype}, stakeAmt: {stakeAmt}, tradingPair: {tradingPair}, response: {createStatus}")

        return "Success"


@api.route('/link')
class Webhook(Resource):
    @api.doc("generate the telegram webhook link")
    @api.expect(userBotId, validate=True)
    def post(self):
        userId = request.json['userId']
        botId = request.json['botId']
        symbol = request.json['symbol']
        webhookops = WebhookOps()
        try:
            url = webhookops.generateWebhookLink(
                baseUrl=Config.WEBHOOK_URL, userId=userId, botId=botId, symbol=symbol)
            return {"message": "success", "webhookURL": url, "status": 200}, 200
        except Exception as e:
            logger.error(f"failed error {str(e)}")
            return{"message": "fail", "status": 400}
