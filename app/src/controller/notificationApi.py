from flask_restx import Resource
from flask import jsonify, request
from app.src.services.Notifications.store.operations import NotificationStore

from app.src.utils.dto import TelegramNotifierDto, LogsDto
from app.src.services.Notifications.telegram import TelegramBot

from telegram import Update
import json
from app.src.controller.userAuth import login_required
from app.src.config import Config


api = TelegramNotifierDto.api
telegramDto = TelegramNotifierDto.telegramDto

api2 = LogsDto.api
logStatusDto = LogsDto.logStatusDto


@api.route('/webhook/add/user')
class TelegramNotification(Resource):
    @api.doc("Extract a users telegram id to be used by Telegram Bot to forward messages")
    def post(self):
        """Extract a users telegram id to be used by Telegram Bot to forward messages"""
        event = request.json
        text = json.dumps(event, indent=4)
        # print(text)
        # retrieve the message in JSON and then transform it to Telegram object
        # update = Update.de_json(request.json, bot)

        # chat_id = update.message.chat.id
        # msg_id = update.message.message_id

        # # Telegram understands UTF-8, so encode text for unicode compatibility
        # text = update.message.text.encode('utf-8').decode()
        # # for debugging purposes only
        # print("got text message :", text)
        # the first time you chat with the bot AKA the welcoming message

        user_telegram_data = event['message']['chat']
        command_text = event['message']['text']

        if "/start" in command_text:
            # print the welcoming message
            bot_welcome = """
            Welcome to User Notification Bot.
            """
            # Spliting the the command from token
            command_text_list = command_text.split()

            # print(command_text_list)
            try:
                token = command_text_list[1]
                msg = {
                    "msg": f'{token}\n{bot_welcome}',
                    "chatId": user_telegram_data['id']
                }

                # send the welcoming message
                resp = TelegramBot.updateUserTelegramId(
                    token, user_telegram_data['id'])
                print("RESP:====", resp)
                print("IF ZERO")

                if resp['status'] == True:
                    TelegramBot.sendMessage(msg)
                    print("IF ONE")
                # Already updated to the dabase or a non error response
                elif resp['status'] == False and resp['msg'] != '':
                    msg = {
                        "msg": resp['msg'],
                        "chatId": user_telegram_data['id']
                    }
                    TelegramBot.sendMessage(msg)
                    print("IF TWO")
                else:
                    # Error response the but printed ---database exceptions
                    print(resp)
                    print("IF THREE")
                    # print(token)

            except Exception as e:
                print("Something missing check the link, use link website", e)

        return 'ok'


@api.route('/disconnect')
class DisconnectTelegram(Resource):

    @api.doc("Disconnect Telegram")
    @api.param('userId', 'The user identifier')
    def put(self, userId):
        resp = TelegramBot.disconnect(userId)
        if resp['status'] == True:
            return {'message': 'success', 'data': {'link': Config.TELEGRAM_BOT_BASE_URL+resp['data']['telegram_token']}, 'status': 200}

        elif resp['status'] == False and resp['msg'] != '':
            return {'message': 'Telegram not connected', 'status': 400}


# notification store Endpoints
@api2.route('/')
class Notifications(Resource):
    @api2.doc(params={'ch': 'message channel'})
    def get(self):
        channel = request.args.get('ch')
        print(channel)
        notificationStore = NotificationStore()
        resp = notificationStore.retrieveAllNotifications(channel)
        return jsonify(resp)

    @api.expect(logStatusDto, validate=True)
    def put(self):
        params = request.json
        notificationStore = NotificationStore()
        resp = notificationStore.modifyNotificationStatus(
            channel=params['channel'], eventName=params['eventName'], timestamp=params['timestamp'], status=params['status'])
        if resp != None:
            return resp, 200
        else:
            return {"message": "fail", "error": "An error occured while modifying the message use the correct timestamp", "status": 400}

    @api2.doc(params={'ch': 'message channel', 'evnt': 'event name', 'tsmp': 'message timestamp'})
    def delete(self):
        channel = request.args.get('ch')
        timestamp = request.args.get('tsmp')
        eventName = request.args.get('evnt')

        notificationStore = NotificationStore()
        resp = notificationStore.modifyNotificationStatus(
            channel=channel, eventName=eventName, timestamp=float(timestamp), status='cleared')
        if resp != None:
            return resp, 200
        else:
            return {"message": "fail", "error": "An error occured while modifying the message use the correct timestamp", "status": 400}


@api2.route('/all')
class DeleteAllNotifications(Resource):
    @api2.doc(params={'ch': 'message channel'})
    def delete(self):
        channel = request.args.get('ch')
        notificationStore = NotificationStore()
        resp = notificationStore.ClearAllUserNotifications(channel)
        if resp != None:
            return resp, 200
        else:
            return {"message": "fail", "error": "An error occured while modifying the message use the correct timestamp", "status": 400}
