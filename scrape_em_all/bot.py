import logging
import os
from datetime import date

import mongoengine
from aiogram import executor, types
from aiogram.dispatcher.filters import Text

from scrape_em_all.config import app, bot, dispatcher
from scrape_em_all.helpers import CeleryTaskManager, register_new_user
from scrape_em_all.models import DjinniVacancies, DouVacancies, User, WorkVacancies

# from scrape_em_all.models import BaseVacancy, DjinniVacancies, User
from scrape_em_all.tasks import (
    scheduled_djinni_parsing,
    scheduled_dou_parsing,
    scheduled_workua_parsing,
)

logging.basicConfig(level=logging.INFO)


@dispatcher.message_handler(commands=["start"])
async def greet(message: types.Message):
    # try except

    commands_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # start_parsing_button = types.KeyboardButton(text="Start parsing for the 1st time")
    subscribe_to_updates = types.KeyboardButton(text="Start searching")
    # commands_keyboard.add(start_parsing_button)
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


@dispatcher.message_handler(commands=["help"])
@dispatcher.message_handler(Text(contains="help"))
async def help(message: types.Message):
    await message.reply(
        "Heyo.\nWhat can I do?\nClick on the menu button to see the list of commands\nYou can enter date in <day> <month> format to find vacancies posted in sertain day: NYI\nKeyboard will help you with the rest"
    )


@dispatcher.message_handler(commands=["find_vacancies"])
@dispatcher.message_handler(Text(equals="Start searching"))
async def start_parsing_tasks(message: types.Message):
    logging.info(f"Celery task started by {message.chat.username}")
    # try:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    stop_button = types.KeyboardButton(text="Stop")
    keyboard.add(stop_button)
    await message.reply("Looking for new vacancies.", reply_markup=keyboard)
    djinni_task = scheduled_djinni_parsing.delay(message.chat.username)
    CeleryTaskManager(message.chat.username).add_to_storage(
        "djinni_task_id", djinni_task.id
    )
    dou_task = scheduled_dou_parsing.delay(message.chat.username)
    CeleryTaskManager(message.chat.username).add_to_storage("dou_task_id", dou_task.id)

    workua_task = scheduled_workua_parsing.delay(message.chat.username)
    CeleryTaskManager(message.chat.username).add_to_storage(
        "workua_task_id", workua_task.id
    )
    # except Exception as e:
    #     await bot.send_message(message.chat.id, f"There was an error: {str(e)}")
    #     logging.error(repr(e))

    return


@dispatcher.message_handler(commands=["stop", "break", "end"])
@dispatcher.message_handler(Text(equals="Stop"))
async def break_from_parsing(message: types.Message):
    keyboard_on_stop = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_again_button = types.KeyboardButton(text="Start searching")
    keyboard_on_stop.add(start_again_button)

    try:
        current_user_tasks = CeleryTaskManager(message.chat.username)
        djinni_task = current_user_tasks.retrieve_task("djinni_task_id")
        dou_task = current_user_tasks.retrieve_task("dou_task_id")
        workua_task = current_user_tasks.retrieve_task("workua_task_id")

    except KeyError:
        await message.reply(
            "You aren't subscribed to parsing rn. Hint: /find_vacancies atm"
        )
        return
    await message.reply("Hold on, we are stopping")
    app.control.revoke(djinni_task, terminate=True, signal="SIGKILL")
    app.control.revoke(dou_task, terminate=True, signal="SIGKILL")
    app.control.revoke(workua_task, terminate=True, signal="SIGKILL")

    current_user_tasks.clear_tasks_from_storage()
    print(f"{message.chat.username} removed all tasks from storage")
    await bot.send_message(
        message.chat.id,
        "Parsing stopped.\nYou can subscribe again at any time",
        reply_markup=keyboard_on_stop,
    )


@dispatcher.message_handler(Text(equals="today"))
@dispatcher.message_handler(commands=["today"])
async def show_todays_vacancies(message: types.Message):
    await message.reply("Today's vacancies will be shown in a moment...")
    user = User.objects.get(username=message.chat.username)
    djinni_ads = DjinniVacancies.objects(parsed_by=user, ad_posted_at=date.today())
    for djinni_ad in djinni_ads:
        await bot.send_message(
            message.chat.id,
            f"{djinni_ad.title}\ndjinni.co{djinni_ad.link}\n{djinni_ad.short_description}",
        )
    dou_ads = DouVacancies.objects(parsed_by=user, ad_posted_at=date.today())
    for dou_ad in dou_ads:
        await bot.send_message(
            message.chat.id,
            f"{dou_ad.title}\n{dou_ad.link}\n{dou_ad.short_description}",
        )
    workua_ads = WorkVacancies.objects(parsed_by=user, ad_posted_at=date.today())
    for work_ad in workua_ads:
        await bot.send_message(
            message.chat.id,
            f"{work_ad.title}\nwork.ua{work_ad.link}\n{work_ad.short_description}",
        )


if __name__ == "__main__":
    mongoengine.register_connection(
        alias="core",
        host=os.environ.get("MONGO_HOST"),
        port=int(os.environ.get("MONGO_PORT")),
        name=os.environ.get("DB_NAME"),
    )
    executor.start_polling(dispatcher, skip_updates=True)
