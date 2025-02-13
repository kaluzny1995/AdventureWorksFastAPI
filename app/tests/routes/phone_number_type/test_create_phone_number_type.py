import pytest
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIRegisteredUser, PhoneNumberTypeInput, PhoneNumberType, 
                        E400BadRequest, E401Unauthorized)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PhoneNumberTypeFactory)

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import phone_number_type as phone_number_type_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token, insert_test_phone_number_types,
                                               create_tables, drop_tables, drop_collection)


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)

postgresdb_connection_string, postgresdb_engine = PostgresDBFactory.get_db_connection_details(test_suffix="_test")
phone_number_type_provider = PhoneNumberTypeFactory.get_provider(postgresdb_connection_string, postgresdb_engine)


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

    monkeypatch.setattr(phone_number_type_routes, 'phone_number_type_provider', phone_number_type_provider)

    insert_test_phone_number_types(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)
    drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, phone_number_type", [
    (awfapi_nonreadonly_user, PhoneNumberTypeInput(name="Cell 2"))
])
def test_create_phone_number_type_should_return_201_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             phone_number_type: PhoneNumberTypeInput) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.post(f"/create_phone_number_type", data=phone_number_type.json(),
                               headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        new_phone_number_type = PhoneNumberType(**response.json())
        assert new_phone_number_type.phone_number_type_id is not None
        assert new_phone_number_type.name == phone_number_type.name
        assert new_phone_number_type.modified_date is not None

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, phone_number_type, expected_message", [
    (awfapi_readonly_user,
     PhoneNumberTypeInput(name="Cell 2"),
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description=f"{E400BadRequest.READONLY_ACCESS_FOR_USER}: "
                                 f"[testuser] Current user 'testuser' has readonly restricted access.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_create_phone_number_type_should_return_400_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             phone_number_type: PhoneNumberTypeInput,
                                                             expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.post("/create_phone_number_type", data=phone_number_type.json(),
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


@pytest.mark.parametrize("phone_number_type, expected_message", [
    (PhoneNumberTypeInput(name="Cell 2"),
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_create_phone_number_type_should_return_401_response(client, monkeypatch,
                                                             phone_number_type: PhoneNumberTypeInput,
                                                             expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)

        # Act
        response = client.post(f"/create_phone_number_type", data=phone_number_type.json())

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
