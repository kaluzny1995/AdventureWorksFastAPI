import pytest
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIUserInput, AWFAPIRegisteredUser,
                        E400BadRequest)
from app.factories import MongoDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_user
from app.tests.fixtures.fixtures_tests import drop_collection


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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, expected_message", [
    (awfapi_user,
     AWFAPIRegisteredUser(username="testuser2", password="testpassword", repeated_password="testpassword",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=True),
     ResponseMessage(title="User registered.",
                     description="New user 'testuser2' registered.",
                     code=status.HTTP_201_CREATED))
])
def test_register_awfapi_user_should_return_201_response(client, monkeypatch,
                                                         existing_awfapi_user: AWFAPIUserInput,
                                                         awfapi_registered_user: AWFAPIRegisteredUser,
                                                         expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)

        # Act
        response = client.post("/register_awfapi_user", data=awfapi_registered_user.json())

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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, expected_message", [
    (awfapi_user,
     AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     ResponseMessage(title="Unique constraint violation. Value 'testuser' for field 'username' already exists.",
                     description=f"{E400BadRequest.UNIQUE_CONSTRAINT_VIOLATION}: "
                                 f"[username] [testuser] Field 'username' must have unique values. "
                                 f"Provided username 'testuser' already exists.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_user,
     AWFAPIRegisteredUser(username="testuser2", password="testpassword", repeated_password="testpassword",
                          full_name="Test User 2", email="test.user@test.user", is_readonly=False),
     ResponseMessage(title="Unique constraint violation. Value 'test.user@test.user' for field 'email' already exists.",
                     description=f"{E400BadRequest.UNIQUE_CONSTRAINT_VIOLATION}: "
                                 f"[email] [test.user@test.user] Field 'email' must have unique values. "
                                 f"Provided email 'test.user@test.user' already exists.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_register_awfapi_user_should_return_400_response(client, monkeypatch,
                                                         existing_awfapi_user: AWFAPIUserInput,
                                                         awfapi_registered_user: AWFAPIRegisteredUser,
                                                         expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)

        # Act
        response = client.post("/register_awfapi_user", data=awfapi_registered_user.json())

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
