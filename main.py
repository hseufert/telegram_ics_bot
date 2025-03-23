import ICS_date_bot_lightweight as ICS_bot

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import os, sys, logging

API_KEY = os.getenv("TELEGRAM_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def validateParameter():
    if API_KEY == "":
        sys.exit("missing api key")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send = "Commands: \n"
    send += ICS_bot.getHelpString()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=send)

if __name__ == '__main__':

    validateParameter()

    application = ApplicationBuilder().token(API_KEY).build()

    bot_handlers = []

    bot_handlers.extend(ICS_bot.getHandlers())

    bot_handlers.append(CommandHandler('help', help))
    
    application.add_handlers(bot_handlers)

    application.run_polling()