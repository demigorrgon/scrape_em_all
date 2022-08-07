import logging
import os
from datetime import datetime

import mongoengine
from aiogram import executor, types
from aiogram.dispatcher.filters import Text

from scrape_em_all.config import app, bot, dispatcher
from scrape_em_all.helpers import get_user_or_exception, register_new_user
from scrape_em_all.models import BaseVacancy, DjinniVacancies, User
from scrape_em_all.tasks import scheduled_djinni_parsing

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


@dispatcher.message_handler(commands=["debug"])
async def debug_queries(message: types.Message):
    user: User = User.objects.get(username=message.chat.username)
    djinni = DjinniVacancies()
    new_vacancy = BaseVacancy()
    new_vacancy.title = "some"
    new_vacancy.link = "idk"
    new_vacancy.short_description = "asd"
    new_vacancy.ad_posted_at = datetime.now()
    djinni.user = user
    djinni.vacancies.append(new_vacancy)
    djinni.save()
    print(DjinniVacancies.objects.filter(vacancies__link="idk", user=user))
    await message.reply("Added new debug line")


@dispatcher.message_handler(commands=["celery"])
async def test_celery_task_parse(message: types.Message):
    await message.reply("Celery task started")
    logging.info(f"Celery task started by {message.chat.username}")
    user = get_user_or_exception(username=message.chat.username)
    try:
        # result = scheduled_djinni_parsing.delay(telegram_username=user.username)
        # print(result.get())
        app.add_periodic_task(60, scheduled_djinni_parsing, (user.username,))
        await message.reply("Task finished successfully")
        logging.info("Celery task finished")
    except Exception as e:
        await bot.send_message(message.chat.id, f"There was an error: {str(e)}")
        logging.error(repr(e))

    return


if __name__ == "__main__":
    mongoengine.register_connection(
        alias="core",
        host=os.environ.get("MONGO_HOST"),
        port=int(os.environ.get("MONGO_PORT")),
        name=os.environ.get("DB_NAME"),
    )
    executor.start_polling(dispatcher, skip_updates=True)
