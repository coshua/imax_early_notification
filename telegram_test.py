from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

BOT_TOKEN = "5792832504:AAEvFuVtYKEUrjMvLnpGMnzd1vr5OqdCMnE"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)
bot = Bot(BOT_TOKEN)
def echo(update: Update, context:CallbackContext):
    update.message.reply_text(update.message.text)

updater = Updater(BOT_TOKEN)
updater.bot.send_message(5794019445, "This is bot")
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(Filters.text, echo))
updater.start_polling()
updater.idle()

