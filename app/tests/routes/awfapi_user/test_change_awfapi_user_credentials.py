import pytest
import pymongo
from starlette.testclient import TestClient

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig
from app.models import Message, AWFAPIUserInput, AWFAPIRegisteredUser, AWFAPIChangedUserCredentials
from app.providers import AWFAPIUserProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_tests import obtain_access_token, drop_collection


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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_credentials", [
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword2", repeated_password="testpassword2",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserCredentials(new_username="testuser22", current_password="testpassword2",
                                  new_password="testpassword22", repeat_new_password="testpassword22")),
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword2", repeated_password="testpassword2",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserCredentials(new_username="testuser22", current_password="testpassword2")),
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword2", repeated_password="testpassword2",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserCredentials(current_password="testpassword2",
                                  new_password="testpassword22", repeat_new_password="testpassword22"))
])
def test_change_awfapi_user_credentials_should_return_200_response(client, monkeypatch,
                                                                   existing_awfapi_user: AWFAPIUserInput,
                                                                   awfapi_registered_user: AWFAPIRegisteredUser,
                                                                   awfapi_user_username: str,
                                                                   awfapi_changed_user_credentials: AWFAPIChangedUserCredentials) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_credentials/{awfapi_user_username}",
                              data=awfapi_changed_user_credentials.json(),
                              headers={
                                  'Authorization': f"Bearer {access_token}"
                              })

        # Assert
        assert response.status_code == 200
        response_message = Message(**response.json())
        assert response_message.title == "User credentials changed"
        # assert response_message.description == "Credentials of user 'testuser22' changed." #  turned off, waiting for expected description param

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_credentials, expected_message", [
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword2", repeated_password="testpassword2",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserCredentials(new_username="testuser", current_password="testpassword2"),
     "Field 'username' must have unique values. Provided value 'testuser' already exists."),
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword2", repeated_password="testpassword2",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserCredentials(new_username="testuser22", current_password="testpassword22"),
     "User provided wrong current password.")
])
def test_change_awfapi_user_credentials_should_return_400_response(client, monkeypatch,
                                                                   existing_awfapi_user: AWFAPIUserInput,
                                                                   awfapi_registered_user: AWFAPIRegisteredUser,
                                                                   awfapi_user_username: str,
                                                                   awfapi_changed_user_credentials: AWFAPIChangedUserCredentials,
                                                                   expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_credentials/{awfapi_user_username}",
                              data=awfapi_changed_user_credentials.json(),
                              headers={
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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_credentials", [
    (AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserCredentials(new_username="testuser2", current_password="testpassword2"))
])
def test_change_awfapi_user_credentials_should_return_401_response(client, monkeypatch,
                                                                   existing_awfapi_user: AWFAPIUserInput,
                                                                   awfapi_registered_user: AWFAPIRegisteredUser,
                                                                   awfapi_user_username: str,
                                                                   awfapi_changed_user_credentials: AWFAPIChangedUserCredentials) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_credentials/{awfapi_user_username}",
                              data=awfapi_changed_user_credentials.json())

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_credentials", [
    (AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "testuser22",
     AWFAPIChangedUserCredentials(new_username="testuser22", current_password="testpassword22"))
])
def test_change_awfapi_user_credentials_should_return_404_response(client, monkeypatch,
                                                                   existing_awfapi_user: AWFAPIUserInput,
                                                                   awfapi_registered_user: AWFAPIRegisteredUser,
                                                                   awfapi_user_username: str,
                                                                   awfapi_changed_user_credentials: AWFAPIChangedUserCredentials) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_credentials/{awfapi_user_username}",
                              data=awfapi_changed_user_credentials.json(),
                              headers={
                                  'Authorization': f"Bearer {access_token}"
                              })

        # Assert
        assert response.status_code == 404
        response_dict = response.json()
        assert response_dict['detail']['detail'] == "User of given id testuser22 was not found."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)
