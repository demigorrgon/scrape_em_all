import os

import mongoengine
import pytz

# import redis
from aiogram import Bot, Dispatcher
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

tz = pytz.timezone("Europe/Kiev")

bot = Bot(token=os.environ.get("BOT_TOKEN"))
dispatcher = Dispatcher(bot)

# r = redis.Redis(host=os.environ.get("REDIS_HOST", port=6379, db=0))

mongo_connection = mongoengine.register_connection(alias="core", name="scrape_em_db")
app = Celery("scrape_em_all", broker="redis://0.0.0.0:6379//0")
