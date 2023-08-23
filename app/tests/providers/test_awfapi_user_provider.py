import pytest
import pymongo
from typing import List

from app.config import MongodbConnectionConfig
from app.models import AWFAPIUserInput
from app.providers import AWFAPIUserProvider
from app import errors

from app.tests.fixtures.fixtures_tests import drop_collection


connection_string: str = MongodbConnectionConfig.get_db_connection_string()
collection_name: str = MongodbConnectionConfig.get_collection_name(test_suffix="_test")
db_engine: pymongo.MongoClient = pymongo.MongoClient(connection_string)
awfapi_user_provider: AWFAPIUserProvider = AWFAPIUserProvider(connection_string, collection_name, db_engine)


@pytest.mark.parametrize("awfapi_users", [
    [AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS"),
     AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6")],
    [AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6")]
])
def test_get_awfapi_users_should_return_valid_objects(awfapi_users: List[AWFAPIUserInput]) -> None:
    # Arrange
    for awfapi_user in awfapi_users:
        awfapi_user_provider.insert_awfapi_user(awfapi_user)

    # Act
    expected_awfapi_users = awfapi_user_provider.get_awfapi_users()

    # Assert
    try:
        assert len(awfapi_users) == len(expected_awfapi_users)
        for au, eau in zip(awfapi_users, expected_awfapi_users):
            assert au.username == eau.username
            assert au.full_name == eau.full_name
            assert au.email == eau.email
            assert au.is_readonly == eau.is_readonly
            assert au.hashed_password == eau.hashed_password
            assert eau.date_created is not None
            assert eau.date_modified is not None
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
def test_get_awfapi_user_should_return_valid_object(awfapi_user: AWFAPIUserInput) -> None:
    # Arrange
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)

    # Act
    expected_awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)

    # Assert
    try:
        assert awfapi_user.username == expected_awfapi_user.username
        assert awfapi_user.full_name == expected_awfapi_user.full_name
        assert awfapi_user.email == expected_awfapi_user.email
        assert awfapi_user.is_readonly == expected_awfapi_user.is_readonly
        assert awfapi_user.hashed_password == expected_awfapi_user.hashed_password
        assert expected_awfapi_user.date_created is not None
        assert expected_awfapi_user.date_modified is not None
    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("awfapi_user, expected_error", [
    (AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     errors.NotFoundError)
])
def test_get_awfapi_user_should_raise_expected_error(awfapi_user: AWFAPIUserInput, expected_error: Exception) -> None:
    try:
        # Arrange
        awfapi_user_provider.insert_awfapi_user(awfapi_user)

        with pytest.raises(expected_error):
            # Act
            # Assert
            awfapi_user_provider.get_awfapi_user("")

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
def test_insert_awfapi_user_should_insert_object(awfapi_user: AWFAPIUserInput) -> None:
    # Arrange
    # Act
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)

    # Assert
    try:
        expected_awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        assert awfapi_user.username == expected_awfapi_user.username
        assert awfapi_user.full_name == expected_awfapi_user.full_name
        assert awfapi_user.email == expected_awfapi_user.email
        assert awfapi_user.is_readonly == expected_awfapi_user.is_readonly
        assert awfapi_user.hashed_password == expected_awfapi_user.hashed_password
        assert expected_awfapi_user.date_created is not None
        assert expected_awfapi_user.date_modified is not None
    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("existing_awfapi_user, new_awfapi_user, expected_error", [
    (AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria 2", email="dzh.awaria2@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     errors.UsernameAlreadyExistsError),
    (AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6"),
     AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6"),
     errors.EmailAlreadyExistsError)
])
def test_insert_awfapi_user_should_raise_expected_error(existing_awfapi_user: AWFAPIUserInput,
                                                        new_awfapi_user: AWFAPIUserInput,
                                                        expected_error: Exception) -> None:
    # Arrange
    awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)
    # Act
    # Assert
    with pytest.raises(expected_error):
        try:
            awfapi_user_provider.insert_awfapi_user(new_awfapi_user)
        except Exception as e:
            drop_collection(db_engine, collection_name)
            raise e
        else:
            drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("awfapi_user, updated_awfapi_user", [
    (AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIUserInput(username="dzhejkobawaria", full_name="Dzhejkob Awaria 2", email="dzh.awaria2@gmail.com",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6")),
    (AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6"),
     AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                     is_readonly=False, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS"))
])
def test_update_awfapi_user_should_update_object(awfapi_user: AWFAPIUserInput,
                                                 updated_awfapi_user: AWFAPIUserInput) -> None:
    # Arrange
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)
    original_awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)

    # Act
    updated_awfapi_user_username = awfapi_user_provider.update_awfapi_user(awfapi_user_username, updated_awfapi_user)

    # Assert
    try:
        expected_awfapi_user = awfapi_user_provider.get_awfapi_user(updated_awfapi_user_username)
        assert updated_awfapi_user.username == expected_awfapi_user.username
        assert updated_awfapi_user.full_name == expected_awfapi_user.full_name
        assert updated_awfapi_user.email == expected_awfapi_user.email
        assert updated_awfapi_user.is_readonly == expected_awfapi_user.is_readonly
        assert updated_awfapi_user.hashed_password == expected_awfapi_user.hashed_password
        assert original_awfapi_user.date_created == expected_awfapi_user.date_created
        assert original_awfapi_user.date_modified <= expected_awfapi_user.date_modified
    except Exception as e:
        drop_collection(db_engine, collection_name)
        raise e
    else:
        drop_collection(db_engine, collection_name)


@pytest.mark.parametrize("existing_awfapi_users, awfapi_user_username, updated_awfapi_user, expected_error", [
    ([AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                      is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS")],
     "dzhawaria",
     AWFAPIUserInput(username="testuser", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     errors.UsernameAlreadyExistsError),
    ([AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                      is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
     AWFAPIUserInput(username="testuser", full_name="Test User", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS")],
     "testuser",
     AWFAPIUserInput(username="testuser", full_name="Test User", email="dzh.awaria@gmail.com",
                     is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS"),
     errors.EmailAlreadyExistsError)
])
def test_update_awfapi_user_should_raise_expected_error(existing_awfapi_users: List[AWFAPIUserInput],
                                                        awfapi_user_username: str,
                                                        updated_awfapi_user: AWFAPIUserInput,
                                                        expected_error: Exception) -> None:
    # Arrange
    for existing_awfapi_user in existing_awfapi_users:
        awfapi_user_provider.insert_awfapi_user(existing_awfapi_user)

    # Act
    # Assert
    with pytest.raises(expected_error):
        try:
            awfapi_user_provider.update_awfapi_user(awfapi_user_username, updated_awfapi_user)
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
def test_delete_awfapi_user_should_delete_object(awfapi_user: AWFAPIUserInput) -> None:
    # Arrange
    awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user)

    # Act
    awfapi_user_provider.delete_awfapi_user(awfapi_user_username)

    # Assert
    with pytest.raises(errors.NotFoundError):
        try:
            awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        except Exception as e:
            drop_collection(db_engine, collection_name)
            raise e
        else:
            drop_collection(db_engine, collection_name)
