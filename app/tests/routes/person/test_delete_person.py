import pytest
import pymongo
import sqlalchemy
from sqlmodel import create_engine
from typing import List
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig, PostgresdbConnectionConfig
from app.models import ResponseMessage, AWFAPIRegisteredUser, EPersonType, PersonInput, \
    E400BadRequest, E401Unauthorized, E404NotFound
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


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, expected_message", [
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     ResponseMessage(title="Person deleted.",
                     description="Person of given id '{}' deleted.",
                     code=status.HTTP_200_OK))
])
def test_delete_person_should_return_200_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  original_person: PersonInput,
                                                  person_id: int,
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
        person_id = person_provider.insert_person(original_person)

        # Act
        response = client.delete(f"/delete_person/{person_id}",
                                 headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        message = ResponseMessage(**response.json())
        assert message.title == expected_message.title
        assert message.description == expected_message.description.replace("{}", str(person_id))
        assert message.code == expected_message.code

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id,, expected_message", [
    (awfapi_readonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description=f"{E400BadRequest.READONLY_ACCESS_FOR_USER}: "
                                 f"[testuser] Current user 'testuser' has readonly restricted access.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_delete_person_should_return_400_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  original_person: PersonInput,
                                                  person_id: int,
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
        person_id = person_provider.insert_person(original_person)

        # Act
        response = client.delete(f"/delete_person/{person_id}",
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


@pytest.mark.parametrize("original_person, person_id, expected_message", [
    (PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_delete_person_should_return_401_response(client, monkeypatch,
                                                  original_person: PersonInput,
                                                  person_id: int,
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
        person_id = person_provider.insert_person(original_person)

        # Act
        response = client.delete(f"/delete_person/{person_id}")

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


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, expected_message", [
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     ResponseMessage(title="Entity 'Person' of id '-1' not found.",
                     description=f"{E404NotFound.PERSON_NOT_FOUND}: Person of id '-1' does not exist.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_delete_person_should_return_404_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  original_person: PersonInput,
                                                  person_id: int,
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
        person_provider.insert_person(original_person)

        # Act
        response = client.delete(f"/delete_person/{person_id}",
                                 headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        message = ResponseMessage(**response.json()['detail'])
        assert message.title == expected_message.title
        assert message.description == expected_message.description.replace("{}", str(person_id))
        assert message.code == expected_message.code

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
