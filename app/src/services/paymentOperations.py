from app.src.models.invoice import InvoiceModel
from app.src.utils.coinbase.coinbase import CoinBaseInvoice
from coinbase_commerce.client import Client
from app.src.config import Config

from app.src import db
from app.src.models import PlansModel

from app.src.utils import logging
logger = logging.GetLogger(__name__)
class CoinBaseOperations():
    def __init__(self):
        self.CoinBaseClinet = Client(Config.COINBASE_KEY)
        self.CoinBaseInvoice =  CoinBaseInvoice(Config.COINBASE_KEY)
    
    def subscriptionPlanDetails(self, subscription):
        plan = db.session.query(PlansModel).filter(PlansModel.plan == subscription).first()
        if plan:
            description = plan.description
            planId = plan.id
            packageDetails = {
                "amount": plan.price,
                "currency":"USD"
            }
            print("Package Details", packageDetails)
            return packageDetails, description, planId

    def getInvoiceInfo(self, subscription, userDetails):
        packageDetails, description, planId = self.subscriptionPlanDetails(subscription)
        invoiceParams = {
            "business_name": "Crypttops 3c",
            "customer_email": userDetails['customerEmail'],
            "customer_name": userDetails['customerName'],
            "name": "PACKAGE SUBSCRIPTION",
            "description": description,
            "pricing_type": "fixed_price",
            "metadata": {
                "customer_id": userDetails['customerId'],
                "customer_name": userDetails['customerName']
            },
            "local_price": packageDetails,
            "memo": description
        }
        return invoiceParams, planId

    def createInvoice(self, subscription, userDetails):
        invoiceParams, planId = self.getInvoiceInfo(subscription, userDetails)
        try:
            response = self.CoinBaseInvoice.createInvoice(invoiceParams)
            logger.info(f"invoice response, {response}")
            return response, planId
        except Exception as e:
            logger.exception("Invoice Exception {}".format(str(e)))
            return str(e)