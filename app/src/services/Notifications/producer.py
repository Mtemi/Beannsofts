from flask import Flask, render_template
from flask_sse import sse
from app.src.config import Config
from app import app
from datetime import datetime

from app.src.services.Notifications.store.operations import NotificationStore


appContext = app.app_context()

sse_events = Config.SSE_EVENTS


def publishMessage(msg, msg_type, event_name, channel, **kwargs):
    """
    msg:type; string
    msg_type:type; string
    event_name:type; string

    Any other info dict: **kwargs={} or name = ''
    """

    # verification before publishing the message
    if msg_type == 'info' or msg_type == 'error':
        pass
    else:
        raise Exception(
            'Invalid message type\n allowed types are info or error')

    if event_name not in sse_events:
        raise Exception(
            f'{event_name} is not registered,\n Registered events are {sse_events}')

    message = {
        "msg_type": msg_type,
        "msg": msg,
        "status": "unread"
    }

    # Storing the log to mongodb
    notificationStore = NotificationStore()
    notificationStore.store(message=message, channel=channel,
                            eventName=event_name, otherInfo=kwargs)

    message.update(kwargs)

    appContext.push()
    # with app.app_context():

    sse.publish(message, type=event_name, channel=channel)

    appContext.pop()
