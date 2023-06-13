import pytest
import pymongo
from starlette.testclient import TestClient

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig
from app.models import Token, AWFAPIRegisteredUser
from app.providers import AWFAPIUserProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes

from app.tests.fixtures.fixtures_tests import register_test_user, drop_collection


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


@pytest.mark.parametrize("awfapi_registered_user, username, password", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser", "testpassword")
])
def test_login_for_access_token_should_return_200_response(client, monkeypatch,
                                                           awfapi_registered_user: AWFAPIRegisteredUser,
                                                           username: str, password: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.post("/token", data={'username': username, 'password': password})
        token = Token(**response.json())
        token_user = jwt_authentication_service.get_user_from_token(token.access_token)

        # Assert
        assert response.status_code == 200
        assert token.token_type == "bearer"
        assert token_user.username == awfapi_registered_user.username

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, username, password, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser2", "testpassword", "Invalid username."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser", "testpassword2", "Invalid password.")
])
def test_login_for_access_token_should_return_401_response(client, monkeypatch,
                                                           awfapi_registered_user: AWFAPIRegisteredUser,
                                                           username: str, password: str,
                                                           expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.post("/token", data={'username': username, 'password': password})

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
