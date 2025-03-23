
import asyncio, logging, sys, pathlib, os

from typing import Any, Dict
import dateutil
from dateutil.parser import parse, parserinfo
from datetime import datetime
from icalendar import Calendar, Event, vCalAddress, vText

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    BufferedInputFile,
)

API_KEY = os.getenv("TELEGRAM_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

form_router = Router()

class Form(StatesGroup):
    name = State()
    start_date = State()
    end_date = State()
    full_day = State()
    start_time = State ()
    end_time = State()
    
def is_date(string):
    try: 
        return True, parse(string, fuzzy=True, dayfirst=True, yearfirst=False)

    except ValueError:
        return False, datetime.now()

def is_time(string):
    try: 
        return True, datetime.strptime(string, "%H:%M")

    except ValueError:
        return False, datetime.now()

class CustomParserInfo(parserinfo):
    parserinfo(True, False)
    # three months in Spanish for illustration

@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer(
        "What will your event be called?",
        reply_markup=ReplyKeyboardRemove(),
    )
@form_router.message(Form.name)
async def command_start(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Form.start_date)
    await message.answer(
        "At which date will your event Start?",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )

@form_router.message(Form.start_date)
async def process_start_date(message: Message, state: FSMContext) -> None:
    datebool, dt = is_date(message.text)
    if datebool:
        await state.update_data(start_date=dt)
        await state.set_state(Form.end_date)
        await message.answer(
            f"Great, the {html.quote(message.text)}.\n And when will it end?",
            reply_markup=ReplyKeyboardRemove(),
            )
    else:
        await message.answer(
            "I could not make out that day. Please use the format dd.mm.yyyy:",
            reply_markup=ReplyKeyboardRemove(),
            )

@form_router.message(Form.end_date)
async def process_end_date(message: Message, state: FSMContext) -> None:
    datebool, dt = is_date(message.text)
    if datebool:
        await state.update_data(end_date=dt)
        await state.set_state(Form.full_day)    
        await message.answer(
        f"Will your event go on for full days or do you have a start and end time?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Full Days"),
                    KeyboardButton(text="Start/End Time"),
                ]
            ],
            resize_keyboard=True,
        ),
    )
    else:
        await message.answer(
            "I could not make out that day. Please use the format dd.mm.yyyy:",
            reply_markup=ReplyKeyboardRemove(),
            )
    
    

@form_router.message(Form.full_day, F.text == "Full Days")
async def process_full_day(message: Message, state: FSMContext) -> None:
    data = await state.update_data(full_day= True)
    await state.clear()
    await message.answer(
        "Here is your requested event:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await show_summary(message=message, data=data, positive=False)
    

@form_router.message(Form.full_day, F.text == "Start/End Time")
async def process_start_date(message: Message, state: FSMContext) -> None:
    await state.update_data(full_day= False)
    await state.set_state(Form.start_time)
    await message.reply(
        "At what time will your event start?",
        reply_markup=ReplyKeyboardRemove(),
    )

@form_router.message(Form.full_day)
async def process_unknown_write_bots(message: Message) -> None:
    await message.answer(
        f"Please choose one of the provided Messages",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Full Days"),
                    KeyboardButton(text="Start/End Time"),
                ]
            ],
            resize_keyboard=True,
        ),
    )

@form_router.message(Form.start_time)
async def process_language(message: Message, state: FSMContext) -> None:
    timebool, dt = is_time(message.text)
    if timebool:
        await state.update_data(start_time=dt)
        await state.set_state(Form.end_time)    
        await message.reply(
            "And when will it end?",
            reply_markup=ReplyKeyboardRemove(),
        )
    else: 
        await message.reply(
            "Please use the format HH:MM",
            reply_markup=ReplyKeyboardRemove(),
        )


@form_router.message(Form.end_time)
async def process_language(message: Message, state: FSMContext) -> None:
    timebool, dt = is_time(message.text)
    if timebool:
        data = await state.update_data(end_time=dt)
        await state.clear()

        await message.answer(
            "Here is your requested event:"
        )
        await show_summary(message=message, data=data)
    else:
        await message.reply(
            "Please use the format HH:MM",
            reply_markup=ReplyKeyboardRemove(),
        )
    


async def show_summary(message: Message, data: Dict[str, Any], positive: bool = True) -> None:
    name = data["name"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    full_day = data["full_day"]
    
    if not (full_day):
        start_time = data["start_time"]
        end_time = data["end_time"]
        start_date =start_date.combine(start_date, start_time.time(), )
        end_date =end_date.combine(end_date, end_time.time())
    cal = Calendar()
    cal.add('prodid', 'Telegram:GivvlHelper_bot')
    cal.add('version', '2.0')
    event = Event()
    event.add('name', name)
    event.add('summary', name)
    tz = dateutil.tz.tzstr("Europe/Berlin")
    event.add('dtstart', start_date.replace(tzinfo = tz))
    event.add('dtend', end_date.replace(tzinfo = tz))
    
    cal.add_component(event)
    # Write to disk
    
    fileName = name + '.ics'

    file = BufferedInputFile(cal.to_ical(), fileName)
    await message.answer_document(document=file)


async def main():
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=API_KEY, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    dp.include_router(form_router)

    # Start event dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())