import pytest
import pymongo
import sqlalchemy
from sqlmodel import create_engine
from typing import Optional
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig, PostgresdbConnectionConfig
from app.models import CountMessage, ResponseMessage, AWFAPIRegisteredUser, \
    E400BadRequest, E401Unauthorized
from app.providers import AWFAPIUserProvider, PersonPhoneProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person_phone as person_phone_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token,
                                               insert_test_persons, insert_test_phone_number_types,
                                               insert_test_person_phones,
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
person_phone_provider: PersonPhoneProvider = PersonPhoneProvider(
    connection_string=postgresdb_connection_string,
    db_engine=postgresdb_engine
)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("awfapi_registered_user, filters, expected_message", [
    (awfapi_nonreadonly_user, None, CountMessage(entity="Person phone", count=8)),
    (awfapi_readonly_user, None, CountMessage(entity="Person phone", count=8)),
    (awfapi_nonreadonly_user, "person_ids:[1|2|3|4]", CountMessage(entity="Person phone", count=4)),
    (awfapi_nonreadonly_user, "phone_number_type_ids:[1|2]", CountMessage(entity="Person phone", count=3)),
    (awfapi_nonreadonly_user, "person_ids:[4|5],phone_number_type_ids:[3]", CountMessage(entity="Person phone", count=2)),
])
def test_count_person_phones_should_return_200_response(client, monkeypatch,
                                                        awfapi_registered_user: AWFAPIRegisteredUser,
                                                        filters: Optional[str],
                                                        expected_message: CountMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(person_phone_routes, 'person_phone_provider', person_phone_provider)

        # todo: move that to common method insert objects
        insert_test_persons(postgresdb_engine, postgresdb_connection_string)
        insert_test_phone_number_types(postgresdb_engine, postgresdb_connection_string)
        insert_test_person_phones(postgresdb_engine, postgresdb_connection_string)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/count_person_phones", params={'filters': filters},
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        message = CountMessage(**response.json())
        assert message.entity == expected_message.entity
        assert message.count == expected_message.count

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, filters, expected_message", [
    (awfapi_readonly_user, "person_id:[20785|20777]",
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['person_id']' some of which "
                                 f"do not exist in person phone filtering fields: "
                                 f"['person_ids', 'phone_number_type_ids'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids:[20785|20777],phone_number_type_id:[1|2]",
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['person_ids', 'phone_number_type_id']' some of which "
                                 f"do not exist in person phone filtering fields: "
                                 f"['person_ids', 'phone_number_type_ids'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids",
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Invalid filter string: person_ids.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids:[20785[20777|20776|20775|20774]",
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Wrong value of list items: '20785[20777|20776|20775|20774'. Cannot contain '[' or ']'.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids:[20785,20777|20776|20775|20774],phone_number_type_ids:[1|2]",
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Invalid filter string: person_ids:[20785,20777|20776|20775|20774],phone_number_type_ids:[1|2].",
                     code=status.HTTP_400_BAD_REQUEST)),
])
def test_count_person_phones_should_return_400_response(client, monkeypatch,
                                                        awfapi_registered_user: AWFAPIRegisteredUser,
                                                        filters: Optional[str],
                                                        expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(person_phone_routes, 'person_phone_provider', person_phone_provider)

        # todo: move that to common method insert objects
        insert_test_persons(postgresdb_engine, postgresdb_connection_string)
        insert_test_phone_number_types(postgresdb_engine, postgresdb_connection_string)
        insert_test_person_phones(postgresdb_engine, postgresdb_connection_string)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/count_person_phones", params={'filters': filters},
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


@pytest.mark.parametrize("filters, expected_message", [
    (None,
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_count_person_phones_should_return_401_response(client, monkeypatch,
                                                        filters: Optional[str],
                                                        expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(person_phone_routes, 'person_phone_provider', person_phone_provider)

        # todo: move that to common method insert objects
        insert_test_persons(postgresdb_engine, postgresdb_connection_string)
        insert_test_phone_number_types(postgresdb_engine, postgresdb_connection_string)
        insert_test_person_phones(postgresdb_engine, postgresdb_connection_string)

        # Act
        response = client.get("/count_person_phones", params={'filters': filters})

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
