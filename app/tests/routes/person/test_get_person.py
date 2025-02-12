import pytest
from typing import List
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIRegisteredUser, PersonInput, Person,
                        E401Unauthorized, E404NotFound)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PersonFactory)

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person as person_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user, persons_db
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


def fixtures_before_test(monkeypatch: MonkeyPatch) -> List[int]:
    create_tables(postgresdb_engine)

    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
    monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
    monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

    monkeypatch.setattr(person_routes, 'person_provider', person_provider)

    return insert_test_persons(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)
    drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, person_id, expected_person", [
    (awfapi_nonreadonly_user, 0, persons_db[0]),
    (awfapi_nonreadonly_user, 3, persons_db[3]),
    (awfapi_readonly_user, 7, persons_db[7])
])
def test_get_person_should_return_200_response(client, monkeypatch,
                                               awfapi_registered_user: AWFAPIRegisteredUser,
                                               person_id: int,
                                               expected_person: PersonInput) -> None:
    try:
        # Arrange
        person_db_ids = fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/get_person/{person_db_ids[person_id]}",
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        person = Person(**response.json())
        assert person.business_entity_id is not None
        assert person.person_type == expected_person.person_type
        assert person.name_style == expected_person.name_style
        assert person.title == expected_person.title
        assert person.first_name == expected_person.first_name
        assert person.middle_name == expected_person.middle_name
        assert person.last_name == expected_person.last_name
        assert person.suffix == expected_person.suffix
        assert person.email_promotion == expected_person.email_promotion
        assert person.additional_contact_info == expected_person.additional_contact_info
        assert person.demographics == expected_person.demographics
        assert person.rowguid is not None
        assert person.modified_date is not None

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("person_id, expected_message", [
    (0, ResponseMessage(title="JWT token not provided or wrong encoded.",
                        description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                    f"User did not provide or the JWT token is wrongly encoded.",
                        code=status.HTTP_401_UNAUTHORIZED))
])
def test_get_person_should_return_401_response(client, monkeypatch,
                                               person_id: int,
                                               expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        person_db_ids = fixtures_before_test(monkeypatch)

        # Act
        response = client.get(f"/get_person/{person_db_ids[person_id]}")

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


@pytest.mark.parametrize("awfapi_registered_user, person_id, expected_message", [
    (awfapi_readonly_user, -1,
     ResponseMessage(title="Entity 'Person' of id '-1' not found.",
                     description=f"{E404NotFound.PERSON_NOT_FOUND}: Person of id '-1' does not exist.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_get_person_should_return_404_response(client, monkeypatch,
                                               awfapi_registered_user: AWFAPIRegisteredUser,
                                               person_id: int,
                                               expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        _ = fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/get_person/{person_id}", headers={'Authorization': f"Bearer {access_token}"})

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
