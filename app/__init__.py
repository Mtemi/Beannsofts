from app.src.models import UserModel, ExchangeModel, ExchangeEnum, OrdersModel, BotModel, PlansModel, SubscriptionModel, InvoiceModel, TerminalOrderModel, DCABotOrderModel, DcaBotModel, SmartOrdersModel, GridBotModel
from app.src import app, db

from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate


from flask_restx import Api
from flask import Blueprint

from app.src.controller.botApi import api as botNS
from app.src.controller.exchangeApi import api as excNS
from app.src.controller.userAuth import api as userNS
from app.src.controller.userAuth import api2 as authNS
from app.src.controller.OrderApi import api as orderNS
from app.src.controller.paymentApi import api as paymentNS
from app.src.controller.adminApi import api as adminNS
from app.src.controller.terminalOrdersApi import api as terminalOrdersNS
from app.src.controller.smartTradeApi import api as smartTradeNS
from app.src.controller.notificationApi import api as telegramNotifierNS
from app.src.controller.strategiesApi import api as strategiesNS
from app.src.controller.notificationApi import api2 as logsNS
from app.src.controller.webhookApi import api as webhookNS
from app.src.controller.accountsApi import api as accountsNS
blueprint = Blueprint('api', __name__)

apiDocsAuthorization = {
    'Basic Auth': {
        'type': 'basic',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(blueprint,
          version="1.0",
          title="Crypttops BITSGAP exchange trading bots API",
          description="Trading Bots working with Binance Spot Exchange",
          authorizations=apiDocsAuthorization,
          security='Bearer Auth'
          )

api.add_namespace(botNS, path='/bot')
api.add_namespace(excNS, path='/exchanges')
api.add_namespace(userNS, path='/users')
api.add_namespace(orderNS, path='/orders')
api.add_namespace(authNS)
api.add_namespace(paymentNS, path='/subscription')
api.add_namespace(adminNS, path='/admin')
api.add_namespace(terminalOrdersNS, path='/terminal')
api.add_namespace(smartTradeNS, path='/smart')
api.add_namespace(telegramNotifierNS, path='/telegram')
api.add_namespace(strategiesNS, path='/strategy')
api.add_namespace(logsNS, path='/notifications')
api.add_namespace(webhookNS, path='/webhook')
api.add_namespace(accountsNS, path='/accounts')

migrate = Migrate(app, db)
