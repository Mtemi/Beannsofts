from typing import Tuple, Dict
from app.src.models.bot import GridBotModel
from app.src.models.users import UserModel
from app.src.services.SubscriptionOperations import filterPlanActions, subscriptionType
from app.src.models.orders import OrdersModel
from flask_restx import Resource
from . import login_required
from flask import request, jsonify
from app.src.models import BotModel, ExchangeModel, DcaBotModel
from app.src import db
from app.src.services import BotOperations
from app.src.utils.dto import BotDto 
from app.src.utils import logging
from app.src.services import createOrderFromBot
from app.tasks import DCABotTask, startGridBot
from app.src.utils.helpers import serializerDB
import datetime
import json
import ast

logger = logging.GetLogger(__name__)

api = BotDto.api

gridbot = BotDto.gridbot
gridbotupdate=BotDto.gridbotupdate
dcabot = BotDto.dcabot
startGridBotDto = BotDto.startGridBot
botId = BotDto.botId
botOrder = BotDto.botOrder

@api.route('/grid/manual')
class GridBot(Resource):
    @api.doc('create GRID Bot')
    @api.expect(gridbot, validate=True)
    @login_required
    def post(self, user):
        """Create a GRID Bot config"""
        params = request.json
        userId = user.id
        params.update({'botType':'GRID'})

        subscription = subscriptionType(userId)
        print("The subscriptions, {}".format(subscription))
        if subscription:
            print(subscription.plan_id)
            # TODO fetch plan_action object from eger loaded subscription 
            planAction = filterPlanActions(subscription.plan_id)
            print("PLan Action {}".format(planAction))
            
            totalBots = db.session.query(GridBotModel).filter(GridBotModel.user_id == userId, GridBotModel.botType == "GRID").count()
            print("Total Bots, {}".format(totalBots))

            if totalBots >= planAction['bots'] and planAction['bots'] != 0:
                return {"message":"Request Denied, Upgrade your subscription", "status":403}, 200
            else:
                params['symbol'] = params['symbol'].upper() 
                params.update({"user_id":userId})
                if db.session.query(GridBotModel).filter(GridBotModel.botName == params["botName"]).first() is None:
                    bot = GridBotModel(**params)
                    db.session.add(bot)
                    db.session.commit()
                    
                    # The bot object jsonified the response the api response
                    #    
                    return jsonify(
                        {
                            "status": 200,
                            "message": "Grid Bot "+params["botName"]+ " created successfully",
                            "result":bot
                        })
                        
                else:
                    return {
                        "message": "The bot name already exits. Kindly update the bot name", 
                        "status": 301}, 301

    @api.doc('Edit GRID Bot')
    @api.expect(gridbotupdate, validate=True)
    @login_required
    def put(self, user):
        """Update a GRID Bot Configs"""
        params = request.json
        # print(params)
        userId = user.id
        params.update({'user_id':userId})
        bot = db.session.query(GridBotModel).filter(
            GridBotModel.id == params['id'], GridBotModel.user_id==userId).first()
        # print(bot)
        if bot is not None:
            del params['id']
            db.session.query(GridBotModel).filter(
            GridBotModel.id == bot.id).update(params)

            gridbot = params
            gridbot.update({"bot_id": bot.id})
            db.session.commit()
            return {"status": "ok", "message": "Bot updated", "result": gridbot}, 200

        else:
            return {"message": "The bot you tried to edit does not exist", "status": "fail"}, 400

    @api.doc('Delete GRID Bot')
    @api.doc(params={"bot_id":"bot_id"})
    # @api.expect(botId, validate=True)
    @login_required
    def delete(self, user):
        """Delete a DCA Bot"""
        # params = request.json
        botId = request.args.get("bot_id")
        userId = user.id
        bot = db.session.query(GridBotModel).filter(
            GridBotModel.id == botId).first()

        if bot is not None:
            botID = bot.id
            db.session.query(GridBotModel).filter(
                GridBotModel.id == botId).delete()
            db.session.commit()

            return {"status": "ok", "message": "Bot deleted"}, 200
        else:
            return {"message": "The bot you tried to delete does not exist", "status": 400}, 200

    @api.doc('Get a list of all user Grid Bots')
    @login_required
    def get(self, user):
        """Get a list of all Grid Bots for users"""
        userId = user.id
        bots = db.session.query(GridBotModel).filter(
            GridBotModel.user_id == userId).all()
        if bots:
            allUserBots = serializerDB(jsonify(bots))
            return {"status": "ok", "message": "Bots retrieved", "result": json.loads(allUserBots)}, 200
        else:
            return {"message": "No bots found","result":[], "status": "ok"}, 200

