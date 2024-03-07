import pytest
import pymongo
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig
from app.models import ResponseMessage, AWFAPIUser, AWFAPIRegisteredUser, \
    E400BadRequest, E401Unauthorized
from app.providers import AWFAPIUserProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_tests import register_test_user, obtain_access_token, drop_collection


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


@pytest.mark.parametrize("awfapi_registered_user", [
    awfapi_nonreadonly_user
])
def test_current_nonreadonly_user_should_return_200_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/current_nonreadonly_user", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == status.HTTP_200_OK
        awfapi_user = AWFAPIUser(**response.json())
        assert awfapi_user.username == awfapi_registered_user.username
        assert awfapi_user.full_name == awfapi_registered_user.full_name
        assert awfapi_user.email == awfapi_registered_user.email
        assert awfapi_user.is_readonly == awfapi_registered_user.is_readonly

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, expected_message", [
    (awfapi_readonly_user,
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description=f"{E400BadRequest.READONLY_ACCESS_FOR_USER}: "
                                 f"[testuser] Current user 'testuser' has readonly restricted access.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_current_nonreadonly_user_should_return_400_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/current_nonreadonly_user", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        message = ResponseMessage(**response.json()['detail'])
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, access_token, expected_message", [
    (awfapi_nonreadonly_user, "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     ResponseMessage(title="Not authorized.",
                     description=f"{E401Unauthorized.JWT_TOKEN_EXPIRED}: JWT token signature expired.",
                     code=status.HTTP_401_UNAUTHORIZED)),
    (awfapi_nonreadonly_user, "fake_access_token",
     ResponseMessage(title="Not authorized.",
                     description=f"{E401Unauthorized.INVALID_CREDENTIALS}: Could not validate credentials.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_current_nonreadonly_user_should_return_401_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             access_token: str,
                                                             expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        if access_token is None:
            access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/current_nonreadonly_user", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        message = ResponseMessage(**response.json()['detail'])
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
