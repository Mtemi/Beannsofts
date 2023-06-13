import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

postgres_local_base = os.getenv('DATABASE_URI')
# postgres_local_base = os.environ['DATABASE_URL

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = os.getenv('SECRET_KEY', 'sirikali-sana-msee')
    DEBUG = False
    TOKEN_EXPIRE_HOURS = 1000
    CELERY_BROKER_URL = os.getenv('REDIS_URL')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
    MONGODB_HOST = os.getenv('MONGO_URL')
    REDIS_URL = os.getenv('REDIS_URL')

    # Coinbase config
    COINBASE_KEY = os.getenv('COINBASE_KEY')
    COINBASE_WEBHOOK_SECRET = os.getenv('COINBASE_WEBHOOK_SECRET')

    # Mail Server Config
    MAIL_SERVER = 'smtp.mailtrap.io'
    MAIL_PORT = 2525
    MAIL_USE_TLS = True
    MAIL_USERNAME = '7953fdc86b4547'
    MAIL_PASSWORD = '7d61c5557d2ebe'
    MAIL_USE_SSL = False
    MAIL_DEFAULT_SENDER = 'info@crypttops.com'

    # sse Events...
    SSE_EVENTS = ['authentication', 'exchange', 'terminal-orders', 'smart-trade', 'smart-buy', 'smart-sell',
                  'smart-cover', 'grid-bot', 'dca-bot', 'bot-market-place', 'subscription', 'payment', 'sse']

    # bot base url

    TELEGRAM_BOT_BASE_URL = os.getenv('TELEGRAM_BOT_BASE_URL')

    TELEGRAM_BOT_TOKEN =os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_BOT_WEBHOOK_URL = 'https://api.3commas.crypttops.com/telegram/webhook/add/user'

    STRATEGY_FOLDER = str(Path().absolute())+"/strategies"
    STRATEGY_ALLOWED_EXTENSIONS = set(['py'])

    WEBHOOK_URL = "https://api.bitsgap.crypttops.com/webhook"

    KlineSymbols5m = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    KlineSymbols30m = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    KlineSymbols1h = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    KlineSymbols4h = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    KlineSymbols12h = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    KlineSymbols1d = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    KlineSymbols1w = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    KlineSymbols1m = ['ethusdt', 'adausdt', 'dogeusdt', 'btcusdt', 'xrpusdt', 'ltcusdt', 'dashusdt','bchusdt'] 
    
    BOOKTICKER_STREAMS = ['btcusdt@bookTicker', 'ethusdt@bookTicker', 'dogeusdt@bookTicker', 'adausdt@bookTicker', 'xrpusdt@bookTicker', 'ltcusdt@bookTicker', 'dashusdt@bookTicker', 'bchusdt@bookTicker']

    STREAMER_SERVICE_API_KEY = "02eTTLVw9T6g3oEmelloLP3IGt8QlCoCOKvdWshpKU1KWOQ7sDIm2xrDOPe3X9S6 "

    STREAMER_SERVICE_API_SECRET = "MjP6qfoCnLX8KeIFAzW0KyE3LL96xlbbTYI962pWtyaES4SBIWiJXBJ1S3uMwoS8"


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = postgres_local_base
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = postgres_local_base
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = postgres_local_base


config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig
)

key = Config.SECRET_KEY
