import datetime

import mongoengine

from scrape_em_all.config import tz

datetime_with_tz = datetime.datetime.now(tz=tz)


class VacanciesPerSpecialization(mongoengine.EmbeddedDocument):
    user_id = mongoengine.ObjectIdField()
    selected_language = mongoengine.StringField()
    djinni_vacancies = mongoengine.ListField()
    dou_vacancies = mongoengine.ListField()
    robota_vacancies = mongoengine.ListField()
    workua_vacancies = mongoengine.ListField()

    meta = {
        "db_alias": "core",
        "collection": "vacancies",
    }


class User(mongoengine.Document):
    username = mongoengine.StringField(required=True)
    telegram_id = mongoengine.StringField(required=True)
    has_parsed = mongoengine.BooleanField(default=False)
    first_interaction_with_bot = mongoengine.DateTimeField(
        default=datetime_with_tz,
    )
    parsed_vacancies = mongoengine.EmbeddedDocumentListField(VacanciesPerSpecialization)
    meta = {
        "db_alias": "core",
        "collection": "user",
    }
