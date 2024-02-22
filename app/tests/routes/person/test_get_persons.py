import pytest
import pymongo
import sqlalchemy
from sqlmodel import create_engine
from typing import Optional, List
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig, PostgresdbConnectionConfig
from app.models import ResponseMessage, AWFAPIRegisteredUser, EOrderType, EPersonType, PersonInput, Person
from app.providers import AWFAPIUserProvider, BusinessEntityProvider, PersonProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person as person_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token,
                                               create_tables, drop_tables, drop_collection)


mongodb_connection_string: str = MongodbConnectionConfig.get_db_connection_string()
mongodb_collection_name: str = MongodbConnectionConfig.get_collection_name(test_suffix="_test")
mongodb_engine: pymongo.MongoClient = pymongo.MongoClient(mongodb_connection_string)
awfapi_user_provider: AWFAPIUserProvider = AWFAPIUserProvider(
    connection_string=mongodb_connection_string,
    collection_name=mongodb_collection_name,
    db_engine=mongodb_engine
)
awfapi_user_service: AWFAPIUserService = AWFAPIUserService(awfapi_user_provider=awfapi_user_provider)
jwt_authentication_service: JWTAuthenticationService = JWTAuthenticationService(
    jwt_auth_config=JWTAuthenticationConfig.from_json(),
    awfapi_user_provider=awfapi_user_provider,
    awfapi_user_service=awfapi_user_service
)

postgresdb_connection_string: str = PostgresdbConnectionConfig.get_db_connection_string(test_suffix="_test")
postgresdb_engine: sqlalchemy.engine.Engine = create_engine(postgresdb_connection_string)
business_entity_provider: BusinessEntityProvider = BusinessEntityProvider(
    connection_string=postgresdb_connection_string,
    db_engine=postgresdb_engine
)
person_provider: PersonProvider = PersonProvider(
    connection_string=postgresdb_connection_string,
    business_entity_provider=business_entity_provider,
    db_engine=postgresdb_engine
)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


awfapi_nonreadonly_user: AWFAPIRegisteredUser = AWFAPIRegisteredUser(username="testuser", password="testpassword",
                                                                     repeated_password="testpassword",
                                                                     full_name="Test AWFAPIUserInput",
                                                                     email="test.user@test.user", is_readonly=False)
awfapi_readonly_user: AWFAPIRegisteredUser = AWFAPIRegisteredUser(username="testuser", password="testpassword",
                                                                  repeated_password="testpassword",
                                                                  full_name="Test AWFAPIUserInput",
                                                                  email="test.user@test.user", is_readonly=True)
persons_db: List[PersonInput] = [
    PersonInput(person_type=EPersonType.GC, first_name="John", last_name="Doe"),
    PersonInput(person_type=EPersonType.EM, first_name="John", last_name="Smith"),
    PersonInput(person_type=EPersonType.IN, first_name="John", last_name="Adams"),
    PersonInput(person_type=EPersonType.VC, first_name="John", middle_name="K", last_name="Adams"),
    PersonInput(person_type=EPersonType.SP, first_name="John", middle_name="J", last_name="Adams"),
    PersonInput(person_type=EPersonType.GC, first_name="Brian", last_name="Washer"),
    PersonInput(person_type=EPersonType.SC, first_name="Aaron", last_name="Dasmi"),
    PersonInput(person_type=EPersonType.SC, first_name="Aaron", last_name="Washington"),
    PersonInput(person_type=EPersonType.SC, first_name="Sharon", last_name="Smith"),
    PersonInput(person_type=EPersonType.SC, first_name="Claire", last_name="Smith"),
]


