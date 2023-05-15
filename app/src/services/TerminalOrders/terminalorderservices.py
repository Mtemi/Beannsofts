from app.src.services.BinanceFuturesOpeartions import BinanceFuturesOps
from app.src.services.binanceoperations import BinanceOps
from app.src import db
from app.src.models import TerminalOrderModel, ExchangeModel

from app import app

ctx = app.app_context()

class OrderOps:
    def getExchangeInfo(exchangeId: int) -> None:
        exchangeInfo = db.session.query(ExchangeModel).filter(ExchangeModel.id == exchangeId).first()
        return exchangeInfo

    def getExchangeInfoByName(exchange_name: str) -> None:
        exchangeInfo = db.session.query(ExchangeModel).filter(ExchangeModel.exchange_name == exchange_name).first()
        return exchangeInfo
    
    def getOpenOrder(orderId: int) -> None:
        """Returns order details"""
        ctx.push()
        openOrder = db.session.query(TerminalOrderModel).filter(TerminalOrderModel.id == orderId).first()
        ctx.pop()
        return openOrder
    
    def updateOrderDetails(orderId: int, orderDetails: dict()) -> None:
        ctx.push()
        db.session.query(TerminalOrderModel).filter(TerminalOrderModel.id == orderId).update(orderDetails)
        db.session.commit() 
        ctx.pop()

class ExchangeResolver:
    def loadExchange(orderParams: dict()):
        if orderParams["exchangeInfo"]["exchangeType"] == "binance":
            exchange = BinanceOps(api_key=orderParams["exchangeInfo"]["key"], api_secret=orderParams["exchangeInfo"]["secret"], trade_symbol=orderParams["symbol"])
            return exchange

        if orderParams["exchangeInfo"]["exchangeType"] == "binance-futures":
            exchange = BinanceFuturesOps(api_key=orderParams["exchangeInfo"]["key"], api_secret=orderParams["exchangeInfo"]["secret"], trade_symbol=orderParams["symbol"])
            return exchange

        return None