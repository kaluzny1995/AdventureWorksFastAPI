import sqlalchemy
import pymongo
from sqlmodel import SQLModel
from starlette.testclient import TestClient

from app.models import AWFAPIRegisteredUser, Token
from app.providers import BusinessEntityProvider, PersonProvider, PhoneNumberTypeProvider, PersonPhoneProvider
from app.services import AWFAPIUserService

from app.tests.fixtures.fixtures_entry_lists import persons_db, phone_number_types_db, person_phones_db


def create_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.create_all(bind=engine)


def drop_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.drop_all(bind=engine)


def register_test_user(awfapi_user_service: AWFAPIUserService, awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    awfapi_user_service.register_awfapi_user(awfapi_registered_user)


def obtain_access_token(client: TestClient, awfapi_registered_user: AWFAPIRegisteredUser) -> str:
    response = client.post("/token", data={'username': awfapi_registered_user.username,
                                           'password': awfapi_registered_user.password})
    token = Token(**response.json())
    return token.access_token


def insert_test_persons(engine: sqlalchemy.engine.Engine, connection_string: str) -> None:
    person_provider = PersonProvider(connection_string, BusinessEntityProvider(connection_string, engine), engine)
    for person in persons_db:
        person_provider.insert_person(person)


def insert_test_phone_number_types(engine: sqlalchemy.engine.Engine, connection_string: str) -> None:
    phone_number_type_provider = PhoneNumberTypeProvider(connection_string, engine)
    for phone_number_type in phone_number_types_db:
        phone_number_type_provider.insert_phone_number_type(phone_number_type)


def insert_test_person_phones(engine: sqlalchemy.engine.Engine, connection_string: str) -> None:
    person_phone_provider = PersonPhoneProvider(connection_string, engine)
    for person_phone in person_phones_db:
        person_phone_provider.insert_person_phone(person_phone)


def drop_collection(engine: pymongo.MongoClient, name: str) -> None:
    engine.awfapi[name].drop()
