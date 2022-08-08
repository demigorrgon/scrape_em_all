import asyncio
import logging
import os

import mongoengine
from aiogram import executor, types
from aiogram.dispatcher.filters import Text

from scrape_em_all.config import app, bot, dispatcher
from scrape_em_all.helpers import CeleryTaskManager, register_new_user

# from scrape_em_all.models import BaseVacancy, DjinniVacancies, User
from scrape_em_all.tasks import scheduled_djinni_parsing, scheduled_dou_parsing

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
            "Heyo! I'm a Scrape'em all bot. I will help you with finding desired jobs in Ukrainian IT segment.\nCurrently supported: djinni.co, jobs.dou.ua, robota.ua, work.ua\nParces Python vacancies with 1 year exp (depending on filters of parsed websites)",
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


@dispatcher.message_handler(commands=["celery"])
async def test_celery_task_parse(message: types.Message):
    logging.info(f"Celery task started by {message.chat.username}")
    # try:
    await message.reply("Parsing started")
    djinni_task = scheduled_djinni_parsing.delay(message.chat.username)
    CeleryTaskManager(message.chat.username).add_to_storage(
        "djinni_task_id", djinni_task.id
    )
    await asyncio.sleep(3)
    dou_task = scheduled_dou_parsing.delay(message.chat.username)
    CeleryTaskManager(message.chat.username).add_to_storage("dou_task_id", dou_task.id)

    # except Exception as e:
    #     await bot.send_message(message.chat.id, f"There was an error: {str(e)}")
    #     logging.error(repr(e))

    return


@dispatcher.message_handler(commands=["break"])
async def break_from_parsing(message: types.Message):
    try:
        current_user_tasks = CeleryTaskManager(message.chat.username)
        djinni_task = current_user_tasks.retrieve_task("djinni_task_id")
        dou_task = current_user_tasks.retrieve_task("dou_task_id")

    except KeyError:
        await message.reply("You aren't subscribed to parsing rn. Hint: /celery atm")
        return
    await message.reply("Hold on, we are stopping")
    app.control.revoke(djinni_task, terminate=True, signal="SIGKILL")
    app.control.revoke(dou_task, terminate=True, signal="SIGKILL")

    current_user_tasks.clear_tasks_from_storage()
    await bot.send_message(message.chat.id, "Parsing stopped")


if __name__ == "__main__":
    mongoengine.register_connection(
        alias="core",
        host=os.environ.get("MONGO_HOST"),
        port=int(os.environ.get("MONGO_PORT")),
        name=os.environ.get("DB_NAME"),
    )
    executor.start_polling(dispatcher, skip_updates=True)
