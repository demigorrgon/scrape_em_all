# [Scrape'em all Bot](https://t.me/scrape_em_all_bot)
Is a telegram bot that helps you with parsing Python related vacancies with ~1 year of experience on ukrainian job boards (djinni.co, dou.ua, work.ua). robota.ua is way too dynamic, bot could be extended with Selenium parsing of that site 

Filters on some sites are pretty bad, so it shouldn't be an issue if there is gonna be a senior position here and there, it should motivate you instead.

## Tech stack
Scrape'em all Bot is written with aiogram, aiohttp + bs4, celery, mongodb(mongoengine)

### Possible enhancements: 
- Remove restrictions of programming language
- Remove restrictions with experience
- Refactor scrapers, tasks processing
