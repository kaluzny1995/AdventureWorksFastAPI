import pytest
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIRegisteredUser, PersonPhoneInput, PersonPhone,
                        E401Unauthorized, E404NotFound, E400BadRequest)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PersonPhoneFactory)

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person_phone as person_phone_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user, person_phones_db
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token,
                                               insert_test_persons, insert_test_phone_number_types,
                                               insert_test_person_phones,
                                               create_tables, drop_tables, drop_collection)


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)

postgresdb_connection_string, postgresdb_engine = PostgresDBFactory.get_db_connection_details(test_suffix="_test")
person_phone_provider = PersonPhoneFactory.get_provider(postgresdb_connection_string, postgresdb_engine)


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

    monkeypatch.setattr(person_phone_routes, 'person_phone_provider', person_phone_provider)

    insert_test_persons(postgresdb_engine, postgresdb_connection_string)
    insert_test_phone_number_types(postgresdb_engine, postgresdb_connection_string)
    insert_test_person_phones(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)
    drop_tables(postgresdb_engine)


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
        fixtures_before_test(monkeypatch)
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
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, person_id, phone_number, phone_number_type_id, expected_message", [
    (awfapi_readonly_user, -1, "", -1,
     ResponseMessage(title="Empty string in positional parameter.",
                     description=f"{E400BadRequest.EMPTY_STRING_IN_PARAMETER}: "
                                 f"Each of the positional endpoint parameters cannot be empty string.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_get_person_phone_should_return_400_response(client, monkeypatch,
                                                     awfapi_registered_user: AWFAPIRegisteredUser,
                                                     person_id: int, phone_number: str, phone_number_type_id: int,
                                                     expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/get_person_phone/{person_id}/{phone_number}/{phone_number_type_id}",
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        json_object = response.json() if 'detail' not in response.json() else response.json()['detail']
        message = ResponseMessage(**json_object)
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


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
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get(f"/get_person_phone/{person_id}/{phone_number}/{phone_number_type_id}")

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
        fixtures_before_test(monkeypatch)
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
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()
