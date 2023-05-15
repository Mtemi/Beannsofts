import json
from app.src.models import subscription
from flask import request
from flask_restx import Resource
from app.src.models.users import UserModel
from app.src.utils.dto import InvoiceDto
from app.src.controller import login_required

from app.src.services.paymentOperations import CoinBaseOperations

import datetime
from app.src.models.invoice import InvoiceModel
from app.src import db

api = InvoiceDto.api
invoice = InvoiceDto.invoice

from app.src.utils import logging
logger = logging.GetLogger(__name__)

@api.route('/invoice')
class Invoice(Resource):
    @api.doc('Subscribe to a subscription package')
    @api.expect(invoice, validate=True)
    def post(self):
        subscription = request.json['subscription']
        userId = request.json['userId']

        user = db.session.query(UserModel).filter_by(id=userId).first()
        userInfo = {
            "customerName": user.username, 
            "customerId": user.id,
            "customerEmail": user.email,
            "subscription": subscription
        }
        operation = CoinBaseOperations()
        invoice, planId = operation.createInvoice(subscription, userInfo)
        resp = {
            "status": "ok",
            "invoice": invoice.json()
        }
        logger.info(f"Invoice created for user {user.username} {invoice.json()}")
        emailData = {
            'subject': 'SUBSCRIPTION INVOICE',
            'to': userInfo['customerEmail'],
            'body': invoice.json()['data']['hosted_url']
        }
        invoiceParams = {
            "invoice_id": invoice.json()['data']['id'],
            "invoice_code": invoice.json()['data']['code'],
            "created_on": datetime.datetime.utcnow(),
            "invoice_status":  invoice.json()['data']['status'],
            "plan": subscription,
            "plan_id": planId,
            "modified_on": None,
            "user_id": user.id
        }

        invoice = InvoiceModel(**invoiceParams)
        db.session.add(invoice)
        db.session.commit()

        try:
            from app.tasks import sendAsyncMail
            mail =  sendAsyncMail.apply_async(args=(emailData,))
            return resp, 200
        except Exception as e:
            logger.exception("Invoice Mail not sent")
            return resp, 200