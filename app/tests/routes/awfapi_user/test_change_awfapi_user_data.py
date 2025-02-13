import pytest
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIUserInput, AWFAPIRegisteredUser, AWFAPIChangedUserData,
                        E400BadRequest, E401Unauthorized, E404NotFound)
from app.factories import MongoDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import (awfapi_user, awfapi_user2,
                                                     awfapi_nonreadonly_user, awfapi_nonreadonly_user2)
from app.tests.fixtures.fixtures_tests import obtain_access_token, drop_collection


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def fixtures_before_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
    monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
    monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data, expected_message", [
    (awfapi_user, awfapi_nonreadonly_user2, "testuser2",
     AWFAPIChangedUserData(full_name="Test User 22", email="test.user22@test.user", is_readonly=False),
     ResponseMessage(title="User data changed.",
                     description="Data of user 'testuser2' changed.",
                     code=status.HTTP_200_OK))
])
def test_change_awfapi_user_data_should_return_200_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData,
                                                            expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}",
                              data=awfapi_changed_user_data.json(),
                              headers={
                                  'Authorization': f"Bearer {access_token}"
                              })

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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data, expected_message", [
    (awfapi_user, awfapi_nonreadonly_user2, "testuser2",
     AWFAPIChangedUserData(full_name="Test User 2", email="test.user@test.user", is_readonly=True),
     ResponseMessage(title="Unique constraint violation. Value 'test.user@test.user' for field 'email' already exists.",
                     description=f"{E400BadRequest.UNIQUE_CONSTRAINT_VIOLATION}: "
                                 f"[email] [test.user@test.user] Field 'email' must have unique values. "
                                 f"Provided email 'test.user@test.user' already exists.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_change_awfapi_user_data_should_return_400_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData,
                                                            expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}",
                              data=awfapi_changed_user_data.json(),
                              headers={
                                  'Authorization': f"Bearer {access_token}"
                              })

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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data, expected_message", [
    (awfapi_user2, awfapi_nonreadonly_user, "testuser2",
     AWFAPIChangedUserData(full_name="Test User 22", email="test.user22@test.user", is_readonly=False),
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_change_awfapi_user_data_should_return_401_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData,
                                                            expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}",
                              data=awfapi_changed_user_data.json())

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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data, expected_message", [
    (awfapi_user2, awfapi_nonreadonly_user, "testuser22",
     AWFAPIChangedUserData(full_name="Test User 22", email="test.user22@test.user", is_readonly=False),
     ResponseMessage(title="Entity 'User' of id 'testuser22' not found.",
                     description=f"{E404NotFound.AWFAPI_USER_NOT_FOUND}: "
                                 f"AWFAPI user of username 'testuser22' does not exist.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_change_awfapi_user_data_should_return_404_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData,
                                                            expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}",
                              data=awfapi_changed_user_data.json(),
                              headers={
                                  'Authorization': f"Bearer {access_token}"
                              })

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