@pytest.mark.parametrize("awfapi_registered_user, filters, order_by, order_type, offset, limit, expected_persons", [
    (awfapi_nonreadonly_user, None, None, "asc", 0, 3, [persons_db[0], persons_db[1], persons_db[2]]),
    (awfapi_nonreadonly_user, None, None, "asc", 1, 1, [persons_db[1]]),
    (awfapi_readonly_user, None, None, "asc", 0, 3, [persons_db[0], persons_db[1], persons_db[2]]),
    (awfapi_nonreadonly_user, "person_type:GC", None, "asc", 0, 10, [persons_db[0], persons_db[5]]),
    (awfapi_nonreadonly_user, "person_type:SC,last_name_phrase:smi", None, "asc", 0, 10, [persons_db[6], persons_db[8], persons_db[9]]),
    (awfapi_nonreadonly_user, "person_type:SC,first_name_phrase:ron,last_name_phrase:smi", None, "asc", 0, 10, [persons_db[6], persons_db[8]]),
    (awfapi_nonreadonly_user, "first_name_phrase:john", "full_name", "asc", 0, 10, [persons_db[4], persons_db[3], persons_db[2], persons_db[0], persons_db[1]]),
    (awfapi_nonreadonly_user, "first_name_phrase:john", "full_name", "asc", 0, 3, [persons_db[4], persons_db[3], persons_db[2]]),
    (awfapi_nonreadonly_user, "first_name_phrase:john", "full_name", "asc", 2, 3, [persons_db[2], persons_db[0], persons_db[1]]),
    (awfapi_nonreadonly_user, "first_name_phrase:john", "person_type", "desc", 0, 10, [persons_db[3], persons_db[4], persons_db[2], persons_db[0], persons_db[1]]),
])
def test_get_persons_should_return_200_response(client, monkeypatch,
                                                awfapi_registered_user: AWFAPIRegisteredUser,
                                                filters: Optional[str],
                                                order_by: Optional[str], order_type: Optional[EOrderType],
                                                offset: int, limit: int,
                                                expected_persons: List[PersonInput]) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(person_routes, 'person_provider', person_provider)

        for pdb in persons_db:
            person_provider.insert_person(pdb)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/get_persons",
                              params={'filters': filters,
                                      'order_by': order_by, 'order_type': order_type,
                                      'offset': offset, 'limit': limit},
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_dict = response.json()
        persons = list(map(lambda rd: Person(**rd), response_dict))
        assert len(persons) == len(expected_persons)
        for p, ep in zip(persons, expected_persons):
            print("Persons:", p.dict(), ep.dict())
            assert p.business_entity_id is not None
            assert p.person_type == ep.person_type
            assert p.name_style == ep.name_style
            assert p.title == ep.title
            assert p.first_name == ep.first_name
            assert p.middle_name == ep.middle_name
            assert p.last_name == ep.last_name
            assert p.suffix == ep.suffix
            assert p.email_promotion == ep.email_promotion
            assert p.additional_contact_info == ep.additional_contact_info
            assert p.demographics == ep.demographics
            assert p.rowguid is not None
            assert p.modified_date is not None

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, filters, order_by, order_type, offset, limit, expected_message", [
    (awfapi_readonly_user, None, None, "asc", -1, 0,
     ResponseMessage(title="Invalid value for SQL clause.",
                     description="Value '-1' is invalid for SKIP clause.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, None, None, "asc", 0, -1,
     ResponseMessage(title="Invalid value for SQL clause.",
                     description="Value '-1' is invalid for LIMIT clause.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "last_name:pph", None, "asc", 0, 0,
     ResponseMessage(title="Non-existing fields in filter string.",
                     description="Filter string contains fields: '['last_name']' some of which "
                                 "do not exist in person filtering fields: "
                                 "['person_type', 'first_name_phrase', 'last_name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "last_name_phrase:pph,first_name:ffh", None, "asc", 0, 0,
     ResponseMessage(title="Non-existing fields in filter string.",
                     description="Filter string contains fields: '['last_name_phrase', 'first_name']' some of which "
                                 "do not exist in person filtering fields: "
                                 "['person_type', 'first_name_phrase', 'last_name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "pers_type:GC", None, "asc", 0, 0,
     ResponseMessage(title="Non-existing fields in filter string.",
                     description="Filter string contains fields: '['pers_type']' some of which "
                                 "do not exist in person filtering fields: "
                                 "['person_type', 'first_name_phrase', 'last_name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_type", None, "asc", 0, 0,
     ResponseMessage(title="Invalid filter string.",
                     description="Invalid filter string: person_type.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_type:SC,last_name_phrase", None, "asc", 0, 0,
     ResponseMessage(title="Invalid filter string.",
                     description="Invalid filter string: person_type:SC,last_name_phrase.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, None, "name", "asc", 0, 0,
     ResponseMessage(title="Non-existing column for ordering.",
                     description="Column does not exist in persons view ('name').",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, None, "additional_contact_info", "asc", 0, 0,
     ResponseMessage(title="Unsupported ordering for this data type.",
                     description="Cannot order by column 'additional_contact_info'. "
                                 "PostgreSQL does not support ordering for 'xml' data type.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, None, "demographics", "asc", 0, 0,
     ResponseMessage(title="Unsupported ordering for this data type.",
                     description="Cannot order by column 'demographics'. "
                                 "PostgreSQL does not support ordering for 'xml' data type.",
                     code=status.HTTP_400_BAD_REQUEST)),
])
def test_get_persons_should_return_400_response(client, monkeypatch,
                                                awfapi_registered_user: AWFAPIRegisteredUser,
                                                filters: Optional[str],
                                                order_by: Optional[str], order_type: Optional[EOrderType],
                                                offset: int, limit: int,
                                                expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(person_routes, 'person_provider', person_provider)

        for pdb in persons_db:
            person_provider.insert_person(pdb)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/get_persons",
                              params={'filters': filters,
                                      'order_by': order_by, 'order_type': order_type,
                                      'offset': offset, 'limit': limit},
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        message = ResponseMessage(**response.json()['detail'])
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("filters, order_by, order_type, offset, limit, expected_message", [
    (None, None, "asc", 0, 3,
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description="User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_get_persons_should_return_401_response(client, monkeypatch,
                                                filters: Optional[str],
                                                order_by: Optional[str], order_type: Optional[EOrderType],
                                                offset: int, limit: int,
                                                expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(person_routes, 'person_provider', person_provider)

        for pdb in persons_db:
            person_provider.insert_person(pdb)

        # Act
        response = client.get("/get_persons",
                              params={'filters': filters,
                                      'order_by': order_by, 'order_type': order_type,
                                      'offset': offset, 'limit': limit})

        # Assert
        message = ResponseMessage(**response.json())
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
