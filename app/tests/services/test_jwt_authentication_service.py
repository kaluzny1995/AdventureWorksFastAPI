import pytest
import pymongo
from typing import Optional

from app.config import MongodbConnectionConfig
from app.models import AWFAPIRegisteredUser
from app.providers import AWFAPIUserProvider
from app.services import AWFAPIUserService, JWTAuthenticationService
from app import errors

from app.tests.fixtures.fixtures_tests import register_test_user, drop_collection


connection_string: str = MongodbConnectionConfig.get_db_connection_string()
collection_name: str = MongodbConnectionConfig.get_collection_name(test_suffix="_test")
db_engine: pymongo.MongoClient = pymongo.MongoClient(connection_string)
awfapi_user_provider: AWFAPIUserProvider = AWFAPIUserProvider(connection_string, collection_name, db_engine)
awfapi_user_service: AWFAPIUserService = AWFAPIUserService(awfapi_user_provider=awfapi_user_provider)
jwt_auth_service: JWTAuthenticationService = JWTAuthenticationService(awfapi_user_provider=awfapi_user_provider,
                                                                      awfapi_user_service=awfapi_user_service)


@pytest.mark.parametrize("awfapi_registered_user, username, password, expected_error", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser", "testpassword", None),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser2", "testpassword", errors.InvalidCredentialsError),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "testuser", "testpassword2", errors.InvalidCredentialsError)
])
def test_authenticate_user_should_return_valid_object_or_raise_expected_error(awfapi_registered_user: AWFAPIRegisteredUser,
                                                                              username: str, password: str,
                                                                              expected_error: Optional[Exception]) -> None:
    # Arrange
    register_test_user(awfapi_user_service, awfapi_registered_user)

    try:
        if expected_error is None:
            # Act
            expected_awfapi_user = jwt_auth_service.authenticate_user(username, password)

            # Assert
            assert awfapi_registered_user.username == expected_awfapi_user.username
            assert awfapi_registered_user.full_name == expected_awfapi_user.full_name
            assert awfapi_registered_user.email == expected_awfapi_user.email
            assert awfapi_registered_user.is_readonly == expected_awfapi_user.is_readonly
        else:
            with pytest.raises(expected_error):
                # Act
                # Assert
                jwt_auth_service.authenticate_user(username, password)

    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("awfapi_registered_user, access_token, expected_error", [
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     None, None),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     errors.JWTTokenSignatureExpiredError),
    (AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "fake_access_token", errors.InvalidCredentialsError),
    (AWFAPIRegisteredUser(username="dzhawaria", password="awaria95", repeated_password="awaria95",
                          full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True),
     "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     errors.JWTTokenSignatureExpiredError)
])
def test_get_user_from_token_should_return_valid_object_or_raise_expected_error(awfapi_registered_user: AWFAPIRegisteredUser,
                                                                                access_token: Optional[str],
                                                                                expected_error: Optional[Exception]) -> None:
    # Arrange
    register_test_user(awfapi_user_service, awfapi_registered_user)
    if access_token is None:
        access_token = jwt_auth_service.create_access_token(data={"sub": awfapi_registered_user.username})

    try:
        if expected_error is None:
            # Act
            expected_awfapi_user = jwt_auth_service.get_user_from_token(access_token)

            # Assert
            assert awfapi_registered_user.username == expected_awfapi_user.username
            assert awfapi_registered_user.full_name == expected_awfapi_user.full_name
            assert awfapi_registered_user.email == expected_awfapi_user.email
            assert awfapi_registered_user.is_readonly == expected_awfapi_user.is_readonly
        else:
            with pytest.raises(expected_error):
                # Act
                # Assert
                jwt_auth_service.get_user_from_token(access_token)

    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)
