import pytest
import datetime as dt
from typing import Optional

from app.models import AWFAPIUser, AWFAPIUserInput,\
    AWFAPIViewedUser, AWFAPIChangedUserData, AWFAPIChangedUserCredentials, AWFAPIRegisteredUser


@pytest.mark.parametrize("username, full_name, email, is_readonly, hashed_password, expected_awfapi_user_input", [
    ("dzhawaria", "Dzhejkob Awaria", "dzh.awaria@gmail.com",
     False, "$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6",
     AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                     is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6")),
    ("testuser", "Test AWFAPIUserInput", "test.user@test.user",
     True, "$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS",
     AWFAPIUserInput(username="testuser", full_name="Test AWFAPIUserInput", email="test.user@test.user",
                     is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS"))
])
def test_awfapi_user_input_constructor_should_create_valid_object(username: str, full_name: str, email: str,
                                                                  is_readonly: bool, hashed_password: str,
                                                                  expected_awfapi_user_input: AWFAPIUserInput) -> None:
    # Act
    awfapi_user_input = AWFAPIUserInput(username=username, full_name=full_name, email=email,
                                        is_readonly=is_readonly, hashed_password=hashed_password)

    # Assert
    assert awfapi_user_input.username == expected_awfapi_user_input.username
    assert awfapi_user_input.full_name == expected_awfapi_user_input.full_name
    assert awfapi_user_input.email == expected_awfapi_user_input.email
    assert awfapi_user_input.is_readonly == expected_awfapi_user_input.is_readonly
    assert awfapi_user_input.hashed_password == expected_awfapi_user_input.hashed_password


@pytest.mark.parametrize("username, full_name, email, is_readonly, hashed_password,"
                         "date_created, date_modified, expected_awfapi_user", [
                            ("dzhawaria", "Dzhejkob Awaria", "dzh.awaria@gmail.com",
                             False, "$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6",
                             dt.datetime(2022, 1, 1, 0, 0, 0), dt.datetime(2022, 1, 1, 0, 0, 0),
                             AWFAPIUser(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                                        is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6",
                                        date_created=dt.datetime(2022, 1, 1, 0, 0, 0), date_modified=dt.datetime(2022, 1, 1, 0, 0, 0))),
                            ("testuser", "Test AWFAPIUserInput", "test.user@test.user",
                             True, "$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS",
                             dt.datetime(2023, 8, 12, 21, 23, 55), dt.datetime(2023, 10, 21, 12, 3, 21),
                             AWFAPIUser(username="testuser", full_name="Test AWFAPIUserInput", email="test.user@test.user",
                                        is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS",
                                        date_created=dt.datetime(2023, 8, 12, 21, 23, 55), date_modified=dt.datetime(2023, 10, 21, 12, 3, 21)))
                            ])
def test_awfapi_user_constructor_should_create_valid_object(username: str, full_name: str, email: str,
                                                            is_readonly: bool, hashed_password: str,
                                                            date_created: dt.datetime, date_modified: dt.datetime,
                                                            expected_awfapi_user: AWFAPIUser) -> None:
    # Act
    awfapi_user = AWFAPIUser(username=username, full_name=full_name, email=email,
                             is_readonly=is_readonly, hashed_password=hashed_password,
                             date_created=date_created, date_modified=date_modified)

    # Assert
    assert awfapi_user.username == expected_awfapi_user.username
    assert awfapi_user.full_name == expected_awfapi_user.full_name
    assert awfapi_user.email == expected_awfapi_user.email
    assert awfapi_user.is_readonly == expected_awfapi_user.is_readonly
    assert awfapi_user.hashed_password == expected_awfapi_user.hashed_password
    assert awfapi_user.date_created == expected_awfapi_user.date_created
    assert awfapi_user.date_modified == expected_awfapi_user.date_modified


@pytest.mark.parametrize("awfapi_user, awfapi_user_input, expected_awfapi_user", [
    (AWFAPIUser(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6",
                date_created=dt.datetime(2022, 1, 1, 0, 0, 0), date_modified=dt.datetime(2022, 1, 1, 0, 0, 0)),
     AWFAPIUserInput(username="dzhawaria2", full_name="Dzhejkob J Awaria", email="dzh.awaria2@gmail.com",
                     is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6"),
     AWFAPIUser(username="dzhawaria2", full_name="Dzhejkob J Awaria", email="dzh.awaria2@gmail.com",
                is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6",
                date_created=dt.datetime(2022, 1, 1, 0, 0, 0), date_modified=dt.datetime(2022, 1, 1, 0, 0, 0))),

    (AWFAPIUser(username="testuser", full_name="Test AWFAPIUserInput", email="test.user@test.user",
                is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS",
                date_created=dt.datetime(2023, 8, 12, 21, 23, 55), date_modified=dt.datetime(2023, 10, 21, 12, 3, 21)),
     AWFAPIUserInput(username="testuser22", full_name="Test AWFAPIUser22", email="test.user22@test.user",
                     is_readonly=False, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6"),
     AWFAPIUser(username="testuser22", full_name="Test AWFAPIUser22", email="test.user22@test.user",
                is_readonly=False, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6",
                date_created=dt.datetime(2023, 8, 12, 21, 23, 55), date_modified=dt.datetime(2023, 10, 21, 12, 3, 21)))
])
def test_update_awfapi_user_from_input_return_valid_object(awfapi_user: AWFAPIUser, awfapi_user_input: AWFAPIUserInput,
                                                           expected_awfapi_user: AWFAPIUser) -> None:
    # Arrange
    original_awfapi_user = AWFAPIUser(**awfapi_user.dict())
    # Act
    updated_awfapi_user = awfapi_user.update_from_input(awfapi_user_input)

    # Assert
    assert updated_awfapi_user.username == expected_awfapi_user.username
    assert updated_awfapi_user.full_name == expected_awfapi_user.full_name
    assert updated_awfapi_user.email == expected_awfapi_user.email
    assert updated_awfapi_user.is_readonly == expected_awfapi_user.is_readonly
    assert updated_awfapi_user.hashed_password == expected_awfapi_user.hashed_password
    assert original_awfapi_user.date_created == expected_awfapi_user.date_created
    assert original_awfapi_user.date_modified == expected_awfapi_user.date_modified


@pytest.mark.parametrize("username, full_name, email, is_readonly,"
                         "date_created, date_modified, expected_awfapi_viewed_user", [
                            ("dzhawaria", "Dzhejkob Awaria", "dzh.awaria@gmail.com", False,
                             dt.datetime(2022, 1, 1, 0, 0, 0), dt.datetime(2022, 1, 1, 0, 0, 0),
                             AWFAPIViewedUser(username="dzhawaria", full_name="Dzhejkob Awaria",
                                              email="dzh.awaria@gmail.com", is_readonly=False,
                                              date_created=dt.datetime(2022, 1, 1, 0, 0, 0),
                                              date_modified=dt.datetime(2022, 1, 1, 0, 0, 0)))
                            ])
def test_awfapi_viewed_user_constructor_should_create_valid_object(username: str, full_name: str,
                                                                   email: str, is_readonly: bool,
                                                                   date_created: dt.datetime,
                                                                   date_modified: dt.datetime,
                                                                   expected_awfapi_viewed_user: AWFAPIViewedUser) -> None:
    # Act
    awfapi_viewed_user = AWFAPIViewedUser(username=username, full_name=full_name, email=email, is_readonly=is_readonly,
                                          date_created=date_created, date_modified=date_modified)

    # Assert
    assert awfapi_viewed_user.username == expected_awfapi_viewed_user.username
    assert awfapi_viewed_user.full_name == expected_awfapi_viewed_user.full_name
    assert awfapi_viewed_user.email == expected_awfapi_viewed_user.email
    assert awfapi_viewed_user.is_readonly == expected_awfapi_viewed_user.is_readonly
    assert awfapi_viewed_user.date_created == expected_awfapi_viewed_user.date_created
    assert awfapi_viewed_user.date_modified == expected_awfapi_viewed_user.date_modified


@pytest.mark.parametrize("username, password, repeated_password, full_name, email, is_readonly, "
                         "expected_awfapi_registered_user", [
                            ("dzhawaria", "awaria95", "awaria95", "Dzhejkob Awaria", "dzh.awaria@gmail.com", False,
                             AWFAPIRegisteredUser(username="dzhawaria", password="awaria95", repeated_password="awaria95",
                                                  full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com", is_readonly=False)),
                            ("testuser", "testpassword", "testpassword", "Test AWFAPIUserInput", "test.user@test.user", True,
                             AWFAPIRegisteredUser(username="testuser", password="testpassword", repeated_password="testpassword",
                                                  full_name="Test AWFAPIUserInput", email="test.user@test.user", is_readonly=True)),
                            ])
def test_awfapi_registered_user_constructor_should_create_valid_object(username: str, password: str, repeated_password: str,
                                                                       full_name: str, email: str, is_readonly: bool,
                                                                       expected_awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    # Act
    awfapi_registered_user = AWFAPIRegisteredUser(username=username, password=password, repeated_password=repeated_password,
                                                  full_name=full_name, email=email, is_readonly=is_readonly)

    # Assert
    assert awfapi_registered_user.username == expected_awfapi_registered_user.username
    assert awfapi_registered_user.password == expected_awfapi_registered_user.password
    assert awfapi_registered_user.repeated_password == expected_awfapi_registered_user.repeated_password
    assert awfapi_registered_user.full_name == expected_awfapi_registered_user.full_name
    assert awfapi_registered_user.email == expected_awfapi_registered_user.email
    assert awfapi_registered_user.is_readonly == expected_awfapi_registered_user.is_readonly


@pytest.mark.parametrize("full_name, email, is_readonly, expected_awfapi_changed_user_data", [
                            ("Dzhejkob Awaria", "dzh.awaria@gmail.com", False,
                             AWFAPIChangedUserData(full_name="Dzhejkob Awaria",
                                                   email="dzh.awaria@gmail.com", is_readonly=False)),
                            ("Test AWFAPIUserInput", "test.user@test.user", True,
                             AWFAPIChangedUserData(full_name="Test AWFAPIUserInput",
                                                   email="test.user@test.user", is_readonly=True))
                            ])
def test_awfapi_changed_user_data_constructor_should_create_valid_object(full_name: str, email: str, is_readonly: bool,
                                                                         expected_awfapi_changed_user_data: AWFAPIChangedUserData) -> None:
    # Act
    awfapi_changed_user_data = AWFAPIChangedUserData(full_name=full_name, email=email, is_readonly=is_readonly)

    # Assert
    assert awfapi_changed_user_data.full_name == expected_awfapi_changed_user_data.full_name
    assert awfapi_changed_user_data.email == expected_awfapi_changed_user_data.email
    assert awfapi_changed_user_data.is_readonly == expected_awfapi_changed_user_data.is_readonly


@pytest.mark.parametrize("new_username, current_password, new_password, repeated_password,"
                         "expected_awfapi_changed_user_credentials", [
                            ("dzhejkobawaria", "awaria95", "dzhawaria95", "dzhawaria95",
                             AWFAPIChangedUserCredentials(new_username="dzhejkobawaria", current_password="awaria95",
                                                          new_password="dzhawaria95", repeated_password="dzhawaria95")),
                            (None, "awaria95", "dzhawaria95", "dzhawaria95",
                             AWFAPIChangedUserCredentials(current_password="awaria95",
                                                          new_password="dzhawaria95", repeated_password="dzhawaria95")),
                            ("dzhejkobawaria", "awaria95", None, None,
                             AWFAPIChangedUserCredentials(new_username="dzhejkobawaria", current_password="awaria95")),
                            ])
def test_awfapi_changed_user_credentials_constructor_should_create_valid_object(new_username: Optional[str],
                                                                                current_password: str,
                                                                                new_password: Optional[str],
                                                                                repeated_password: Optional[str],
                                                                                expected_awfapi_changed_user_credentials: AWFAPIChangedUserCredentials) -> None:
    # Act
    awfapi_changed_user_credentials = AWFAPIChangedUserCredentials(new_username=new_username,
                                                                   current_password=current_password,
                                                                   new_password=new_password,
                                                                   repeated_password=repeated_password)

    # Assert
    assert awfapi_changed_user_credentials.new_username == expected_awfapi_changed_user_credentials.new_username
    assert awfapi_changed_user_credentials.current_password == expected_awfapi_changed_user_credentials.current_password
    assert awfapi_changed_user_credentials.new_password == expected_awfapi_changed_user_credentials.new_password
    assert awfapi_changed_user_credentials.repeated_password == expected_awfapi_changed_user_credentials.repeated_password
