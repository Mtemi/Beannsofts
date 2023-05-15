from itsdangerous import exc
from app.src import db
from app.src.models.dcabot import DCABotOrderModel, DcaBotModel
from app.src.models.exchange import ExchangeModel
from app.src.models.orders import OrdersModel


class Pnl():
    def spotLongUnrealizedPnl(self, markingPrice, intialRate, positionSize):
        """ Long spot unrealized pnl"""
        unrealizedPnl = (markingPrice - intialRate)*positionSize
        percentage = unrealizedPnl/(intialRate*positionSize) * 100
        return {'unrealizedPnl': unrealizedPnl, 'percentage': percentage}

    def spotShortUnrealizedPnl(self, intialRate, markingPrice, positionSize):
        """Short spot unrealized pnl"""
        unrealizedPnl = (intialRate - markingPrice)*positionSize
        percentage = unrealizedPnl/(intialRate*positionSize) * 100

        return {'unrealizedPnl': unrealizedPnl, 'percentage': percentage}

    def marginUnrealizedPnl(self, intialRate, markingPrice, positionSize, leverage):
        """ Margin unrealized pnl"""
        unrealizedPnl = (((markingPrice - intialRate)
                         * positionSize)/leverage)*leverage
        percentage = unrealizedPnl/(intialRate*positionSize) * 100
        return {'unrealizedPnl': unrealizedPnl, 'percentage': percentage}

    def futuresLongUnrealizedPnl(self, markingPrice, intialRate, positionSize):
        """ Futures short unrealized pnl"""
        unrealizedPnl = (markingPrice - intialRate)*positionSize
        percentage = unrealizedPnl/(intialRate*positionSize) * 100
        return {'unrealizedPnl': unrealizedPnl, 'percentage': percentage}

    def futuresShortUnrealized(self, markingPrice, intialRate, positionSize):
        """Futures short unrealized pnl"""
        unrealizedPnl = (intialRate - markingPrice)*positionSize
        percentage = unrealizedPnl/(intialRate*positionSize) * 100
        return {'unrealizedPnl': unrealizedPnl, 'percentage': percentage}


def getBotTradeDetails(botId, userId, botType, exchangeId):

    exchange = db.session.query(ExchangeModel).filter_by(id=exchangeId).first()

    if botType == "dca":
        orders = db.session.query(DCABotOrderModel).filter_by(
            bot_id=botId, user_id=userId).all()

        print("orders", orders)
        openOrders = []

        # positionData = {

        #     'markingPrice': 110,
        #     'intialBuyRate': 35130,
        #     'positionSize': 10,
        #     'leverage': 10,
        #     'orderType': '',
        #     'side': '',
        #     'symbol':  ''

        # }
        for order in orders:
            price = order.price
            size = order.qty
            side = order.side

            order_data = {
                'intialRate': order.price,
                'positionSize': order.qty,
                'leverage': 10,
                'exchangeType': exchange.exchange_type,
                'side': order.side,
                'symbol': order.symbol
            }
            openOrders.append(order_data)

        return openOrders

    elif botType == "grid":
        db.session.query(DCABotOrderModel).filter_by(
            id=botId, user_id=userId).all()
