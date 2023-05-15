
import json

from itsdangerous import exc
from app.src.services.webhook.utils import decryptMessage, encryptMessage


class WebhookOps():

    def generateToken(self, userId, botId, symbol):
        """encrypts the data and generates token"""
        message = {
            "userId": userId,
            "botId": botId,
            "symbol": symbol
        }
        token = encryptMessage(json.dumps(message))

        return token.decode('utf-8')

    def decodeToken(self, token):
        """Decrypts data to obtain data"""
        try:
            data = decryptMessage(bytes(token, 'utf-8'))
            return json.loads(data)
        except Exception as e:
            print(e)
            return {"message": "fail", "error": str(e), "status": 400}

    def generateWebhookLink(self, baseUrl, userId, botId, symbol):
        """Generates the webhook url"""
        link = baseUrl+f"/{self.generateToken(userId, botId, symbol)}/signal"
        return link
