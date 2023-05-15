
from datetime import datetime
from typing import Dict
from app.src.services.Notifications.store.utils import serializeJsonified
from app.src.utils import logging
from app.src.services.Notifications.store.models.mongoStore import MessageKwargs, Message, MessageEvent, MessageChannel
from flask import jsonify
from app.src import app
import json

logger = logging.GetLogger(__name__)


class NotificationStore():
    storedEvents = []
    # CREATE

    def store(self, message: Dict, channel: int, eventName: str,  otherInfo: Dict):
        """Builds up the the data mongo engine models and saves the data document."""

        data = MessageChannel.objects(channel=channel).first()

        if bool(data):

            # check all the available events
            for i in range(len(data.message_event)):
                self.storedEvents.append(data.message_event[i].event_name)

            # check the incoming event if its already registered
            if eventName in self.storedEvents:
                for i in range(len(data.message_event)):
                    if data.message_event[i].event_name == eventName:
                        otherInfo = MessageKwargs(**otherInfo)
                        now = datetime.utcnow()
                        message.update(
                            {'time_added': now, 'timestamp': now.timestamp()})
                        message = Message(**message, other_info=otherInfo)
                        data.message_event[i].message.append(message)
                        data.save()
                        logger.info(
                            f"{channel} - {eventName} message updated successfully")

                        break
            else:
                # Event not resgistered. creating a new event
                now = datetime.utcnow()
                message.update(
                    {'time_added': now, 'timestamp': now.timestamp()})

                otherInfo = MessageKwargs(**otherInfo)
                message = Message(**message, other_info=otherInfo)
                eventName = {"event_name": eventName}
                messageEvent = MessageEvent(message=[message], **eventName)
                data.message_event.append(messageEvent)
                data.save()

        else:
            # Register a new channel.
            now = datetime.utcnow()
            message.update({'time_added': now, 'timestamp': now.timestamp()})
            channel = {"channel": channel}
            otherInfo = MessageKwargs(**otherInfo)
            message = Message(**message, other_info=otherInfo)
            eventName = {"event_name": eventName}
            messageEvent = MessageEvent(message=[message], **eventName)
            messageChannel = MessageChannel(
                **channel, message_event=[messageEvent]).save()

            logger.info(f"{channel} - {eventName} message saved successfully")

    def retrieveAllNotifications(self, channel):
        """
        Retrieves all the logs/notifications excluding the cleared messages
        """
        data = MessageChannel.objects(channel=channel).first()

        if bool(data):

            # filter all the cleared logs/notifications
            message_event1 = data.message_event

            print(len(message_event1[:]))
            # utilize copy mechanism
            for msgevent in range(len(message_event1[:])):
                for msg in message_event1[msgevent].message[:]:
                    if msg.status == 'cleared':
                        message_event1[msgevent].message.remove(msg)

            with app.app_context():
                notificationMessages = serializeJsonified(
                    jsonify(message_event1))

            logger.info(
                f"{channel} notifications fetched successfully")

            return {"message": "success", "data": json.loads(notificationMessages), "status": 200}

        else:
            logger.info(f"{channel} does not exist")
            return {"message": "fail", "error": f"no logs for user {channel}", "status": 200}

    def retrieveNotificationsByEvent(self, channel, eventName):
        pass

    def retrieveNotificationsByEventStatus(channel, event, status):

        pass

    def modifyNotificationStatus(self, channel, eventName, timestamp, status):
        """ Changing the state of the message to either read or cleared"""

        data = MessageChannel.objects(channel=channel).first()
        if bool(data):
            for i in range(len(data.message_event)):
                self.storedEvents.append(data.message_event[i].event_name)

            # check the incoming event if its already registered
            if eventName in self.storedEvents:
                for i in range(len(data.message_event)):
                    if data.message_event[i].event_name == eventName:

                        for j in range(len(data.message_event[i].message)):
                            if data.message_event[i].message[j].timestamp == timestamp:
                                data.message_event[i].message[j].status = status
                                data.save()
                                logger.info(
                                    f"{channel} - {eventName} notifications updated successfully")
                                return {"message": "success", "status": 200}

            else:
                return {"message": "fail", "error": f"notifications  for {eventName}", "status": 400}
        else:
            logger.info(f"{channel} - {eventName} does not exist")
            return {"message": f"no notification for user {channel}"}

    def deleteNotificationbyTimestamp(self, channel, eventName, timestamp):
        """Deleting the notifications by timestamp"""

        data = MessageChannel.objects(channel=channel).first()
        if bool(data):
            for i in range(len(data.message_event)):
                self.storedEvents.append(data.message_event[i].event_name)

            # check the incoming event if its already registered
            if eventName in self.storedEvents:
                for i in range(len(data.message_event)):
                    if data.message_event[i].event_name == eventName:

                        for j in range(len(data.message_event[i].message)):
                            if data.message_event[i].message[j].timestamp == timestamp:
                                data.message_event[i].message.pop(j)
                                data.save()
                                logger.info(
                                    f"{channel} - {eventName} notification deleted by timestamp successfully")
                                break

            else:
                return {"message": "fail", "error": f"no notifications for {eventName}", "status": 400}
        else:
            logger.info(f"{channel} - {eventName} does not exist")
            return {"message": f"no notification for user {channel}"}

        pass

    def deleteNotificationsByEvent(self, channel, eventName):
        """Deleting all the notifications logs of specific event"""

        data = MessageChannel.objects(channel=channel).first()
        if bool(data):
            for i in range(len(data.message_event)):
                self.storedEvents.append(data.message_event[i].event_name)

            if eventName in self.storedEvents:
                for i in range(len(data.message_event)):
                    if data.message_event[i].event_name == eventName:
                        data.message_event.pop(i)
                        data.save()
                        logger.info(
                            f"notification for {channel} {eventName} cleared successfully")
                        break
        else:
            logger.info(f"{channel} - {eventName} does not exist")
            return {"message": f"no notification for user {channel}"}

    def deleteAllUserNotifications(self, channel):
        """
        Delete all user notifications
        """
        data = MessageChannel.objects(channel=channel).first()
        if bool(data):
            data.delete()
            logger.info(f"{channel} notifications cleared successfully")
            return {"message": f"{channel} cleared successifully"}

        else:
            logger.info(f"{channel} does not exist")
            return {"message": f"no notification for user {channel}"}

    def ClearAllUserNotifications(self, channel):
        """
        Change the status of all messages to cleared
        """
        data = MessageChannel.objects(channel=channel).first()
        if bool(data):
            for i in range(len(data.message_event)):
                for j in range(len(data.message_event[i].message)):
                    data.message_event[i].message[j].status = "cleared"
            data.save()

            logger.info(f"{channel} notifications cleared successfully")
            data = serializeJsonified(jsonify(data))
            return {"message": "success", "data": json.loads(data), "status": 200}

        else:
            logger.info(f"{channel} does not exist")
            return {"message": f"no notification for user {channel}"}
