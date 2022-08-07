import asyncio
import re

import aiohttp
from bs4 import BeautifulSoup

from scrape_em_all.config import bot
from scrape_em_all.helpers import (
    check_if_parsed_entry_exists_in_db,
    date_in_ukrainian_to_datetime,
    get_user_or_exception,
)
from scrape_em_all.models import DjinniVacancies


class DjinniScraper:
    """
    Scraper for djinni.co, scrapes python related jobs with 1 year of exp
    Could be easily extendable on need
    @param: telegram_username: user's telegram username to query and save embedded document data related to that user
    """

    def __init__(self, telegram_username: str) -> None:
        self.url = "https://djinni.co/jobs/keyword-python/?exp_level=1y&page="
        try:
            self.user = get_user_or_exception(telegram_username)
        except Exception:
            print(
                f"User: {telegram_username} was not found. Did he change telegram username?"
            )
            raise Exception("User does not exist. Rerun /start command")

    async def fetch(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                page = await response.text()
                soup = BeautifulSoup(page, "html.parser")
                pagination = soup.findAll("li", {"class": "page-item"})[1:-1]
                last_page = re.findall(r">[0-9]+<", str(pagination[-1]))[0][1:-1]
                tasks = []
                for page_number in range(1, int(last_page) + 1):
                    task = asyncio.create_task(
                        self.fetch_paginated_page(session, page_number)
                    )
                    tasks.append(task)

                parsed_data = await asyncio.gather(*tasks)
                for parsed_page in parsed_data:
                    for ad in parsed_page:
                        title = ad[0]
                        link = ad[1]
                        short_description = ad[2]
                        ad_posted_at = date_in_ukrainian_to_datetime(ad[3])
                        # if parsed data entry is in db -> don't save, move on to next advertisement
                        if check_if_parsed_entry_exists_in_db(
                            vacancies_model=DjinniVacancies,
                            user=self.user,
                            parsed_data=ad,
                        ):
                            continue
                        new_vacancy = DjinniVacancies(
                            parsed_by=self.user,
                            title=title,
                            link=link,
                            short_description=short_description,
                            ad_posted_at=ad_posted_at,
                        )
                        new_vacancy.save()
                        print(new_vacancy)
                        if self.user.has_parsed:
                            # send notifications only after initial parse
                            await bot.send_message(
                                self.user.telegram_id,
                                f"Found new vacancy: \n{title}, djinni.co{link}\n{short_description}",
                            )
                await bot.send_message(
                    self.user.telegram_id,
                    f"{DjinniVacancies.objects(parsed_by=self.user).count()} opened vacancies on djinni atm",
                )
                self.user.has_parsed = True
                self.user.save()
                return

    async def fetch_paginated_page(
        self, session: aiohttp.ClientSession, page_number: str
    ):
        async with session.get(self.url + str(page_number)) as page_response:
            page = await page_response.text()
            soup = BeautifulSoup(page, "html.parser")
            vacancies_titles = soup.findAll("div", {"class": "list-jobs__title"})
            vacancies_text = [item.find("span").text for item in vacancies_titles]
            vacanies_links = [
                item.find("a", {"class": "profile"})["href"]
                for item in vacancies_titles
            ]
            vacancies_date_posted = [
                item.find("div", {"class": "text-date pull-right"}).text.strip()
                for item in soup.find_all("li", {"class": "list-jobs__item"})
            ]
            vacancies_descriptions = [
                item.find("p").text
                for item in soup.findAll("div", {"class": "list-jobs__description"})
            ]
            # vacancies_details = soup.find_all("div", {"class": "list-jobs__details"})
            # print(f"details:{vacancies_details}")

            return list(
                zip(
                    vacancies_text,
                    vacanies_links,
                    vacancies_descriptions,
                    vacancies_date_posted,
                )
            )


class DouScraper(DjinniScraper):
    def __init__(self, telegram_username: str) -> None:
        super().__init__(telegram_username)
        self.url = "https://jobs.dou.ua/vacancies/?category=Python&exp=1-3"

    async def fetch(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                page = await response.text()
                soup = BeautifulSoup(page, "html.parser")
                ad_headers = soup.find_all("a", {"class": "vt"})
                print(ad_headers)

    async def parse_page(self):
        pass


# if __name__ == "__main__":
#     # start = datetime.now()
#     djinni = DjinniScraper(telegram_username="demigorrgon")
#     # dou = DouScraper(telegram_username="demigorrgon")
#     asyncio.run(djinni.fetch())
# asyncio.run(dou.fetch())

# end = datetime.now()
# print(f"Finished in: {end-start}")
