import time
from typing import List
import requests
import json

from flask_mail import Mail, Message
from celery import Celery
from celery.schedules import crontab
from app.src.config import Config

from app.src.services.DCABot.DCABot import DCABot
from app.src.services.GridBot.GridBot import GridBot

from app.src.utils import logging
from app.src.services.TerminalOrders.TerminalOrder import TerminalOrderer

from app.src.services.SmartTrades.SmartBuy.tradeExecuter import *
from app.src.services.SmartTrades.SmartSell.tradeExecuter import smartSellExecutor
from app.src.services.SmartTrades.SmartCover.tradeExecutor import smartCoverExecutor
from app.src.services.SmartTrades.SmartTrade.tradeExecutor import smartTradeExecutor

from app.src.services.SubscriptionOperations import querySubscriptionExpiry, changeSubscriptionStatus
from app import app
import redis
import pickle


logger = logging.GetLogger(__name__)

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL,
                backend=Config.CELERY_BROKER_URL)

mail = Mail(app)
appContext = app.app_context()
redisConn = redis.from_url(Config.REDIS_URL)

bookTickerStreams = Config.BOOKTICKER_STREAMS

apiKey = Config.STREAMER_SERVICE_API_KEY
apiSecret = Config.STREAMER_SERVICE_API_SECRET

# CRONJOB THAT EXECUTES EVERY 3 HOURS
celery.conf.beat_schedule = {
    "checkSubscriptionEveryDay": {
        "task": "app.tasks.checkSubscriptionExpiry",
        "schedule":  crontab(minute=0, hour='*/3')
    },
    "getKline5min": {
        "task": "app.tasks.getKline5min",
        "schedule":  crontab(minute='*/5')
    },
    "getKline30min": {
        "task": "app.tasks.getKline30min",
        "schedule":  crontab(minute='*/30')
    },
    "getKline1h": {
        "task": "app.tasks.getKline1h",
        "schedule":  crontab(minute='*/60')
    },
    "getKline4h": {
        "task": "app.tasks.getKline4h",
        "schedule":  crontab(minute=0, hour='*/4')
    },
    "getKline1d": {
        "task": "app.tasks.getKline1d",
        "schedule":  crontab(minute=0, hour=0)
    }
    # "getKline1w": {
    #     "task": "app.tasks.getKline1w",
    #     "schedule":  crontab(minute='*/10080')
    # },
    # "getKline1m": {
    #     "task": "app.tasks.getKline1m",
    #     "schedule":  crontab(minute='*/43200')
    # },
    # "getKlineAll": {
    #     "task": "app.tasks.getKlineAll",
    #     "schedule":  crontab(minute='*/43200')
    # }
}
    
@celery.task(bind=True)
def getKline5min(self):
    logger.info("Started Kline 5min task")
    for symbol in Config.KlineSymbols5m:
        try:
            # logger.info("Getting Kline 5min for symbol: %s", symbol)
            response = requests.get(
                "https://api.binance.com/api/v1/klines?symbol=" + symbol.upper() + "&interval=5m&limit=1")
            if response.status_code == 200:
                kline5min = response.json()[0]
                redisConn.lpush(symbol+"@5m", pickle.dumps(kline5min))
                # logger.info("Kline 5min for symbol: %s updated , kline is: %s", symbol, kline5min)
            else:
                logger.error("Error while getting Kline 5min for symbol: %s", symbol)
        except Exception as e:
            logger.error("Error while getting Kline 5min for symbol: %s error %s", symbol, e)
    logger.info("Finished Kline 5min task")
    
@celery.task(bind=True)
def getKline30min(self):
    logger.info("Started Kline 30min task")
    for symbol in Config.KlineSymbols30m:
        try:
            # logger.info("Getting Kline 30min for symbol: %s", symbol)
            response = requests.get(
                "https://api.binance.com/api/v1/klines?symbol=" + symbol.upper() + "&interval=30m&limit=1")
            if response.status_code == 200:
                kline30min = response.json()[0]
                redisConn.lpush(symbol+"@30m", pickle.dumps(kline30min))
                # logger.info("Kline 30min for symbol: %s updated , kline is: %s", symbol, kline30min)
            else:
                logger.error("Error while getting Kline 30min for symbol: %s", symbol)
        except Exception as e:
            logger.error("Error while getting Kline 30min for symbol: %s error %s", symbol, e)
    logger.info("Finished Kline 30min task")