@api.route('/dca')
class DCABot(Resource):
    @api.doc('create new DCA Bot')
    @api.expect(dcabot, validate=True)
    @login_required
    def post(self, user):
        """Create a DCA Bot config"""
        params = request.json
        userId = user.id
        pairlist = str(list(params['pairlist']))
        params.update({'user_id': userId, 'botType': 'DCA', 'pairlist': pairlist})
        bot = DcaBotModel.find_by_botname(str(params['botname']))
        print(bot)
        if bot:
            return {"message": "The bot name already exits. Kindly update the bot name", "status": 301}, 301
        
        subscription = subscriptionType(userId)
        print("The subscriptions, {}".format(subscription))
        
        if subscription:
            print(subscription.plan_id)
            planAction = filterPlanActions(subscription.plan_id)
            print("PLan Action {}".format(planAction))

            totalBots = db.session.query(DcaBotModel).filter(
                DcaBotModel.user_id == userId, DcaBotModel.botType == "DCA").count()
            print("Total Bots, {}".format(totalBots))

            if totalBots >= planAction['bots'] and planAction['bots'] != 0:
                return {"message": "Request Denied, Upgrade your subscription", "status": 403}, 200
            else:
                if db.session.query(DcaBotModel).filter(DcaBotModel.botname == params["botname"]).first() is None:
                    params.update({"user_id":userId})
                    bot = DcaBotModel(**params)
                    db.session.add(bot)
                    db.session.commit()
                    dcabot = params
                    dcabot.update({"bot_id": bot.id, "leverage": bot.leverage})

                    return {"status": "ok", "message": "Bot created", "result": dcabot}, 200
                else:
                    return {"message": "The bot name already exits. Kindly update the bot name", "status": 301}, 301

    @api.doc('Edit DCA Bot')
    @api.expect(dcabot, validate=True)
    @login_required
    def put(self, user):
        """Update a DCA Bot Configs"""
        params = request.json
        bot = db.session.query(DcaBotModel).filter(
            DcaBotModel.id == params['id']).first()
         
        if bot is not None:
            print("Bot ID",bot.id)
            del params['id']
            db.session.query(DcaBotModel).filter(
            DcaBotModel.id == bot.id).update(params)

            db.session.commit()
            dcabot = params
            dcabot.update({"bot_id": bot.id})
            json.dumps(dcabot)

            return {"status": "ok", "message": "Bot updated", "result": dcabot}, 200

        else:
            return {"message": "The bot you tried to edit does not exist", "status": "fail"}, 400

    @api.doc('Delete DCA Bot')
    @api.doc(params={"bot_id":"bot_id"})
    # @api.expect(botId, validate=True)
    @login_required
    def delete(self, user):
        """Delete a DCA Bot"""
        print("calling delete function")
        botId = request.args.get("bot_id")
        userId = user.id
      
        bot = db.session.query(DcaBotModel).filter(
            DcaBotModel.id == botId).first()

        if bot is not None:
            botID = bot.id
            db.session.query(DcaBotModel).filter(
                DcaBotModel.id == botID, DcaBotModel.user_id ==userId).delete()
            db.session.commit()

            return {"status": "ok", "message": "Bot deleted"}, 200
        
        else:
            return {"message": "The bot you tried to delete does not exist", "status": 400}


    @api.doc('Get a list of all user DCA Bots')
    @login_required
    def get(self, user):
        userId = user.id
        """Get a list of all DCA Bots for users"""
        bots = db.session.query(DcaBotModel).filter(
            DcaBotModel.user_id == userId).all()
        if bots:
            allUserBots = serializerDB(jsonify(bots))
            return {"status": "ok", "message": "Bots retrieved", "result": json.loads(allUserBots)}, 200
        else:
            return {"message": "No bots found", "status":"ok", "result":[]}, 200
        
@api.route('/dca/start')
class startDCABot(Resource):
    @api.doc('Start DCA Bot')
    @api.expect(botId, validate=True)
    @login_required
    def post(self, user):
        """Start a DCA Bot"""
        botId = request.json['bot_id']
        userId = user.id
        bot = db.session.query(DcaBotModel).filter(DcaBotModel.id == botId).first()
        pairs = bot.pairlist
      
        user = db.session.query(UserModel).filter_by(id=userId).first()

        if bot is not None:
            params = serializerDB(jsonify(bot))
            print("The params", params)
            configs = json.loads(params)
            print("params, {}".format(configs))
            
            # pairs = ast.literal_eval(configs["pairlist"]) #convert string list to list
            pairs=configs["pairlist"]
        
            # print("pairs SINGLE, {}".format(pairs[1]))
            exchange = db.session.query(ExchangeModel).filter(ExchangeModel.id == bot.exchange_id).first()
            if exchange is not None:
                configs.update({'exchangename': exchange.exchange_name,
                                'key': exchange.key,
                                'secret': exchange.secret,
                                'operation': exchange.exchange_type,
                                'userid': userId,
                                'chatid':user.telegram_id,
                                'pairlist':pairs
                                })
                print("Configs, {}".format(configs))
            else:
                return {"message": "The exchange you tried to start the bot on is not active", "status": 400}, 400
            
            botInstance = DCABotTask.apply_async(args=(configs,))
            logger.debug("Bot Instance celery Task ID:  {}".format(botInstance.id))

            db.session.query(DcaBotModel).filter_by(id = bot.id).update({"task_id": botInstance.id, "is_running": True, "started_at":datetime.datetime.utcnow()})
            db.session.commit()
            return {"status": "ok","message": f"Bot {bot.botname} of id: {bot.id} started"}, 200
        else:
            return {"message": "The bot you tried to start does not exist", "status": 404}, 404
