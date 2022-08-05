import logging

import mongoengine
from aiogram import executor, types
from aiogram.dispatcher.filters import Text

from scrape_em_all.config import dispatcher
from scrape_em_all.helpers import register_new_user
from scrape_em_all.models import User

logging.basicConfig(level=logging.INFO)


@dispatcher.message_handler(commands=["start", "help"])
async def greet(message: types.Message):
    # try except

    commands_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_parsing_button = types.KeyboardButton(text="Start parsing for the 1st time")
    subscribe_to_updates = types.KeyboardButton(
        text="Subscribe to updates (every 15 mins)"
    )
    commands_keyboard.add(start_parsing_button)
    commands_keyboard.add(subscribe_to_updates)
    if not register_new_user(message):
        await message.answer(
            "You've already started conversation with me, please select parsing choices.",
            reply_markup=commands_keyboard,
        )

    else:
        await message.answer(
            "Heyo! I'm a Scrape'em all bot. I will help you with finding desired jobs in Ukrainian IT segment.\nCurrently supported: djinni.co, jobs.dou.ua, robota.ua, work.ua",
            reply_markup=commands_keyboard,
        )


@dispatcher.message_handler(Text(equals="Start parsing for the 1st time"))
async def handle_first_time_parsing(message: types.Message):
    options_after_parsing = types.ReplyKeyboardMarkup(resize_keyboard=True)
    some_button = types.KeyboardButton(text="DEBUG")
    options_after_parsing.add(some_button)
    await message.reply(
        "Started parsing.... (static)", reply_markup=options_after_parsing
    )


@dispatcher.message_handler(Text(equals="Subscribe to updates (every 15 mins)"))
async def subscribe_to_scheduled_parsing(messsage: types.Message):
    await messsage.reply(
        "Very well then. I'll notify you if something new was found this time",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@dispatcher.message_handler(Text(equals="User"))
async def debug_queries(message: types.Message):
    user_data = User.objects(username=message.chat.username).first()
    print(user_data)
    await message.reply(f"{user_data}")


if __name__ == "__main__":
    mongoengine.register_connection(alias="core", name="scrape_em_db")
    executor.start_polling(dispatcher, skip_updates=True)
