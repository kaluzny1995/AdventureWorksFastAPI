import pytest
import pymongo
import sqlalchemy
from sqlmodel import create_engine
from typing import List
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig, PostgresdbConnectionConfig
from app.models import ResponseMessage, AWFAPIRegisteredUser, EPersonType, PersonInput, Person
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


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, person", [
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.VC, first_name="Dzh", middle_name="J", last_name="Aw")),
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, name_style="0",
                 title="Mr.", first_name="Dzhejkob", middle_name="J.", last_name="Awaria", suffix="Jr",
                 email_promotion=1,
                 additional_contact_info="<contact_details>?</contact_details>",
                 demographics="<demographic_details>?</demographic_details>"),
     -1,
     PersonInput(person_type=EPersonType.VC, name_style="1",
                 first_name="Dzh", middle_name="JJ.", last_name="Aw", suffix="Jrr",
                 email_promotion=2))
])
def test_update_person_should_return_200_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  original_person: PersonInput,
                                                  person_id: int,
                                                  person: PersonInput) -> None:
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
        origin = person_provider.get_person(person_id)

        # Act
        response = client.put(f"/update_person/{person_id}", data=person.json(),
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        updated_person = Person(**response.json())
        assert updated_person.business_entity_id == origin.business_entity_id
        assert updated_person.person_type == person.person_type
        assert updated_person.name_style == person.name_style
        assert updated_person.title == person.title
        assert updated_person.first_name == person.first_name
        assert updated_person.middle_name == person.middle_name
        assert updated_person.last_name == person.last_name
        assert updated_person.suffix == person.suffix
        assert updated_person.email_promotion == person.email_promotion
        assert updated_person.additional_contact_info == person.additional_contact_info
        assert updated_person.demographics == person.demographics
        assert str(updated_person.rowguid) == origin.rowguid
        assert updated_person.modified_date >= origin.modified_date

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, person, expected_message", [
    (awfapi_readonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.VC, first_name="Dzh", middle_name="J", last_name="Aw"),
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description="Current user 'testuser' has readonly restricted access.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_update_person_should_return_400_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  original_person: PersonInput,
                                                  person_id: int,
                                                  person: PersonInput,
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
        response = client.put(f"/update_person/{person_id}", data=person.json(),
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


@pytest.mark.parametrize("original_person, person_id, person, expected_message", [
    (PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.VC, first_name="Dzh", middle_name="J", last_name="Aw"),
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description="User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_update_person_should_return_401_response(client, monkeypatch,
                                                  original_person: PersonInput,
                                                  person_id: int,
                                                  person: PersonInput,
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
        response = client.put(f"/update_person/{person_id}")

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


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, person, expected_message", [
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.VC, first_name="Dzh", middle_name="J", last_name="Aw"),
     ResponseMessage(title="Person not found.",
                     description="Person of given id '-1' was not found.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_update_person_should_return_404_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  original_person: PersonInput,
                                                  person_id: int,
                                                  person: PersonInput,
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
        response = client.put(f"/update_person/{person_id}", data=person.json(),
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


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, person, expected_message", [
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria", email_promotion=-1),
     ResponseMessage(title="Pydantic validation error: 4 validation errors for Person",
                     description="{'email_promotion': 'ensure this value is greater than or equal to 0'}",
                     code=status.HTTP_422_UNPROCESSABLE_ENTITY)),
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria", email_promotion=3),
     ResponseMessage(title="Pydantic validation error: 4 validation errors for Person",
                     description="{'email_promotion': 'ensure this value is less than or equal to 2'}",
                     code=status.HTTP_422_UNPROCESSABLE_ENTITY))
])
def test_update_person_should_return_422_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  original_person: PersonInput,
                                                  person_id: int,
                                                  person: PersonInput,
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
        response = client.put(f"/update_person/{person_id}", data=person.json(),
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