@api.route('/dca/stop')
class stopDCABot(Resource):
    @api.doc('Start DCA Bot')
    @api.expect(botId, validate=True)
    @login_required
    def post(self, user):
        """Start a DCA Bot"""
        botId = request.json['bot_id']
        userId = user.id
        bot = db.session.query(DcaBotModel).filter(
            DcaBotModel.id == botId).first()

        if bot is not None:
            taskID = bot.task_id
            task = DCABotTask.AsyncResult(taskID).revoke(terminate=True)

            db.session.query(DcaBotModel).filter_by(id = botId).update({"task_id": None, "is_running": False, "stopped_at":datetime.datetime.utcnow()})
            db.session.commit()
            logger.info(f"DCA bot of Id: {botId} for user: {userId} stopped")
            return {"message": "Bot stoped successfully", "status": "ok"}, 200
        else:
            return {"message": "The bot you tried to stop does not exist", "status": 404}, 404

@api.route('/grid/start')
class GridBotStart(Resource):
    @api.doc("start grid bot")
    @api.expect(botId, validate=True)
    @login_required
    def post(self, user):
        """Start a already configured bot - iniates a bot instance"""
        botId = request.json['bot_id']
        userId =user.id
        
        bot = db.session.query(GridBotModel).filter(GridBotModel.id == botId).first()
        
        if bot is not None:
            exchange = db.session.query(ExchangeModel).filter(ExchangeModel.id == bot.exchange_id).first()
            user = db.session.query(UserModel).filter_by(id=userId).first()
            params = {
                'user_id': int(userId),
                'bot_id':int(bot.id),
                'botName': bot.botName,
                'key': exchange.key,
                'secret': exchange.secret,
                'operation': exchange.exchange_type,
                'chatId': user.telegram_id
            }
            print(type(vars(bot)))
            params.update(vars(bot))

            
            print("The params", params)
            del params['_sa_instance_state']

            print("new params", params)
            botInstance = startGridBot.apply_async(args=(params,))

            db.session.query(GridBotModel).filter(
                GridBotModel.botName == bot.botName).update({GridBotModel.is_running: True, GridBotModel.task_id: botInstance.id})
            db.session.commit()
            logger.info(f"GRID bot started, ID: {botInstance.id}")
            return {"status": "ok", "message": "Bot Started", "result": {"botID": bot.id, "botName":bot.botName,'taskID': botInstance.id}}, 200
        
        else:
            logger.info("Bot does not exist")
            return {"status": "fail","message": "The specified bot does not exists. Create a bot to start"}, 400

@api.route('/grid/stop')
class stopGridBot(Resource):
    @api.doc('Stop Grid Bot')
    @api.expect(botId, validate=True)
    @login_required
    def post(self,user):
        """Start a DCA Bot"""
        botId = request.json['bot_id']
        bot = db.session.query(GridBotModel).filter(
            GridBotModel.id == botId, GridBotModel.user_id==user.id).first()

        if bot is not None:
            taskID = bot.task_id
            task = startGridBot.AsyncResult(taskID).revoke(terminate=True)

            db.session.query(GridBotModel).filter(
                GridBotModel.id == botId).update({GridBotModel.is_running: False, GridBotModel.task_id: None})
            db.session.commit()

            logger.info("bot stopped")
            return {"message": "Bot stoped successfully", "status": "ok"}, 200

@api.route('/all/list')
class ListBots(Resource):
    @api.doc("List all bots belonging to a user Resource")
    @api.param('userId', 'The user id')
    def get(self):
        """List all bots belonging to a user"""
        userId = request.args.get("userId")
        return BotOperations.queryAllBots(userId)

@api.route('/all/copy')
class CopyBot(Resource):
    @api.doc("Create a replica of an existing bot Resource")
    @api.expect(dcabot, validate=True)
    def post(self):
        """Create a replica of an existing bot"""
        BotId = request.json['bot_id']
        botName = request.json['botName']
        userId = request.json["userId"]
        return BotOperations.copyBot(self, userId, BotId, botName)
       
@api.route('/all/open/trade')
class OpenTrade(Resource):
    @api.doc("place a trade using the data from the bot")
    @api.expect(botOrder, validate=True)
    def post(self):
        botId = request.json['bot_id']
        userId = request.json["userId"]
        orderRes = createOrderFromBot(userId, botId)
        return orderRes

@api.route('/record/orders')
class saveBotOrders(Resource):
    def post(self):
        data = request.json
               
        order = OrdersModel(**data)

        db.session.add(order)
        db.session.commit()
        return {"status": "ok"}, 200


@api.route('/dca/list/orders')
class listBotOrders(Resource):
    @api.doc("List all orders belonging to a dca bot")
    @api.param('botId', 'The bot id')
    def get(self) -> Tuple[Dict[str, str], int]:
        """List all orders belonging to a dca bot"""
        botId = request.args.get("botId")
        return BotOperations.queryAllDcaBotOrders(botId)
