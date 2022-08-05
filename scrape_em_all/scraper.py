import asyncio
import re
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup


class DjinniScraper:
    """
    Scraper for djinni.co, scrapes python related jobs with 1 year of exp
    Could be easily extendable on need
    """

    def __init__(self) -> None:
        self.url = "https://djinni.co/jobs/keyword-python/?exp_level=1y&page="

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
                print(parsed_data)
                # # with open("test_data.txt", "w") as file:
                # #     file.write("".join(item for item in parsed_data))

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


if __name__ == "__main__":
    start = datetime.now()
    djinni = DjinniScraper()

    asyncio.run(djinni.fetch())
    end = datetime.now()
    # print(f"Finished in: {end-start}")