@celery.task(bind=True)
def getKline1h(self):
    logger.info("Started Kline 1hour task")
    for symbol in Config.KlineSymbols1h:
        try:
            # logger.info("Getting Kline 30min for symbol: %s", symbol)
            response = requests.get(
                "https://api.binance.com/api/v1/klines?symbol=" + symbol.upper() + "&interval=1h&limit=1")
            if response.status_code == 200:
                kline1h = response.json()[0]
                redisConn.lpush(symbol+"@1h", pickle.dumps(kline1h))
                # logger.info("Kline 1h for symbol: %s updated , kline is: %s", symbol, kline30min)
            else:
                logger.error("Error while getting Kline 1hour for symbol: %s", symbol)
        except Exception as e:
            logger.error("Error while getting Kline 1hour for symbol: %s error %s", symbol, e)
    logger.info("Finished Kline 1hour task")


@celery.task(bind=True)
def getKline4h(self):
    logger.info("Started Kline 4 hour task")
    for symbol in Config.KlineSymbols4h:
        try:
            # logger.info("Getting Kline 30min for symbol: %s", symbol)
            response = requests.get(
                "https://api.binance.com/api/v1/klines?symbol=" + symbol.upper() + "&interval=4h&limit=1")
            if response.status_code == 200:
                kline4h = response.json()[0]
                redisConn.lpush(symbol+"@4h", pickle.dumps(kline4h))
                # logger.info("Kline 1h for symbol: %s updated , kline is: %s", symbol, kline30min)
            else:
                logger.error("Error while getting Kline 4 hour for symbol: %s", symbol)
        except Exception as e:
            logger.error("Error while getting Kline 4 hour for symbol: %s error %s", symbol, e)
    logger.info("Finished Kline 4 hour task")

@celery.task(bind=True)
def getKline1d(self):
    logger.info("Started Kline 1 day task")
    for symbol in Config.KlineSymbols1d:
        try:
            # logger.info("Getting Kline 30min for symbol: %s", symbol)
            response = requests.get(
                "https://api.binance.com/api/v1/klines?symbol=" + symbol.upper() + "&interval=1d&limit=1")
            if response.status_code == 200:
                kline4h = response.json()[0]
                redisConn.lpush(symbol+"@1d", pickle.dumps(kline4h))
                # logger.info("Kline 1h for symbol: %s updated , kline is: %s", symbol, kline30min)
            else:
                logger.error("Error while getting Kline 1 day for symbol: %s", symbol)
        except Exception as e:
            logger.error("Error while getting Kline 1 day for symbol: %s error %s", symbol, e)
    logger.info("Finished Kline 1 day task")

@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 10})
def DCABotTask(self, configs):
    appContext.push()
    logger.info("DCABotTask started")
    dcaBot = DCABot(configs)
    dcaBot.cleanup()
    dcaBot.startup()
    while dcaBot.isActive:
        # dcaBot.cleanup()
        # logger.info(f"DCA Bot is being canceleed... BOTID: {dcaBot._config['id']}")
        dcaBot.process()

    #     dcaBot.process()
    #     if dcaBot.count >= 2 :
    #         dcaBot.cleanup()
    #         logger.info(f"DCA Bot is being canceleed... BOTID: {dcaBot._config['id']}")
    #         dcaBot.Active = False
            
    #     logger.info("DCABotTask finished")
    appContext.pop()


