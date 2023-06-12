import pytest
import pymongo
from typing import Optional
from starlette.testclient import TestClient

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig
from app.models import Token, AWFAPIUser, AWFAPIRegisteredUser
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


@pytest.mark.parametrize("awfapi_registered_user, password, is_password_verified", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testpassword", True),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testpassword2", False)
])
def test_verify_should_return_200_response(client, monkeypatch,
                                           awfapi_registered_user: AWFAPIRegisteredUser, password: str,
                                           is_password_verified: bool) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/verify/{password}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict['verified'] == is_password_verified

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, password", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testpassword")
])
def test_verify_should_return_401_response(client, monkeypatch,
                                           awfapi_registered_user: AWFAPIRegisteredUser, password: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.get(f"/verify/{password}")

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, access_token, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     None, "AUTHENTICATED"),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     "EXPIRED"),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "fake_access_token", "UNAUTHENTICATED")
])
def test_test_should_return_200_response(client, monkeypatch,
                                         awfapi_registered_user: AWFAPIRegisteredUser,
                                         access_token: Optional[str],
                                         expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        if access_token is None:
            access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/test", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict['message'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user", [
    AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                         full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True)
])
def test_jwt_auth_test_should_return_200_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/jwt_auth_test", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict['message'] == "JWT Authentication works!"
        assert response_dict['token'] == access_token

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, access_token, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     "JWT token signature expired."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "fake_access_token", "Could not validate credentials.")
])
def test_jwt_auth_test_should_return_401_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  access_token: Optional[str], expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        if access_token is None:
            access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/jwt_auth_test", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user", [
    AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                         full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
    AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                         full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True)
])
def test_current_user_should_return_200_response(client, monkeypatch,
                                                 awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/current_user", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
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


@pytest.mark.parametrize("awfapi_registered_user, access_token, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     "JWT token signature expired."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "fake_access_token", "Could not validate credentials.")
])
def test_current_user_should_return_401_response(client, monkeypatch,
                                                 awfapi_registered_user: AWFAPIRegisteredUser,
                                                 access_token: str, expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        if access_token is None:
            access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/current_user", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user", [
    AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                         full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False)
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
        assert response.status_code == 200
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
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "Current user 'testuser' has readonly restricted access.")
])
def test_current_nonreadonly_user_should_return_400_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             expected_message: Optional[str]) -> None:
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
        assert response.status_code == 400
        response_dict = response.json()
        assert response_dict['detail']['detail'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, access_token, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     "JWT token signature expired."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "fake_access_token", "Could not validate credentials.")
])
def test_current_nonreadonly_user_should_return_401_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             access_token: str,
                                                             expected_message: str) -> None:
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
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
