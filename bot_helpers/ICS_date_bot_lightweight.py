from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import os, sys, re, logging
from datetime import datetime

API_KEY = os.getenv("TELEGRAM_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def validateParameter():
    if API_KEY == "":
        sys.exit("missing api key")

ICS_LAYOUT_FRONT = """BEGIN:VCALENDAR 
VERSION:2.0 
PRODID:Telegram:GivvlHelper_bot/lightweight 
BEGIN:VEVENT
DTSTART;TZID=Europe/Berlin:{datetime_start}
DTEND;TZID=Europe/Berlin:{datetime_end}
NAME:{name}
SUMMARY:{summary}"""

ICS_LAYOUT_LOCATION = """
LOCATION:{location}"""

ICS_LAYOUT_END = """
END:VEVENT
END:VCALENDAR"""

formats = ["%d.%m.%Y %H:%M", "%-d.%-m.%Y %H:%M", "%d.%m.%Y %-H:%M", "%-d.%-m.%Y %-H:%M", "%d.%m.%Y", "%-d.%-m.%Y", "%-d.%-m.%-y %-H:%M", "%-d.%-m.%-y"]

def parseStringToDate(string: str):
    for format in formats:
        try:
            parsed_date = datetime.strptime(string, format)
            return parsed_date
        except ValueError:
            continue
    return ValueError

def parseDatetoString(date: datetime):
    return datetime.strftime(date, "%Y%m%dT%H%M%S")

async def event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_data = " ".join(context.args)
    substring = re.split('_', input_data)
    
    if (1>=len(substring) or 5<=len(substring)):
        msg = "Please stick to the format: /event NAME_LOCATION_DATE_DATE \nNAME and LOCATION mustn't contain any _"
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

    datetime_index = len(substring)-2
    
    date_start = parseStringToDate(substring[datetime_index])
    date_end =parseStringToDate(substring[datetime_index+1])
    if (date_start == ValueError or date_end == ValueError):
        msg = "Please stick to the format: dd.mm.yyyy hh:mm"
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    
    datetime_start_string = parseDatetoString(date_start)
    datetime_end_string = parseDatetoString(date_end)
    output_data = ICS_LAYOUT_FRONT.format(name=substring[0], summary= substring[0], datetime_start = datetime_start_string, datetime_end = datetime_end_string)
    if (len(substring) == 4):
        output_data+= ICS_LAYOUT_LOCATION.format(location=substring[1])
    output_data += ICS_LAYOUT_END
    await context.bot.send_document(chat_id=update.effective_chat.id, document= InputFile(output_data, filename=substring[0] + ".ics"))
    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    send = "Commands: \n"
    send += getHelpString()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=send)

#Commands for easy integration into other bots
def getHandlers():
    handlers = []
    handlers.append(CommandHandler('event', callback=event, has_args=True))
    return handlers

def getHelpString():
    return "- /event : Creates an ICS file with the given info. \nCommand format: \n/event NAME_LOCATION_DATE_DATE \nDATE format: DD.MM.YYYY HH:MM \nLOCATION is optional \n \n"
#END: Commands for easy integration into other bots

if __name__ == '__main__':

    validateParameter()

    application = ApplicationBuilder().token(API_KEY).build()

    event_handler = CommandHandler('event', callback=event, has_args=True)

    help_handler = CommandHandler('help', help)
    
    application.add_handlers([help_handler, event_handler])


    application.run_polling()

