from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.src.config import config_by_name
from flask_cors import CORS
import os
from app.src.config import Config
from flask_mongoengine import MongoEngine
from flask_sse import sse


db = SQLAlchemy()
mdb = MongoEngine()


def create_app(config_name: str) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    app.config["REDIS_URL"] = Config.REDIS_URL
    app.register_blueprint(sse, url_prefix='/stream')
    # app.config['MONGODB_SETTINGS'] = {
    #     'host': Config.MONGODB_HOST+'/crypttops-3c?authSource=admin',
    # }
    CORS(app)
    db.init_app(app)
    app.config['MONGODB_CONNECT'] = False
    mdb.init_app(app)
    return app


app = create_app('dev')
