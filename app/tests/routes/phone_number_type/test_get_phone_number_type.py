import pytest
import pymongo
import sqlalchemy
from sqlmodel import create_engine
from typing import List
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig, PostgresdbConnectionConfig
from app.models import ResponseMessage, AWFAPIRegisteredUser, PhoneNumberTypeInput, PhoneNumberType, \
    E401Unauthorized, E404NotFound
from app.providers import AWFAPIUserProvider, PhoneNumberTypeProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import phone_number_type as phone_number_type_routes
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
phone_number_type_provider: PhoneNumberTypeProvider = PhoneNumberTypeProvider(
    connection_string=postgresdb_connection_string,
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
phone_number_types_db: List[PhoneNumberTypeInput] = [
    PhoneNumberTypeInput(name="Cell"),
    PhoneNumberTypeInput(name="Mobile"),
    PhoneNumberTypeInput(name="Home"),
    PhoneNumberTypeInput(name="Home 2"),
    PhoneNumberTypeInput(name="Home em."),
]


@pytest.mark.parametrize("awfapi_registered_user, phone_number_type_id, expected_phone_number_type", [
    (awfapi_nonreadonly_user, 0, phone_number_types_db[0]),
    (awfapi_nonreadonly_user, 2, phone_number_types_db[2]),
    (awfapi_readonly_user, 4, phone_number_types_db[4])
])
def test_get_phone_number_type_should_return_200_response(client, monkeypatch,
                                                          awfapi_registered_user: AWFAPIRegisteredUser,
                                                          phone_number_type_id: int,
                                                          expected_phone_number_type: PhoneNumberTypeInput) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(phone_number_type_routes, 'phone_number_type_provider', phone_number_type_provider)

        phone_number_type_db_ids = list([phone_number_type_provider.insert_phone_number_type(pntdb)
                                         for pntdb in phone_number_types_db])
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/get_phone_number_type/{phone_number_type_db_ids[phone_number_type_id]}",
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        phone_numer_type = PhoneNumberType(**response.json())
        assert phone_numer_type.phone_number_type_id is not None
        assert phone_numer_type.name == expected_phone_number_type.name
        assert phone_numer_type.modified_date is not None

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("phone_number_type_id, expected_message", [
    (0, ResponseMessage(title="JWT token not provided or wrong encoded.",
                        description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                    f"User did not provide or the JWT token is wrongly encoded.",
                        code=status.HTTP_401_UNAUTHORIZED))
])
def test_get_phone_number_type_should_return_401_response(client, monkeypatch,
                                                          phone_number_type_id: int,
                                                          expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(phone_number_type_routes, 'phone_number_type_provider', phone_number_type_provider)

        phone_number_type_db_ids = list([phone_number_type_provider.insert_phone_number_type(pntdb)
                                         for pntdb in phone_number_types_db])

        # Act
        response = client.get(f"/get_phone_number_type/{phone_number_type_db_ids[phone_number_type_id]}")

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


@pytest.mark.parametrize("awfapi_registered_user, phone_number_type_id, expected_message", [
    (awfapi_readonly_user, -1,
     ResponseMessage(title="Entity 'Phone number type' of id '-1' not found.",
                     description=f"{E404NotFound.PHONE_NUMBER_TYPE_NOT_FOUND}: Phone number type of id '-1' does not exist.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_get_phone_number_type_should_return_404_response(client, monkeypatch,
                                                          awfapi_registered_user: AWFAPIRegisteredUser,
                                                          phone_number_type_id: int,
                                                          expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        monkeypatch.setattr(phone_number_type_routes, 'phone_number_type_provider', phone_number_type_provider)

        _ = list([phone_number_type_provider.insert_phone_number_type(pntdb) for pntdb in phone_number_types_db])
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/get_phone_number_type/{phone_number_type_id}",
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
