from app.src.models import PlansModel
from flask import request
from flask_restx import Resource
from app.src.controller import login_required
from app.src.utils.dto import SubscriptionPlanDto
from app.src import db

from app.src.utils import logging
 
logger = logging.GetLogger(__name__)

api = SubscriptionPlanDto.api
plan = SubscriptionPlanDto.plan


@api.route('/subscription/package/add')
class SubscriptionPackage(Resource):
    @api.doc('create subscription package plan')
    @api.expect(plan, validate=True)
    def post(self):
        """create subscription package plan"""
        data = request.json
        try:
            plan = PlansModel(**data)
            db.session.add(plan)
            db.session.commit()

            return 200
        except Exception as e:
            db.session.rollback()
            logger,Exception("Subscription Plan Creation ERROR {}".format(e))
            return {'message': "Error: {}".format(str(e))},200