@celery.task(bind=True)
def startGridBot(self, params):
    # print("Printing gridbot params", params)

    symbol = params['symbol']

    logger.info("Cleared all the previously stored positions. Starting the bot",)

    bot = GridBot(params)
    tickerName = symbol.lower()+'@bookTicker'

    # Starting the bot a fresh clear all the previous saved positions
    postionStoredListKey = params['botName']+tickerName
    redisConn.delete(postionStoredListKey)

    with app.app_context():
        bot.pricePointsCalculator()

        while True:
            logger.info(f"getting data from {tickerName}")
            price_data = redisConn.get(tickerName)

            # print("The price data is ", price_data)

            if price_data is None:
                print("price_data is none")
                pass
            else:
                price_data = pickle.loads(price_data)
                current_price = float(price_data['data']['b'])

                logger.info("[X] {0} price:{1}".format(
                    price_data['data']['s'], current_price))
                bot.trader(current_price, params['botName']+tickerName)
                time.sleep(10)


@celery.task(bind=True)
def checkSubscriptionExpiry(self):
    """Check and cancel expired subscriptions"""
    try:
        appContext.push()
        expiredSubscriptions = querySubscriptionExpiry()
        for item in expiredSubscriptions:
            changeSubscriptionStatus(item.id)
            logger.info(
                "subscription cancelled for userID: ---{}".format(item.id))
        appContext.pop()

    except Exception as e:
        logger.exception("Error! Check Subscription Expiry, {}".format(e))
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery.task(bind=True)
def startConditionalTerminalOrder(self, params):
    try:
        termOrder = TerminalOrderer(params)
        termOrder.startUp()
        return "Task Completed"
    except Exception as e:
        logger.exception("Error! Conditional Order, {}".format(e))
        raise self.retry(exc=e, countdown=10, max_retries=3)

@celery.task()
def smartBuyTrade(configs):
    print("smartBuyTrade celery Task")
    print(configs)
    # Do the smart buy trade checks and the set conditions are met execute trades on binance futures account
    appContext.push()
    # this can be useful for the persistence of the websockets
    smartBuyExecutor(configs)
    appContext.pop()
    return "[X] Stopped the execution waiting for other tasks to finish"

@celery.task()
def smartSellTrade(configs):
    print("smartSellTrade celery Task")
    print(configs)
    appContext.push()
    smartSellExecutor(configs)
    appContext.pop()
    return "[X] Stopped the execution waiting for other tasks to finish"


@celery.task()
def smartCoverTrade(configs):
    # Do the smart buy trade checks and the set conditions are met execute trades on binance futures account
    appContext.push()
    print(configs)
    smartCoverExecutor(configs)
    appContext.pop()
    return "[X] Stopped the execution waiting for other tasks to finish"


@celery.task()
def smartTrade(configs):
    # Do the smart buy trade checks and the set conditions are met execute trades on binance futures account
    appContext.push()
    print(configs)
    smartTradeExecutor(configs)
    appContext.pop()
    return "[X] Stopped the execution waiting for other tasks to finish"


@celery.task(bind=True)
def sendAsyncMail(self, emailData):
    """Send Email in the background"""
    try:
        appContext.push()
        msg = Message(emailData['subject'],
                      sender=Config.MAIL_DEFAULT_SENDER,
                      recipients=[emailData['to']])
        msg.body = emailData['body']
        logger.info("async background email sent")
        mail.send(msg)
        appContext.pop()

    except Exception as e:
        logger.exception("Error! Mail Sending Fail, {}".format(e))
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(
        15.0, startPriceStreams.s(bookTickerStreams, apiKey, apiSecret), name='bookTicker every 15s')


@celery.task()
def startPriceStreams(streams: List[str], api_key, api_secret):
    # Update the bookTicker price of the trading symbols
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    bookTicker = []

    def handle_socket_message(price_data):
        print("price data at startPriceStreams", price_data)
        redisConn.set(price_data['stream'], pickle.dumps(price_data))
        bookTicker.append(price_data)
        if len(bookTicker) >= len(streams):
            logger.info(
                f"price_data  value is {price_data} ...")
                # f"BookTicker for {streams} updated successifully, restarting task...")
            twm.stop()

    twm.start()

    twm.start_multiplex_socket(
        callback=handle_socket_message, streams=streams)


if __name__ == '__main__':
    celery.start()
