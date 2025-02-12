import pytest
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIRegisteredUser, EPersonType, PersonInput, Person,
                        E400BadRequest, E401Unauthorized, E404NotFound, E422UnprocessableEntity)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PersonFactory)

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person as person_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token, insert_test_persons,
                                               create_tables, drop_tables, drop_collection)


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)

postgresdb_connection_string, postgresdb_engine = PostgresDBFactory.get_db_connection_details(test_suffix="_test")
person_provider = PersonFactory.get_provider(postgresdb_connection_string, postgresdb_engine)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def fixtures_before_test(monkeypatch: MonkeyPatch) -> None:
    create_tables(postgresdb_engine)

    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
    monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
    monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

    monkeypatch.setattr(person_routes, 'person_provider', person_provider)

    insert_test_persons(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)
    drop_tables(postgresdb_engine)


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
        fixtures_before_test(monkeypatch)
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
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, person, expected_message", [
    (awfapi_readonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.VC, first_name="Dzh", middle_name="J", last_name="Aw"),
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description=f"{E400BadRequest.READONLY_ACCESS_FOR_USER}: "
                                 f"[testuser] Current user 'testuser' has readonly restricted access.",
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
        fixtures_before_test(monkeypatch)
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
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("original_person, person_id, person, expected_message", [
    (PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.VC, first_name="Dzh", middle_name="J", last_name="Aw"),
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_update_person_should_return_401_response(client, monkeypatch,
                                                  original_person: PersonInput,
                                                  person_id: int,
                                                  person: PersonInput,
                                                  expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        person_id = person_provider.insert_person(original_person)

        # Act
        response = client.put(f"/update_person/{person_id}")

        # Assert
        message = ResponseMessage(**response.json())
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, person, expected_message", [
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.VC, first_name="Dzh", middle_name="J", last_name="Aw"),
     ResponseMessage(title="Entity 'Person' of id '-1' not found.",
                     description=f"{E404NotFound.PERSON_NOT_FOUND}: Person of id '-1' does not exist.",
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
        fixtures_before_test(monkeypatch)
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
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, original_person, person_id, person, expected_message", [
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria", email_promotion=-1),
     ResponseMessage(title="Pydantic validation error: 4 validation errors for Person | "
                           "{'email_promotion': 'ensure this value is greater than or equal to 0'}",
                     description=f"{E422UnprocessableEntity.INVALID_PERSON_VALUES}: "
                                 f"4 validation errors for Person\n"
                                 f"business_entity_id\n"
                                 f"  field required (type=value_error.missing)\n"
                                 f"email_promotion\n"
                                 f"  ensure this value is greater than or equal to 0 (type=value_error.number.not_ge; limit_value=0)\n"
                                 f"rowguid\n"
                                 f"  field required (type=value_error.missing)\n"
                                 f"modified_date\n"
                                 f"  field required (type=value_error.missing)",
                     code=status.HTTP_422_UNPROCESSABLE_ENTITY)),
    (awfapi_nonreadonly_user,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria"),
     -1,
     PersonInput(person_type=EPersonType.GC, first_name="Dzhejkob", last_name="Awaria", email_promotion=3),
     ResponseMessage(title="Pydantic validation error: 4 validation errors for Person | "
                           "{'email_promotion': 'ensure this value is less than or equal to 2'}",
                     description=f"{E422UnprocessableEntity.INVALID_PERSON_VALUES}: "
                                 f"4 validation errors for Person\n"
                                 f"business_entity_id\n"
                                 f"  field required (type=value_error.missing)\n"
                                 f"email_promotion\n"
                                 f"  ensure this value is less than or equal to 2 (type=value_error.number.not_le; limit_value=2)\n"
                                 f"rowguid\n"
                                 f"  field required (type=value_error.missing)\n"
                                 f"modified_date\n"
                                 f"  field required (type=value_error.missing)",
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
        fixtures_before_test(monkeypatch)
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
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()
