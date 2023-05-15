import logging
from app.src.config import Config

from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
)

# Enable logging
from telegram.utils import helpers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

TOKEN = Config.TELEGRAM_BOT_TOKEN
WEBHOOK_URL = Config.TELEGRAM_BOT_WEBHOOK_URL

def start(update: Update, context: CallbackContext) -> None:
    """Send a deep-linked URL when the command /start is issued."""
    bot = context.bot
    print(bot)
    userObj = update.message.from_user
    print(userObj)
    text = (
        "Awesome, you have successifully accessed notification functionality! "
        "Now let's get back to the private chat."
    )
    update.message.reply_text(text)

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Make sure the deep-linking handlers occur *before* the normal /start handler.
    dispatcher.add_handler(CommandHandler("start", start))
    
    updater.bot.set_webhook(WEBHOOK_URL)
    print("In Server Mode! Listening for incoming messages")


    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
