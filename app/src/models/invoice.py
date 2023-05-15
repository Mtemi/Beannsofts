from app.src import db
from .helpers import BaseClass

class InvoiceModel(BaseClass, db.Model):
    __tablename__ = "invoices"

    invoice_id =  db.Column(db.String(50), nullable=False, primary_key=True)
    invoice_code = db.Column(db.String(50), nullable=False)
    created_on = db.Column(db.DateTime, nullable=True)
    invoice_status = db.Column(db.String(50), nullable=False)
    plan = db.Column(db.String(50), nullable=True)
    modified_on = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    plan_id = db.Column(db.BigInteger, db.ForeignKey('subscription_plans.id', ondelete="CASCADE"), nullable=False)

    def __init(self, invoice_id, invoice_code, created_on, invoice_status, plan, modified_on, user_id):
        self.invoice_id = invoice_id
        self.invoice_code = invoice_code
        self.created_on = created_on
        self.invoice_status = invoice_status
        self.plan = plan
        self.modified_on = modified_on
        self.user_id = user_id