from app.src.services.strategiesOperations import getStategyNames

from ..utils.dto import StrategiesDto

from app.src.services.Notifications.Notification import Notification
from flask_restx import Resource
from app.src.config import Config

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import request
api = StrategiesDto.api
import os

strategyUploadFolder = Config.STRATEGY_FOLDER
strategyAllowedExtensions = Config.STRATEGY_ALLOWED_EXTENSIONS


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in strategyAllowedExtensions


@api.route('')
class StratergyResorce(Resource):
    @api.doc("Get the available strategies")
    def get(self):   
        strategies = getStategyNames(str(strategyUploadFolder))
        return strategies

    @api.doc("Loading the strategy file")
    def post(self):
        try:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(strategyUploadFolder, filename))

                return {
                    "message": f"Strategy *{filename[:-3:]}* uploaded successfully",
                    "status":201
                },201
            else:
                return {
                    "message":f"incorrect strategy file format, the allowed formats are {strategyAllowedExtensions}",
                    "status":400
                }
        except Exception as e:
            return {
                "message":"Error uploading the strategy file",
                "error":str(e),
                "status":400
            }
