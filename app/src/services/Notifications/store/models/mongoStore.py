from app.src import app
from app.src import mdb as db
from flask_mongoengine import MongoEngine
from app.src.utils import logging

# db = MongoEngine(app)


class MessageKwargs(db.DynamicEmbeddedDocument):
    pass


class Message(db.EmbeddedDocument):
    msg = db.StringField()
    msg_type = db.StringField()
    status = db.StringField()
    time_added = db.DateTimeField()
    timestamp = db.FloatField()
    other_info = db.EmbeddedDocumentField(MessageKwargs)


class MessageEvent(db.EmbeddedDocument):
    event_name = db.StringField()
    message = db.EmbeddedDocumentListField(Message)


class MessageChannel(db.Document):
    channel = db.IntField()
    message_event = db.EmbeddedDocumentListField(MessageEvent)
