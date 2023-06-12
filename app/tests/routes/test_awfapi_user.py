import pytest
import pymongo
from typing import List
from starlette.testclient import TestClient

from app.config import JWTAuthenticationConfig, MongodbConnectionConfig
from app.models import Message, AWFAPIUserInput, AWFAPIUser, AWFAPIViewedUser, AWFAPIRegisteredUser, AWFAPIChangedUserData, AWFAPIChangedUserCredentials
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


awfapi_users_db = [
    AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                    is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
    AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                    is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS"),
    AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                    is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6")
]


@pytest.mark.parametrize("awfapi_registered_user, offset, limit, expected_awfapi_users", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     0, 3,
     [awfapi_users_db[0], awfapi_users_db[1], awfapi_users_db[2]]),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     1, 1, [awfapi_users_db[1]]),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     0, 3, [awfapi_users_db[0], awfapi_users_db[1], awfapi_users_db[2]])
])
def test_get_awfapi_users_should_return_200_response(client, monkeypatch,
                                                     awfapi_registered_user: AWFAPIRegisteredUser,
                                                     offset: int, limit: int,
                                                     expected_awfapi_users: List[AWFAPIUserInput]) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/all_awfapi_users", params={'offset': offset, 'limit': limit}, headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        response_dict = response.json()
        awfapi_users = list(map(lambda rd: AWFAPIUser(**rd), response_dict))
        assert len(awfapi_users) == len(expected_awfapi_users)
        for au, eau in zip(awfapi_users, expected_awfapi_users):
            assert au.username == eau.username
            assert au.full_name == eau.full_name
            assert au.email == eau.email
            assert au.is_readonly == eau.is_readonly

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, offset, limit", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     0, 3)
])
def test_get_awfapi_users_should_return_401_response(client, monkeypatch,
                                                     awfapi_registered_user: AWFAPIRegisteredUser,
                                                     offset: int, limit: int) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.get("/all_awfapi_users", params={'offset': offset, 'limit': limit})

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user_username, expected_awfapi_user", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "dzhawaria", awfapi_users_db[0]),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "testuser2", awfapi_users_db[1]),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser22", awfapi_users_db[2])
])
def test_get_awfapi_user_should_return_200_response(client, monkeypatch,
                                                    awfapi_registered_user: AWFAPIRegisteredUser,
                                                    awfapi_user_username: str,
                                                    expected_awfapi_user: AWFAPIUserInput) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/get_awfapi_user/{awfapi_user_username}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        awfapi_user = AWFAPIUser(**response.json())
        assert awfapi_user.username == expected_awfapi_user.username
        assert awfapi_user.full_name == expected_awfapi_user.full_name
        assert awfapi_user.email == expected_awfapi_user.email
        assert awfapi_user.is_readonly == expected_awfapi_user.is_readonly

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "dzhawaria")
])
def test_get_awfapi_user_should_return_401_response(client, monkeypatch,
                                                    awfapi_registered_user: AWFAPIRegisteredUser,
                                                    awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.get(f"/get_awfapi_user/{awfapi_user_username}")

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "dzhawaria2")
])
def test_get_awfapi_user_should_return_404_response(client, monkeypatch,
                                                    awfapi_registered_user: AWFAPIRegisteredUser,
                                                    awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/get_awfapi_user/{awfapi_user_username}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 404
        response_dict = response.json()
        assert response_dict['detail']['detail'] == "AWFAPI User of given id dzhawaria2 was not found."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"))
])
def test_create_awfapi_user_should_return_201_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       awfapi_user: AWFAPIUserInput) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.post("/create_awfapi_user", data=awfapi_user.json(), headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 201
        new_awfapi_user = AWFAPIUser(**response.json())
        assert new_awfapi_user.username == awfapi_user.username
        assert new_awfapi_user.full_name == awfapi_user.full_name
        assert new_awfapi_user.email == awfapi_user.email
        assert new_awfapi_user.is_readonly == awfapi_user.is_readonly

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "Current user 'testuser' has readonly restricted access."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "Field 'username' must have unique values. Provided value 'testuser' already exists."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "Field 'email' must have unique values. Provided value 'test.user@test.user' already exists.")
])
def test_create_awfapi_user_should_return_400_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       awfapi_user: AWFAPIUserInput, expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.post("/create_awfapi_user", data=awfapi_user.json(), headers={
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


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"))
])
def test_create_awfapi_user_should_return_401_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       awfapi_user: AWFAPIUserInput) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.post("/create_awfapi_user", data=awfapi_user.json())

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


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
        assert response.status_code == 200
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
     "Current user 'testuser' has readonly restricted access."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "Field 'username' must have unique values. Provided value 'testuser' already exists."),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "Field 'email' must have unique values. Provided value 'test.user@test.user' already exists.")
])
def test_update_awfapi_user_should_return_400_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       original_awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str, awfapi_user: AWFAPIUserInput,
                                                       expected_message: str) -> None:
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
        assert response.status_code == 400
        response_dict = response.json()
        assert response_dict['detail']['detail'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username, awfapi_user", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF7"))
])
def test_update_awfapi_user_should_return_401_response(client, monkeypatch,
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
        awfapi_user_provider.insert_awfapi_user(original_awfapi_user)

        # Act
        response = client.put(f"/update_awfapi_user/{awfapi_user_username}", data=awfapi_user.json())

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username, awfapi_user", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser22",
     AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF7"))
])
def test_update_awfapi_user_should_return_404_response(client, monkeypatch,
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
        assert response.status_code == 404
        response_dict = response.json()
        assert response_dict['detail']['detail'] == "AWFAPI User of given id testuser22 was not found."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2")
])
def test_delete_awfapi_user_should_return_200_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       original_awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str) -> None:
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
        response = client.delete(f"/delete_awfapi_user/{awfapi_user_username}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        response_message = Message(**response.json())
        assert response_message.info == "AWFAPI user deleted"
        assert response_message.message == "AWFAPI user of given username 'testuser2' deleted."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user, awfapi_user_username, expected_message", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2",
     "Current user 'testuser' has readonly restricted access.")
])
def test_delete_awfapi_user_should_return_400_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str,
                                                       expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(awfapi_user)

        # Act
        response = client.delete(f"/delete_awfapi_user/{awfapi_user_username}", headers={
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


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2")
])
def test_delete_awfapi_user_should_return_401_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(awfapi_user)

        # Act
        response = client.delete(f"/delete_awfapi_user/{awfapi_user_username}")

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser22")
])
def test_delete_awfapi_user_should_return_404_response(client, monkeypatch,
                                                       awfapi_registered_user: AWFAPIRegisteredUser,
                                                       awfapi_user: AWFAPIUserInput,
                                                       awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(awfapi_user)

        # Act
        response = client.delete(f"/delete_awfapi_user/{awfapi_user_username}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 404
        response_dict = response.json()
        assert response_dict['detail']['detail'] == "AWFAPI User of given id testuser22 was not found."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user_username, expected_awfapi_viewed_user", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "dzhawaria", awfapi_users_db[0]),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "testuser2", awfapi_users_db[1]),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser22", awfapi_users_db[2])
])
def test_view_awfapi_user_profile_should_return_200_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             awfapi_user_username: str,
                                                             expected_awfapi_viewed_user: AWFAPIUserInput) -> None:
    try:
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        # Arrange
        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/view_awfapi_user_profile/{awfapi_user_username}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        awfapi_viewed_user = AWFAPIViewedUser(**response.json())
        assert awfapi_viewed_user.username == expected_awfapi_viewed_user.username
        assert awfapi_viewed_user.full_name == expected_awfapi_viewed_user.full_name
        assert awfapi_viewed_user.email == expected_awfapi_viewed_user.email
        assert awfapi_viewed_user.is_readonly == expected_awfapi_viewed_user.is_readonly

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "dzhawaria")
])
def test_view_awfapi_user_profile_should_return_401_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)

        # Act
        response = client.get(f"/view_awfapi_user_profile/{awfapi_user_username}")

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "dzhawaria2")
])
def test_view_awfapi_user_profile_should_return_404_response(client, monkeypatch,
                                                             awfapi_registered_user: AWFAPIRegisteredUser,
                                                             awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        for audb in awfapi_users_db:
            awfapi_user_provider.insert_awfapi_user(audb)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get(f"/view_awfapi_user_profile/{awfapi_user_username}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 404
        response_dict = response.json()
        assert response_dict['detail']['detail'] == "User of given id dzhawaria2 was not found."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user", [
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword", repeated_password="testpassword",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=True))
])
def test_register_awfapi_user_should_return_201_response(client, monkeypatch,
                                                         existing_awfapi_user: AWFAPIUserInput,
                                                         awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)

        # Act
        response = client.post("/register_awfapi_user", data=awfapi_registered_user.json())

        # Assert
        assert response.status_code == 201
        response_message = Message(**response.json())
        assert response_message.info == "User registered"
        assert response_message.message == "New user 'testuser2' registered."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, expected_message", [
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "Field 'username' must have unique values. Provided value 'testuser' already exists."),
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword", repeated_password="testpassword",
                          full_name="Test User 2", email="test.user@test.user", is_readonly=False),
     "Field 'email' must have unique values. Provided value 'test.user@test.user' already exists.")
])
def test_register_awfapi_user_should_return_400_response(client, monkeypatch,
                                                         existing_awfapi_user: AWFAPIUserInput,
                                                         awfapi_registered_user: AWFAPIRegisteredUser,
                                                         expected_message: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)

        # Act
        response = client.post("/register_awfapi_user", data=awfapi_registered_user.json())

        # Assert
        assert response.status_code == 400
        response_dict = response.json()
        assert response_dict['detail']['detail'] == expected_message

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data", [
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword2", repeated_password="testpassword2",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserData(full_name="Test User 22", email="test.user22@test.user", is_readonly=False))
])
def test_change_awfapi_user_data_should_return_200_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData) -> None:
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
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}", data=awfapi_changed_user_data.json(),
                              headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        response_message = Message(**response.json())
        assert response_message.info == "User data changed"
        assert response_message.message == "Data of user 'testuser2' changed."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data, expected_message", [
    (AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser2", password="testpassword2", repeated_password="testpassword2",
                          full_name="Test User 2", email="test.user2@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserData(full_name="Test User 2", email="test.user@test.user", is_readonly=True),
     "Field 'email' must have unique values. Provided value 'test.user@test.user' already exists.")
])
def test_change_awfapi_user_data_should_return_400_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData,
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
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}", data=awfapi_changed_user_data.json(),
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


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data", [
    (AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "testuser2",
     AWFAPIChangedUserData(full_name="Test User 22", email="test.user22@test.user", is_readonly=False))
])
def test_change_awfapi_user_data_should_return_401_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
        awfapi_user_service.register_awfapi_user(awfapi_registered_user)

        # Act
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}", data=awfapi_changed_user_data.json())

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("existing_awfapi_user, awfapi_registered_user, awfapi_user_username, awfapi_changed_user_data", [
    (AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     "testuser22",
     AWFAPIChangedUserData(full_name="Test User 22", email="test.user22@test.user", is_readonly=False))
])
def test_change_awfapi_user_data_should_return_404_response(client, monkeypatch,
                                                            existing_awfapi_user: AWFAPIUserInput,
                                                            awfapi_registered_user: AWFAPIRegisteredUser,
                                                            awfapi_user_username: str,
                                                            awfapi_changed_user_data: AWFAPIChangedUserData) -> None:
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
        response = client.put(f"/change_awfapi_user_data/{awfapi_user_username}", data=awfapi_changed_user_data.json(),
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
        assert response_message.info == "User credentials changed"
        # assert response_message.message == "Credentials of user 'testuser22' changed." #  turned off, waiting for expected message param

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


@pytest.mark.parametrize("awfapi_registered_user, original_awfapi_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2")
])
def test_remove_awfapi_user_account_should_return_200_response(client, monkeypatch,
                                                               awfapi_registered_user: AWFAPIRegisteredUser,
                                                               original_awfapi_user: AWFAPIUserInput,
                                                               awfapi_user_username: str) -> None:
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
        response = client.delete(f"/remove_awfapi_user_account/{awfapi_user_username}", headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == 200
        response_message = Message(**response.json())
        assert response_message.info == "Account removed"
        assert response_message.message == "Account of user 'testuser2' removed."

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser2")
])
def test_remove_awfapi_user_account_should_return_401_response(client, monkeypatch,
                                                               awfapi_registered_user: AWFAPIRegisteredUser,
                                                               awfapi_user: AWFAPIUserInput,
                                                               awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(awfapi_user)

        # Act
        response = client.delete(f"/remove_awfapi_user_account/{awfapi_user_username}")

        # Assert
        assert response.status_code == 401
        response_dict = response.json()
        assert response_dict['detail'] == "Not authenticated"

    except Exception as e:
        drop_collection(mongodb_engine, mongodb_collection_name)
        raise e
    else:
        drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, awfapi_user, awfapi_user_username", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=False),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "testuser22")
])
def test_remove_awfapi_user_account_should_return_404_response(client, monkeypatch,
                                                               awfapi_registered_user: AWFAPIRegisteredUser,
                                                               awfapi_user: AWFAPIUserInput,
                                                               awfapi_user_username: str) -> None:
    try:
        # Arrange
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
        monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
        monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
        monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)
        awfapi_user_provider.insert_awfapi_user(awfapi_user)

        # Act
        response = client.delete(f"/remove_awfapi_user_account/{awfapi_user_username}", headers={
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
