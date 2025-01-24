import pytest
import pymongo
import sqlalchemy
from sqlmodel import create_engine
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig, PostgresdbConnectionConfig
from app.models import ResponseMessage, AWFAPIRegisteredUser, PersonPhoneInput, \
    E400BadRequest, E401Unauthorized, E404NotFound
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


@pytest.mark.parametrize("awfapi_registered_user, original_person_phone, "
                         "person_id, phone_number, phone_number_type_id, "
                         "expected_message", [
    (awfapi_nonreadonly_user,
     PersonPhoneInput(business_entity_id=2, phone_number="123456789", phone_number_type_id=1),
     2, "123456789", 1,
     ResponseMessage(title="Person phone deleted.",
                     description=f"Person phone of given id '(2, \'123456789\', 1)' deleted.",
                     code=status.HTTP_200_OK))
])
def test_delete_person_phone_should_return_200_response(client, monkeypatch,
                                                        awfapi_registered_user: AWFAPIRegisteredUser,
                                                        original_person_phone: PersonPhoneInput,
                                                        person_id: int, phone_number: str, phone_number_type_id: int,
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

        person_phone_provider.insert_person_phone(original_person_phone)

        # Act
        response = client.delete(f"/delete_person_phone/{person_id}/{phone_number}/{phone_number_type_id}",
                                 headers={'Authorization': f"Bearer {access_token}"})

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


@pytest.mark.parametrize("awfapi_registered_user, original_person_phone, "
                         "person_id, phone_number, phone_number_type_id, "
                         "expected_message", [
    (awfapi_readonly_user,
     PersonPhoneInput(business_entity_id=2, phone_number="123456789", phone_number_type_id=1),
     2, "123456789", 1,
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description=f"{E400BadRequest.READONLY_ACCESS_FOR_USER}: "
                                 f"[testuser] Current user 'testuser' has readonly restricted access.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user,
     PersonPhoneInput(business_entity_id=2, phone_number="123456789", phone_number_type_id=1),
     2, "123456789", 1,
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description=f"{E400BadRequest.READONLY_ACCESS_FOR_USER}: "
                                 f"[testuser] Current user 'testuser' has readonly restricted access.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user,
     PersonPhoneInput(business_entity_id=2, phone_number="123456789", phone_number_type_id=1),
     2, "", 1,
     ResponseMessage(title="Empty string in positional parameter.",
                     description=f"{E400BadRequest.EMPTY_STRING_IN_PARAMETER}: "
                                 f"Each of the positional endpoint parameters cannot be empty string.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_delete_person_phone_should_return_400_response(client, monkeypatch,
                                                        awfapi_registered_user: AWFAPIRegisteredUser,
                                                        original_person_phone: PersonPhoneInput,
                                                        person_id: int, phone_number: str, phone_number_type_id: int,
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

        person_phone_provider.insert_person_phone(original_person_phone)

        # Act
        response = client.delete(f"/delete_person_phone/{person_id}/{phone_number}/{phone_number_type_id}",
                                 headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        json_object = response.json() if 'detail' not in response.json() else response.json()['detail']
        message = ResponseMessage(**json_object)
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


@pytest.mark.parametrize("original_person_phone, "
                         "person_id, phone_number, phone_number_type_id, "
                         "expected_message", [
    (PersonPhoneInput(business_entity_id=2, phone_number="123456789", phone_number_type_id=1),
     2, "123456789", 1,
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_delete_person_phone_should_return_401_response(client, monkeypatch,
                                                        original_person_phone: PersonPhoneInput,
                                                        person_id: int, phone_number: str, phone_number_type_id: int,
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

        person_phone_provider.insert_person_phone(original_person_phone)

        # Act
        response = client.delete(f"/delete_person_phone/{person_id}/{phone_number}/{phone_number_type_id}")

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


@pytest.mark.parametrize("awfapi_registered_user, original_person_phone, "
                         "person_id, phone_number, phone_number_type_id, "
                         "expected_message", [
    (awfapi_nonreadonly_user,
     PersonPhoneInput(business_entity_id=2, phone_number="123456789", phone_number_type_id=1),
     -1, "0", -1,
     ResponseMessage(title="Entity 'Person phone' of id '(-1, \'0\', -1)' not found.",
                     description=f"{E404NotFound.PERSON_PHONE_NOT_FOUND}: Person phone of id '(-1, \'0\', -1)' does not exist.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_delete_person_phone_should_return_404_response(client, monkeypatch,
                                                        awfapi_registered_user: AWFAPIRegisteredUser,
                                                        original_person_phone: PersonPhoneInput,
                                                        person_id: int, phone_number: str, phone_number_type_id: int,
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

        person_phone_provider.insert_person_phone(original_person_phone)

        # Act
        response = client.delete(f"/delete_person_phone/{person_id}/{phone_number}/{phone_number_type_id}",
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
