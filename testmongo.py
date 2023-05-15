

# from app.src.services.Notifications.logStore.models.mongoStore import MessageChannel, Message, MessageEvent
# message_details = {
#     "msg":"Grid bot starting",
#     "msg_type":"info",
#     "status":"read"
# }

# message = Message(**message_details)

# event = {"event_name":"grid-bot"}

# event_details = MessageEvent(message=[message], **event)

# print('event_details', event_details)

# # message_event = MessageEvent(message)

# message_saved = MessageChannel(**{'channel':0}, message_event=[event_details]).save()

# print(message_saved)

from app.src.services.Notifications.logStore.logOperations import LogStore
from app.src.services.Notifications.logStore.models.mongoStore import MessageChannel
import json

message_details = {
    "msg": "Dca bot starting",
    "msg_type": "info",
    "status": "unread"
}

logStore = LogStore()
# logStore.store(message=message_details, channel=0, eventName="dca-bot",
#                otherInfo={"detail": "This the test message for log store"})

# message = logStore.retrieveLogsByEvent(channel=0, eventName="grid-bot")
# print(type(message))
# print(json.dumps(json.loads(message), indent=4))

# logStore.modifyMessageStatus(
#     channel=0, eventName="dca-bot", timestamp=1642147346.404073, status="cleared")

# logStore.deleteAllUserLogs(channel=0)
x = logStore.deleteLogsbyTimestamp(
    channel=0, eventName="dca-bot", timestamp=1642155276.612386)


print(x)
