import pytest
import pymongo
from starlette.testclient import TestClient
from fastapi import status

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig
from app.models import ResponseMessage, AWFAPIUserInput, AWFAPIUser, AWFAPIRegisteredUser
from app.providers import AWFAPIUserProvider
from app.services import JWTAuthenticationService, AWFAPIUserService

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
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


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username, awfapi_user", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF7"))
])
def test_update_awfapi_user_should_return_200_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       original_awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str, awfapi_user: AWFAPIUserInput) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(original_awfapi_user)

        # Act
        response = client.put(f"/update_awfapi_user/{awfapi_user_username}", data=awfapi_user.json(), headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == status.HTTP_200_OK
        updated_awfapi_user = AWFAPIUser(**response.json())
        assert updated_awfapi_user.username == awfapi_user.username
        assert updated_awfapi_user.full_name == awfapi_user.full_name
        assert updated_awfapi_user.email == awfapi_user.email
        assert updated_awfapi_user.is_readonly == awfapi_user.is_readonly

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username, awfapi_user, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     ResponseMessage(title="Readonly access for 'testuser'.",
                     description="Current user 'testuser' has readonly restricted access.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     ResponseMessage(title="Field 'username' uniqueness.",
                     description="Field 'username' must have unique values. Provided value 'testuser' already exists.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     ResponseMessage(title="Field 'email' uniqueness.",
                     description="Field 'email' must have unique values. Provided value 'test.user@test.user' already exists.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_update_awfapi_user_should_return_400_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       original_awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str, awfapi_user: AWFAPIUserInput,
                                                       expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(original_awfapi_user)

        # Act
        response = client.put(f"/update_awfapi_user/{awfapi_user_username}", data=awfapi_user.json(), headers={
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


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username, awfapi_user, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF7"),
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description="User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_update_awfapi_user_should_return_401_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       original_awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str, awfapi_user: AWFAPIUserInput,
                                                       expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(original_awfapi_user)

        # Act
        response = client.put(f"/update_awfapi_user/{awfapi_user_username}", data=awfapi_user.json())

        # Assert
        message = ResponseMessage(**response.json())
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username, awfapi_user, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser22",
     AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF7"),
     ResponseMessage(title="AWFAPI User not found.",
                     description="AWFAPI User of given id 'testuser22' was not found.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_update_awfapi_user_should_return_404_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       original_awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str, awfapi_user: AWFAPIUserInput,
                                                       expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(original_awfapi_user)

        # Act
        response = client.put(f"/update_awfapi_user/{awfapi_user_username}", data=awfapi_user.json(), headers={
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