from typing import Dict

from app.src.services.Notifications.telegram import TelegramBot
from app.src.services.Notifications import producer
from app import app

from app.src.utils import logging

logger = logging.GetLogger(__name__)

appContext = app.app_context()
class Notification:
    """This class performs the tasks of sending telegram notifications and events to the frontend application"""
    def sendNotification(self, config):
        appContext.push()
        msg = config["msg"]
        msgType = config["msgType"]
        eventName = config["eventName"]
        channel = config["channel"]
        kwargs = config["kwargs"]
        chatId = config["chatId"]
         
        if chatId == None:
            producer.publishMessage(msg, msgType, eventName, channel, **kwargs)
            logger.info("Only SSE message sent {}".format(config))
        else:
            producer.publishMessage(msg, msgType, eventName, channel, **kwargs)
            TelegramBot.sendMessage(config)
            logger.info("Telegram and SSE message sent {}".format(config))
           
        appContext.pop()