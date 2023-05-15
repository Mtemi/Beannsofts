import requests
import json

class CoinBaseInvoice():
    def __init__(self, API_KEY) -> None:
        self.API_KEY = API_KEY
        self.API_URL = 'https://api.commerce.coinbase.com'
        self.API_VERSION = '2018-03-22'
        self.HEADERS = {
            'Content-Type': 'application/json',
            'X-CC-Api-Key': self.API_KEY,
            'X-CC-Version': self.API_VERSION
        }

    def post(self, endpoint, payload=None):
        url = self.API_URL + endpoint
        return requests.request("POST", url, headers=self.HEADERS, data=payload)

    def get(self, endpoint):
        url = self.API_URL + endpoint
        return requests.request("GET", url, headers=self.HEADERS, )

    def put(self, endpoint, payload=None):
        url = self.API_URL + endpoint
        return requests.request("PUT", url, headers=self.HEADERS, data=payload)

    def createInvoice(self, payload):
        return self.post('/invoices', json.dumps(payload))

    def listInvoices(self):
        return self.get('/invoices')

    def getAnInvoice(self, invoiceId):
        return self.get('/invoices/' + invoiceId)

    def voidAnInvoice(self, invoiceId):
        url = '/invoices/' + invoiceId + '/void'
        return self.put(url)

    def resolveAnInvoice(self, invoiceId):
        url = '/invoices/' + invoiceId + '/resolve'
        return self.put(url)