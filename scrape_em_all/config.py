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
mongo_connection = mongoengine.register_connection(
    alias="core",
    host=os.environ.get("MONGO_HOST"),
    port=int(os.environ.get("MONGO_PORT")),
    name=os.environ.get("DB_NAME"),
)
app = Celery(
    "scrape_em_all",
    backend=f"redis://{os.environ.get('REDIS_HOST')}:6379//0",
    broker=f"redis://{os.environ.get('REDIS_HOST')}:6379//0",
)
app.autodiscover_tasks()
