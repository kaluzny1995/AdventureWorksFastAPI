import pytest
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, Token, AWFAPIRegisteredUser,
                        E401Unauthorized)
from app.factories import MongoDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory

from app.routes import jwt_authentication as jwt_authentication_routes

from app.tests.fixtures.fixtures_entry_lists import awfapi_readonly_user
from app.tests.fixtures.fixtures_tests import register_test_user, drop_collection


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def fixtures_before_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, username, password", [
    (awfapi_readonly_user, "testuser", "testpassword")
])
def test_login_for_access_token_should_return_200_response(client, monkeypatch,
                                                           awfapi_registered_user: AWFAPIRegisteredUser,
                                                           username: str, password: str) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.post("/token", data={'username': username, 'password': password})
        token = Token(**response.json())
        token_user = jwt_authentication_service.get_user_from_token(token.access_token)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert token.token_type == "bearer"
        assert token_user.username == awfapi_registered_user.username

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, username, password, expected_message", [
    (awfapi_readonly_user, "testuser2", "testpassword",
     ResponseMessage(title="Not authorized.",
                     description=f"{E401Unauthorized.INVALID_USERNAME}: Invalid username.",
                     code=status.HTTP_401_UNAUTHORIZED)),
    (awfapi_readonly_user, "testuser", "testpassword2",
     ResponseMessage(title="Not authorized.",
                     description=f"{E401Unauthorized.INVALID_PASSWORD}: Invalid password.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_login_for_access_token_should_return_401_response(client, monkeypatch,
                                                           awfapi_registered_user: AWFAPIRegisteredUser,
                                                           username: str, password: str,
                                                           expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.post("/token", data={'username': username, 'password': password})

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
