import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()

bot = Bot(token=os.environ.get("BOT_TOKEN"))
dispatcher = Dispatcher(bot)


@dispatcher.message_handler(commands=["start", "help"])
async def greet(message: types.Message):
    commands_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_parsing_button = types.KeyboardButton(text="Start parsing for the 1st time")
    subscribe_to_updates = types.KeyboardButton(
        text="Subscribe to updates (every 15 mins)"
    )
    commands_keyboard.add(start_parsing_button)
    commands_keyboard.add(subscribe_to_updates)

    await message.answer(
        "Heyo! I'm a Scrape'em all bot. I will help you with finding desired jobs in Ukrainian IT segment.\nCurrently supported: djinni.co, jobs.dou.ua, robota.ua, work.ua",
        reply_markup=commands_keyboard,
    )


@dispatcher.message_handler(Text(equals="Start parsing for the 1st time"))
async def handle_first_time_parsing(message: types.Message):
    await message.reply(
        "Started parsing.... (static)", reply_markup=types.ReplyKeyboardRemove()
    )


@dispatcher.message_handler(Text(equals="Subscribe to updates (every 15 mins)"))
async def subscribe_to_scheduled_parsing(messsage: types.Message):
    await messsage.reply(
        "Very well then. I'll notify you if something new was found this time",
        reply_markup=types.ReplyKeyboardRemove(),
    )


if __name__ == "__main__":
    executor.start_polling(dispatcher, skip_updates=True)
