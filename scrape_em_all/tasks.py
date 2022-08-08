import asyncio
import time

# from celery.schedules import crontab
from celery.utils.log import get_task_logger

from scrape_em_all.config import app
from scrape_em_all.scraper import DjinniScraper, DouScraper

logger = get_task_logger(__name__)


@app.task(name="djinni_parsing")
def scheduled_djinni_parsing(telegram_username):
    logger.info(f"Djinni parsing started by {telegram_username}")
    while True:
        scraper = DjinniScraper(telegram_username=telegram_username)
        asyncio.run(scraper.fetch())
        logger.info(f"Djinni parsing finished, user:{telegram_username}")
        time.sleep(60)


@app.task(name="dou_parsing")
def scheduled_dou_parsing(telegram_username: str) -> None:
    logger.info(f"Dou parsing started by {telegram_username}")
    while True:
        dou_scraper = DouScraper(telegram_username=telegram_username)
        asyncio.run(dou_scraper.fetch())
        logger.info(f"Dou parsing finished, user:{telegram_username}")
        time.sleep(60)
