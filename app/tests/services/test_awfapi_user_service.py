import pytest
import pymongo

from app.config import MongodbConnectionConfig
from app.models import AWFAPIUserInput, AWFAPIRegisteredUser, AWFAPIChangedUserData, AWFAPIChangedUserCredentials
from app.providers import AWFAPIUserProvider
from app.services import AWFAPIUserService
from app import errors

from app.tests.fixtures.fixtures_tests import drop_collection


connection_string: str = MongodbConnectionConfig.get_db_connection_string()
collection_name: str = MongodbConnectionConfig.get_collection_name(test_suffix="_test")
db_engine: pymongo.MongoClient = pymongo.MongoClient(connection_string)
awfapi_user_provider: AWFAPIUserProvider = AWFAPIUserProvider(connection_string, collection_name, db_engine)
awfapi_user_service: AWFAPIUserService = AWFAPIUserService(awfapi_user_provider=awfapi_user_provider)


@pytest.mark.parametrize("awfapi_user", [
    AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                    is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
    AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                    is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6")
])
def test_view_awfapi_user_should_return_valid_object(awfapi_user: AWFAPIUserInput) -> None:
    # Arrange
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)

    # Act
    expected_awfapi_viewed_user = awfapi_user_service.view_awfapi_user(awfapi_user_username)

    # Assert
    try:
        assert awfapi_user.username == expected_awfapi_viewed_user.username
        assert awfapi_user.full_name == expected_awfapi_viewed_user.full_name
        assert awfapi_user.email == expected_awfapi_viewed_user.email
        assert awfapi_user.is_readonly == expected_awfapi_viewed_user.is_readonly
    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("awfapi_registered_user", [
    AWFAPIRegisteredUser(username="dzhawaria", password="awaria95", repeated_password="awaria95",
                         full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com", is_readonly=False),
    AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                         full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True)
])
def test_insert_awfapi_user_should_insert_object(awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    # Arrange
    # Act
    awfapi_user_username = awfapi_user_service.register_awfapi_user(awfapi_registered_user)

    # Assert
    try:
        expected_awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        assert awfapi_registered_user.username == expected_awfapi_user.username
        assert awfapi_registered_user.full_name == expected_awfapi_user.full_name
        assert awfapi_registered_user.email == expected_awfapi_user.email
        assert awfapi_registered_user.is_readonly == expected_awfapi_user.is_readonly
    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("awfapi_user, awfapi_user_username, awfapi_changed_user_data", [
    (AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "dzhawaria",
     AWFAPIChangedUserData(full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com", is_readonly=False)),
    (AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6"),
     "testuser2",
     AWFAPIChangedUserData(full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True))
])
def test_change_awfapi_user_data_should_update_object(awfapi_user: AWFAPIUserInput, awfapi_user_username: str,
                                                      awfapi_changed_user_data: AWFAPIChangedUserData) -> None:
    # Arrange
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)
    original_awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)

    # Act
    updated_awfapi_user_username = awfapi_user_service.change_awfapi_user_data(awfapi_user_username, awfapi_changed_user_data)

    # Assert
    try:
        expected_awfapi_user = awfapi_user_provider.get_awfapi_user(updated_awfapi_user_username)
        assert original_awfapi_user.username == expected_awfapi_user.username
        assert awfapi_changed_user_data.full_name == expected_awfapi_user.full_name
        assert awfapi_changed_user_data.email == expected_awfapi_user.email
        assert awfapi_changed_user_data.is_readonly == expected_awfapi_user.is_readonly
        assert original_awfapi_user.hashed_password == expected_awfapi_user.hashed_password
        assert original_awfapi_user.date_created == expected_awfapi_user.date_created
        assert original_awfapi_user.date_modified <= expected_awfapi_user.date_modified
    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("awfapi_user, awfapi_user_username, awfapi_changed_user_credentials", [
    (AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "dzhawaria",
     AWFAPIChangedUserCredentials(new_username="dzhejkobawaria", current_password="awaria95",
                                  new_password="dzhawaria95", repeated_password="dzhawaria95")),
    (AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "dzhawaria",
     AWFAPIChangedUserCredentials(current_password="awaria95",
                                  new_password="dzhawaria95", repeated_password="dzhawaria95")),
    (AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     "dzhawaria",
     AWFAPIChangedUserCredentials(new_username="dzhejkobawaria", current_password="awaria95")),
])
def test_change_awfapi_user_credentials_should_update_object(awfapi_user: AWFAPIUserInput, awfapi_user_username: str,
                                                             awfapi_changed_user_credentials: AWFAPIChangedUserCredentials) -> None:
    # Arrange
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)
    original_awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)

    # Act
    updated_awfapi_user_username = awfapi_user_service.change_awfapi_user_credentials(awfapi_user_username, awfapi_changed_user_credentials)

    # Assert
    try:
        expected_awfapi_user = awfapi_user_provider.get_awfapi_user(updated_awfapi_user_username)
        assert original_awfapi_user.full_name == expected_awfapi_user.full_name
        assert original_awfapi_user.email == expected_awfapi_user.email
        assert original_awfapi_user.is_readonly == expected_awfapi_user.is_readonly

        if awfapi_changed_user_credentials.new_username is not None and awfapi_changed_user_credentials.new_password is not None:
            assert awfapi_changed_user_credentials.new_username == expected_awfapi_user.username
            assert awfapi_user_service.verify_password(awfapi_changed_user_credentials.new_password, expected_awfapi_user.hashed_password)
        elif awfapi_changed_user_credentials.new_username is not None:
            assert awfapi_changed_user_credentials.new_username == expected_awfapi_user.username
            assert original_awfapi_user.hashed_password == expected_awfapi_user.hashed_password
        elif awfapi_changed_user_credentials.new_password is not None:
            assert original_awfapi_user.username == expected_awfapi_user.username
            assert awfapi_user_service.verify_password(awfapi_changed_user_credentials.new_password, expected_awfapi_user.hashed_password)

        assert original_awfapi_user.date_created == expected_awfapi_user.date_created
        assert original_awfapi_user.date_modified <= expected_awfapi_user.date_modified
    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("awfapi_user", [
    AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                    is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
    AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                    is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6")
])
def test_remove_awfapi_user_account_should_delete_object(awfapi_user: AWFAPIUserInput) -> None:
    # Arrange
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)

    # Act
    awfapi_user_service.remove_awfapi_user_account(awfapi_user_username)

    # Assert
    with pytest.raises(errors.NotFoundError):
        try:
            awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        except Exception as e:
            drop_collection(db_engine, collection_name)
            raise e
        else:
            drop_collection(db_engine, collection_name)
