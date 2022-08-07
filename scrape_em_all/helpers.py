from copy import deepcopy
from datetime import datetime, timedelta

from aiogram import types
from dateutil.relativedelta import relativedelta

# from scrape_em_all.config import tz
from scrape_em_all.models import BaseVacancy, DjinniVacancies, User


def is_user_registered(username: str) -> True | False:
    user = User.objects(username=username).first()
    if user:
        return True

    return False


def register_new_user(message: types.Message) -> User | None:
    username = message.chat.username
    user_tg_id = message.chat.id
    if is_user_registered(username):
        return
    user = User()
    user.username = username
    user.telegram_id = str(user_tg_id)
    user.parsed_vacancies = []
    user.save()
    return user


def date_in_ukrainian_to_datetime(date_to_convert: str) -> datetime:
    # current_year_object is there to copy it and butcher him later
    # to create month objects of current year
    current_year_object = datetime.today()
    dates = {
        "сьогодні": datetime.today(),
        "вчора": datetime.today() - timedelta(days=1),
    }
    months_in_ukrainian = [
        "січня",
        "лютого",
        "березня",
        "квітня",
        "травня",
        "червня",
        "липня",
        "серпня",
        "вересня",
        "жовтня",
        "листопада",
        "грудня",
    ]
    # generating dict values instead of hardcoding into huge dict
    for num, month in enumerate(months_in_ukrainian):
        dates[month] = deepcopy(current_year_object) + relativedelta(month=num + 1)
    try:
        day_from_input, month_from_input = date_to_convert.split(" ")
        tranlate_to_datetime = dates[month_from_input] + relativedelta(
            day=int(day_from_input)
        )
    except ValueError:
        tranlate_to_datetime = dates[date_to_convert]
    return tranlate_to_datetime


def get_user_or_exception(username: str) -> User:
    user = User.objects.get(username=username)
    if not user:
        raise Exception("Such user does not exist")

    return user


def check_if_parsed_entry_exists_in_db(
    vacancies_model: DjinniVacancies, user: User, parsed_data: tuple
) -> True | False:
    """
    Returns True if parsed_data exists in db, False otherwise.
    Function is querying document by page link (it is unique to every parsed element)
    @params: model = EmbeddedDocument instance according to the parsed site
             parsed_data = tuple of parsed_values in fixed schema, ie link would be parsed_data[1]
    Function should be extended for each website accordingly
    """
    if vacancies_model.__name__ == "DjinniVacancies":
        data_exists = DjinniVacancies.objects(parsed_by=user, link=parsed_data[1])
        if data_exists:
            return True
        return False
