from aiogram import types

from scrape_em_all.models import User


def is_user_registered(username: str):
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
