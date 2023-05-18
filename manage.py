
from flask.cli import FlaskGroup
from itsdangerous import exc

from app.src.models import UserModel, ExchangeModel, ExchangeEnum, OrdersModel, BotModel, PlansModel, SubscriptionModel, InvoiceModel, TerminalOrderModel, DCABotOrderModel, GridBotModel

# ADITIONALAS

from app.src.services.BotOperations import createBotOrderWebhook
from flask_restx import Resource
from app.src.config import Config, DevelopmentConfig

import datetime
from flask import request
from flask_socketio import SocketIO, emit

from coinbase_commerce.client import Client
from coinbase_commerce.webhook import Webhook
from coinbase_commerce.error import SignatureVerificationError, WebhookInvalidPayload

from flask_mail import Mail, Message
from flask_cors import CORS

from app.src.models import InvoiceModel
from app.src.services import OrderOperations
from app.src.services.pnl.pnlcalculator import pnlCalcualtor
from app.src.services.pnl.utils import getBotTradeDetails

from app.src.utils import logging
from app import api, app, db, blueprint

logger = logging.GetLogger(__name__)

# ORiginal stuff begins here

app.register_blueprint(blueprint)

app.app_context().push()

# FIXME Extra stuff needs to be refactored to meet reviewed architecture of app
mail = Mail(app)

# Instantiating websocket
socketio = SocketIO(app, cors_allowed_origins="*")

CORS(app, resources={r"/*": {"origins": "*"}}, support_credentials=True)

cli = FlaskGroup(app)


def listen():
    """This method queries get symbolData and filters last BTC Price"""
    """THe method emits realtime BTC lastprice to the clientside UI"""
    while True:
        lastPrice = OrderOperations.getSymbolLastPrice()
        socketio.emit('BTCPrice', {'price': lastPrice}, broadcast=True)
        socketio.sleep(1)


@socketio.on('getBTCPrice')
def handle_connect():
    """Each time a websocket event getBtcPrice is passed it emits BTC lastprice"""
    listen()


def listenPnlData(botId, userId, botType, exchangeId):

    openOrders = getBotTradeDetails(
        botId=botId, userId=userId, botType=botType, exchangeId=exchangeId)

    print(openOrders)
    pnl = 0
    while True:
        pnl = 0
        for open_order in openOrders:
            resp = pnlCalcualtor(positionData=open_order,
                                 botId=botId, userId=userId)

            pnl += float(resp['unrealizedPnl'])
        # resp = pnlCalcualtor()
        socketname = "pnl"+botType+str(botId)

        print(resp)

        print(socketname)
        socketio.emit(socketname,
                      {'data': pnl}, broadcast=True)
        socketio.sleep(1)


@socketio.on('pnl')
def handlePnlData(data):
    print(data)
    botId = data['botId']
    userId = data['userId']
    botType = data['botType']
    exchangeId = data['exchangeId']

    print(botId, userId)

    if botType == 'grid':
        # TODO
        pass
    if botType == 'dca':
        # Get all the dca method
        listenPnlData(botId, userId, botType, exchangeId)


@app.route('/bot/webhook', methods=['POST'])
def respond():
    data = request.json

    botID = data['bot_id']
    userID = data['user_id']

    print(request.json)
    try:
        createBotOrderWebhook(botID)
    except Exception as e:
        error = {
            "msg": "DCA WEbhook order error",
            "error": str(e),
            "user_id": userID,
            "bot_id": botID
        }
        socketio.emit(error['user_id'], {'error': error}, broadcast=True)

    return "success", 200


@app.route('/invoices/webhook', methods=['POST'])
def invoiceWebhook():
    # event payload
    request_data = request.data.decode('utf-8')
    # webhook signature
    request_sig = request.headers.get('X-CC-Webhook-Signature', None)

    try:
        # signature verification and event object construction
        event = Webhook.construct_event(
            request_data, request_sig, Config.COINBASE_WEBHOOK_SECRET)
    except (WebhookInvalidPayload, SignatureVerificationError) as e:
        return str(e), 400

    logger.info("Received event: id={id}, type={type}".format(
        id=event.id, type=event.type))

    if "created" in event.type:
        invoiceUpdate = {
            "invoice_status":  event.type,
            "modified_on": datetime.datetime.utcnow(),
        }
        logger.info("paid invoice event")
        invoice = db.session.query(InvoiceModel).filter(
            InvoiceModel.invoice_id == event.data['id']).first()
        # print(invoice)
        if invoice is not None:
            print("inside invoice")
            db.session.query(InvoiceModel).filter(
                InvoiceModel.invoice_id == event.data['id']).update(invoiceUpdate)
            db.session.commit()

            # INITIATLIZE AND ACTIVATE THE SUBSCRIPTION
            subscriptionStartDate = datetime.datetime.utcnow(),
            subscriptionExpiryDate = datetime.datetime.utcnow() + datetime.timedelta(days=+30)

            subscription = {
                "start_date": subscriptionStartDate,
                "expiry_date": subscriptionExpiryDate,
                "is_active": True,
                "plan_id": invoice.plan_id
            }

            db.session.query(SubscriptionModel).filter(
                SubscriptionModel.user_id == invoice.user_id).update(subscription)
            # subscription = SubscriptionModel(**subscription)
            # db.session.add(subscription)
            db.session.commit()

            emailData = {
                "subject": "Payment Successfully Verified",
                "to": event.data.customer_email,
                #"body": f"Subscription Expiry Date: {subscriptionExpiryDate}, Plan: {invoice.plan}"
            }
            # Send acknowledgeent of Payment
            sendAsyncMail(emailData)

    return 'success', 200


@api.route('/bot/record/error')
class BotError(Resource):
    def post(self):
        error = request.json
        logger.info("Bot error emited")
        socketio.emit(error['userId'], {'error': error}, broadcast=True)
        return 200

# Cronjobs for background tasks
# TODO create a cronjob/ celery task from this method


def sendAsyncMail(emailData):
    """Background task to send an email with Flask-Mail."""
    msg = Message(emailData['subject'],
                  sender=Config.MAIL_DEFAULT_SENDER,
                  recipients=[emailData['to']])
    msg.body = emailData['body']
    with app.app_context():
        logger.info("async background email sent")
        mail.send(msg)


def sendMail(emailData, app):
    """Background task to send an email with Flask-Mail."""
    msg = Message(emailData['subject'],
                  sender=Config.MAIL_DEFAULT_SENDER,
                  recipients=[emailData['to']])
    msg.body = emailData['body']
    with app.app_context():
        logger.info("email sent")
        mail.send(msg)


if __name__ == '__main__':
     # socketio.run(app, host='0.0.0.0', port=3010)   
     cli()

