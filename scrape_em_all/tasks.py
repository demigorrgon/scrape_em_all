import asyncio

# from celery.schedules import crontab
from celery.utils.log import get_task_logger

from scrape_em_all.config import app
from scrape_em_all.scraper import DjinniScraper

logger = get_task_logger(__name__)


@app.task(name="djinni_parsing")
def scheduled_djinni_parsing(telegram_username):
    logger.info(f"Djinni parsing started by {telegram_username}")
    scraper = DjinniScraper(telegram_username=telegram_username)
    asyncio.run(scraper.fetch())
    logger.info(f"Djinni parsing finished, user:{telegram_username}")
    # app.conf.beat_schedule["djinni_parsing"]["args"] = tuple([telegram_username])
    # print(app.conf.beat_schedule)
    return 200


app.conf.beat_schedule = {
    "djinni-parsing": {
        "task": "djinni_parsing",
        "schedule": 120.0,
    },
}
