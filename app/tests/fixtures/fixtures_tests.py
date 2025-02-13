import sqlalchemy
import pymongo
from typing import List, Tuple
from sqlmodel import SQLModel
from starlette.testclient import TestClient

from app.models import AWFAPIRegisteredUser, Token
from app.providers import (AWFAPIUserProvider,
                           BusinessEntityProvider, PersonProvider, PhoneNumberTypeProvider, PersonPhoneProvider)
from app.services import AWFAPIUserService

from app.tests.fixtures.fixtures_entry_lists import (awfapi_users_db,
                                                     persons_db, phone_number_types_db, person_phones_db)


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


def insert_test_awfapi_users(connection_string: str, collection_name: str, engine: pymongo.MongoClient) -> List[str]:
    awfapi_user_provider = AWFAPIUserProvider(connection_string, collection_name, engine)
    return list(map(lambda audb: awfapi_user_provider.insert_awfapi_user(audb), awfapi_users_db))


def insert_test_persons(engine: sqlalchemy.engine.Engine, connection_string: str) -> List[int]:
    person_provider = PersonProvider(connection_string, BusinessEntityProvider(connection_string, engine), engine)
    return list(map(lambda person: person_provider.insert_person(person), persons_db))


def insert_test_phone_number_types(engine: sqlalchemy.engine.Engine, connection_string: str) -> List[int]:
    phone_number_type_provider = PhoneNumberTypeProvider(connection_string, engine)
    return list(map(lambda phone_number_type: phone_number_type_provider.insert_phone_number_type(phone_number_type), phone_number_types_db))


def insert_test_person_phones(engine: sqlalchemy.engine.Engine, connection_string: str) -> List[Tuple[int, str, int]]:
    person_phone_provider = PersonPhoneProvider(connection_string, engine)
    return list(map(lambda person_phone: person_phone_provider.insert_person_phone(person_phone), person_phones_db))


def drop_collection(engine: pymongo.MongoClient, name: str) -> None:
    engine.awfapi[name].drop()
