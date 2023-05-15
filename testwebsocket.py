import socketio
from app.src import app
from app.src.services.pnl.utils import getBotTradeDetails

# # standard Python
sio = socketio.Client()

sio.connect('http://localhost:5000')


@sio.event
def connect():
    print("I'm connected!")


@sio.event
def connect_error(data):
    print("The connection failed!")


@sio.event
def disconnect():
    print("I'm disconnected!")


sio.emit('pnl', {'botId': 10, 'userId': 2, 'botType': 'dca', 'exchangeId': 1})


@sio.on('pnldca10')
def pnldca10(data):
    print("printon socket", data)

# with app.app_context():
#     x = getBotTradeDetails(botId=10, userId=2, botType='dca')
#     print(x)
