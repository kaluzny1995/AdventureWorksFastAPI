import pytest
import pymongo
import sqlalchemy
from sqlmodel import create_engine
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig, PostgresdbConnectionConfig
from app.models import ResponseMessage, AWFAPIRegisteredUser, PersonPhoneInput, PersonPhone, \
    E401Unauthorized, E404NotFound
from app.providers import AWFAPIUserProvider, PersonPhoneProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person_phone as person_phone_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user, person_phones_db
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


@pytest.mark.parametrize("awfapi_registered_user, person_id, phone_number, phone_number_type_id, expected_person_phone", [
    (awfapi_nonreadonly_user, 1, "000 000 000", 1, person_phones_db[0]),
    (awfapi_nonreadonly_user, 4, "123456789", 3, person_phones_db[3]),
    (awfapi_readonly_user, 8, "000 000 000", 5, person_phones_db[7])
])
def test_get_person_phone_should_return_200_response(client, monkeypatch,
                                                     awfapi_registered_user: AWFAPIRegisteredUser,
                                                     person_id: int, phone_number: str, phone_number_type_id: int,
                                                     expected_person_phone: PersonPhoneInput) -> None:
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
        response = client.get(f"/get_person_phone/{person_id}/{phone_number}/{phone_number_type_id}",
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        person_phone = PersonPhone(**response.json()[0])
        assert person_phone.business_entity_id == expected_person_phone.business_entity_id
        assert person_phone.phone_number == expected_person_phone.phone_number
        assert person_phone.phone_number_type_id == expected_person_phone.phone_number_type_id
        assert person_phone.modified_date is not None

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("person_id, phone_number, phone_number_type_id, expected_message", [
    (0, "0", 0, ResponseMessage(title="JWT token not provided or wrong encoded.",
                               description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                           f"User did not provide or the JWT token is wrongly encoded.",
                               code=status.HTTP_401_UNAUTHORIZED))
])
def test_get_person_phone_should_return_401_response(client, monkeypatch,
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

        # Act
        response = client.get(f"/get_person_phone/{person_id}/{phone_number}/{phone_number_type_id}")

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


@pytest.mark.parametrize("awfapi_registered_user, person_id, phone_number, phone_number_type_id, expected_message", [
    (awfapi_readonly_user, -1, "0", -1,
     ResponseMessage(title="Entity 'Person phone' of id '(-1, \'0\', -1)' not found.",
                     description=f"{E404NotFound.PERSON_PHONE_NOT_FOUND}: Person phone of id '(-1, \'0\', -1)' does not exist.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_get_person_phone_should_return_404_response(client, monkeypatch,
                                                     awfapi_registered_user: AWFAPIRegisteredUser,
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

        # Act
        response = client.get(f"/get_person_phone/{person_id}/{phone_number}/{phone_number_type_id}",
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
