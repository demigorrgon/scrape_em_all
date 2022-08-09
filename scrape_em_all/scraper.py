import asyncio
import re
from collections import namedtuple

import aiohttp
from bs4 import BeautifulSoup

from scrape_em_all.config import bot
from scrape_em_all.helpers import (
    check_if_parsed_entry_exists_in_db,
    date_in_ukrainian_to_datetime,
    get_user_or_exception,
)
from scrape_em_all.models import DjinniVacancies, DouVacancies, WorkVacancies


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
                        if self.user.has_parsed_djinni:
                            # send notifications only after initial parse
                            await bot.send_message(
                                self.user.telegram_id,
                                f"Found new vacancy: \n{title}, djinni.co{link}\n{short_description}",
                            )
                self.user.has_parsed_djinni = True
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

                ad_titles = [
                    self.clean_from_escape_characters(ad.text.strip())
                    for ad in soup.find_all("a", {"class": "vt"})
                ]
                ad_dates = [
                    self.clean_from_escape_characters(ad.text.strip())
                    for ad in soup.find_all("div", {"class": "date"})
                ]
                ad_descriptions = [
                    self.clean_from_escape_characters(ad.text.strip())
                    for ad in soup.find_all("div", {"class": "sh-info"})
                ]
                ad_links = [ad["href"] for ad in soup.find_all("a", {"class": "vt"})]
                ads = list(zip(ad_titles, ad_links, ad_descriptions, ad_dates))
                for ad in ads:
                    ads_tuple = namedtuple("ads", "title link description date")
                    data = ads_tuple(ad[0], ad[1], ad[2], ad[3])
                    if check_if_parsed_entry_exists_in_db(DouVacancies, self.user, ad):
                        continue
                    new_dou_vacancy = DouVacancies(
                        parsed_by=self.user,
                        title=data.title,
                        link=data.link,
                        short_description=data.description,
                        ad_posted_at=date_in_ukrainian_to_datetime(data.date),
                    )
                    new_dou_vacancy.save()
                    if self.user.has_parsed_dou:
                        # send notifications only after initial parse
                        await bot.send_message(
                            self.user.telegram_id,
                            f"Found new vacancy: \n{data.title}\nposted at: {data.date}\n{data.link}\n{data.description}",
                        )

                self.user.has_parsed_dou = True
                self.user.save()
                return

    def clean_from_escape_characters(self, string):
        return re.sub(r"\xa0|\n", " ", string)


class WorkuaScraper(DjinniScraper):
    def __init__(self, telegram_username: str) -> None:
        super().__init__(telegram_username)
        self.url = "https://www.work.ua/jobs-python/?advs=1&page="

    async def fetch(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                page = await response.text()
                soup = BeautifulSoup(page, "html.parser")
                pagination = soup.find_all("ul", {"class": "pagination hidden-xs"})[0]
                last_page_number: str = re.findall(r"[0-9]+", pagination.text.strip())[
                    -1
                ]
                tasks = []
                for page in range(1, int(last_page_number) + 1):
                    task = asyncio.create_task(self.fetch_paginated_page(session, page))
                    tasks.append(task)
                parsed_data = await asyncio.gather(*tasks)
                for parsed_page in parsed_data:
                    for ad in parsed_page:
                        ads_tuple = namedtuple("ads", "title link description date")
                        data = ads_tuple(ad[0], ad[1], ad[2], ad[3])
                        if check_if_parsed_entry_exists_in_db(
                            WorkVacancies, self.user, ad
                        ):
                            continue
                        new_workua_vacancy = WorkVacancies(
                            parsed_by=self.user,
                            title=data.title,
                            link=data.link,
                            short_description=data.description,
                            ad_posted_at=date_in_ukrainian_to_datetime(data.date),
                        )
                        new_workua_vacancy.save()
                        if self.user.has_parsed_workua:
                            # send notifications only after initial parse
                            await bot.send_message(
                                self.user.telegram_id,
                                f"Found new vacancy: \n{data.title}\nposted at: {data.date}\nwhttps://work.ua/{data.link}\n{data.description}",
                            )
                self.user.has_parsed_workua = True
                self.user.save()
                return

    async def fetch_paginated_page(
        self, session: aiohttp.ClientSession, page_number: str
    ):
        async with session.get(self.url + str(page_number)) as page_response:
            page = await page_response.text()
            soup = BeautifulSoup(page, "html.parser")
            header = soup.find_all(
                "div", {"class": "card card-hover card-visited wordwrap job-link"}
            )
            bodies = soup.find_all(
                "p", {"class": "overflow text-muted add-top-sm cut-bottom"}
            )
            titles = []
            links = []
            dates = []
            descriptions = []

            for title in header:
                title_payload = re.findall(r'<h2 class="">\n.+\n<\/h2>', str(title))[0]
                cleaned_link = re.findall(r"\/[a-z]+\/[a-z0-9]+\/", title_payload)[0]
                cleaned_date = re.findall(r"[0-9]+\s[а-я]+\s[0-9]{4}", title_payload)[0]
                cleaned_title = title_payload.split("title=")[1].split(",")[0][1:]
                titles.append(cleaned_title)
                links.append(cleaned_link)
                dates.append(cleaned_date)

            for description in bodies:
                cleaned_body = re.sub(
                    r"\n\s+|\s+|\xa0|\u2060", " ", description.text.strip()
                )
                descriptions.append(cleaned_body)

            return list(zip(titles, links, descriptions, dates))
