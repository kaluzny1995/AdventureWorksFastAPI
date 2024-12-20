from typing import Union, Dict, List
import pytest

from app.models import PrimaryKeyErrorDetails, ForeignKeyErrorDetails
from app import errors, utils


@pytest.mark.parametrize("filter_string, expected_params", [
    ("pt:GC,fnph:Joh,lnph:D", dict(pt="GC", fnph="Joh", lnph="D")),
    ("pt:Joh,lnph:Doe", dict(pt="Joh", lnph="Doe")),
    ("pt:,lnph:Doe", dict(pt="", lnph="Doe")),
    ("pt:Joh,lnph:", dict(pt="Joh", lnph="")),
])
def test_get_filter_params_should_return_expected_params(filter_string: str, expected_params: Dict[str, str]) -> None:
    # Arrange
    # Act
    params = utils.get_filter_params(filter_string)

    # Assert
    assert params == expected_params


@pytest.mark.parametrize("filter_string, expected_error", [
    ("pt:Joh,lnph:Doe,", errors.InvalidFilterStringError),
    (",pt:Joh,lnph:Doe", errors.InvalidFilterStringError),
    ("pt:Joh,lnph:Doe:", errors.InvalidFilterStringError),
    (":pt:Joh,lnph:Doe", errors.InvalidFilterStringError)
])
def test_get_filter_params_should_raise_expected_error(filter_string: str, expected_error: Exception) -> None:
    # Arrange
    with pytest.raises(expected_error):
        # Act
        # Assert
        utils.get_filter_params(filter_string)


@pytest.mark.parametrize("params_dict, expected_params", [
    (dict(pt="3", fnph="Joh", lnph="-1"), dict(pt=3, fnph="Joh", lnph=-1)),
    (dict(pt="3.", fnph="Joh", lnph="-3."), dict(pt=3., fnph="Joh", lnph=-3.)),
    (dict(pt="3", fnph="[Joh]", lnph="D"), dict(pt=3, fnph=["Joh"], lnph="D")),
    (dict(pt="3", fnph="[Joh|Doe]", lnph="D"), dict(pt=3, fnph=["Joh", "Doe"], lnph="D")),
    (dict(pt="3", fnph="[3]", lnph="D"), dict(pt=3, fnph=[3], lnph="D")),
    (dict(pt="3", fnph="[3|4]", lnph="D"), dict(pt=3, fnph=[3, 4], lnph="D")),
    (dict(pt="3", fnph="[3.|4|joh]", lnph="D"), dict(pt=3, fnph=["3.", "4", "joh"], lnph="D")),
])
def test_adjust_filter_params_should_return_expected_params(params_dict: Dict[str, str],
                                                            expected_params: Dict[str, Union[int, float, str, List[int], List[float], List[str]]]) -> None:
    # Arrange
    # Act
    params = utils.adjust_filter_params(params_dict)

    # Assert
    assert params == expected_params


@pytest.mark.parametrize("params_dict, expected_error", [
    (dict(pt="3", fnph="J[o]h", lnph="-1"), errors.InvalidFilterStringError),
    (dict(pt="3", fnph="[[Joh]]", lnph="-1"), errors.InvalidFilterStringError),
    (dict(pt="3", fnph="[Joh]]", lnph="-1"), errors.InvalidFilterStringError),
    (dict(pt="3", fnph="[J[oh]", lnph="-1"), errors.InvalidFilterStringError),
    (dict(pt="3", fnph="[Joh|Doe]]", lnph="-1"), errors.InvalidFilterStringError),
    (dict(pt="3", fnph="[Joh[|]Doe]", lnph="-1"), errors.InvalidFilterStringError),
])
def test_adjust_filter_params_should_raise_expected_error(params_dict: Dict[str, str],
                                                          expected_error: Exception) -> None:
    # Arrange
    with pytest.raises(expected_error):
        # Act
        # Assert
        utils.adjust_filter_params(params_dict)


@pytest.mark.parametrize("error_message, expected_username", [
    ("E400_000: [testuser] Current user 'testuser' has readonly restricted access.", "testuser"),
    ("E400_000: [testuser2] Current user 'testuser2' has readonly restricted access.", "testuser2"),
    ("E400_000: [testuser22] Current user 'testuser22' has readonly restricted access.", "testuser22")
])
def test_get_username_from_message_should_return_expected_username(error_message: str,
                                                                   expected_username: str) -> None:
    # Arrange
    # Act
    username = utils.get_username_from_message(error_message)

    # Assert
    assert username == expected_username


@pytest.mark.parametrize("error_message, expected_field_name, expected_field_value", [
    ("E400_001: [username] [testuser] "
     "Field 'username' must have unique values. "
     "Provided username 'testuser' already exists.", "username", "testuser"),
    ("E400_001: [email] [test.user@test.com] "
     "Field 'email' must have unique values. "
     "Provided email 'test.user@test.com' already exists.", "email", "test.user@test.com"),
    ("E400_001: [uuid] [12340987-1908] "
     "Field 'uuid' must have unique values. "
     "Provided uuid '12340987-1908' already exists.", "uuid", "12340987-1908")
])
def test_get_unique_field_name_from_message_should_return_expected_field(error_message: str,
                                                                         expected_field_name: str,
                                                                         expected_field_value: str) -> None:
    # Arrange
    # Act
    field_name, field_value = utils.get_unique_field_details_from_message(error_message)

    # Assert
    assert field_name == expected_field_name
    assert field_value == expected_field_value


@pytest.mark.parametrize("error_message, is_required_skipped, expected_title, expected_details", [
    ("""E422_000: 1 validation error for Request
    body -> first_name
      field required (type=value_error.missing)""", False,
     "1 validation error for Request",
     dict(first_name="field required")),
    ("""E422_001: 4 validation errors for Person
    business_entity_id
      field required (type=value_error.missing)
    email_promotion
      ensure this value is less than or equal to 2 (type=value_error.number.not_le; limit_value=2)
    rowguid
      field required (type=value_error.missing)
    modified_date
      field required (type=value_error.missing)""", False,
     "4 validation errors for Person",
     dict(business_entity_id="field required",
          email_promotion="ensure this value is less than or equal to 2",
          rowguid="field required",
          modified_date="field required")),
    ("""E422_001: 4 validation errors for Person
    business_entity_id
      field required (type=value_error.missing)
    email_promotion
      ensure this value is less than or equal to 2 (type=value_error.number.not_le; limit_value=2)
    rowguid
      field required (type=value_error.missing)
    modified_date
      field required (type=value_error.missing)""", True,
     "4 validation errors for Person",
     dict(email_promotion="ensure this value is less than or equal to 2"))
])
def test_get_validation_error_details_from_message_should_return_expected_details(error_message: str,
                                                                                  is_required_skipped: bool,
                                                                                  expected_title: str,
                                                                                  expected_details: Dict[str, str]) -> None:
    # Arrange
    # Act
    title, details = utils.get_validation_error_details_from_message(error_message, is_required_skipped)
    # Assert
    assert title == expected_title
    assert details == expected_details


@pytest.mark.parametrize("error_message, expected_details", [
    ("E400_003: (psycopg2.errors.UniqueViolation) duplicate key value "
     "violates unique constraint \"PK_PhoneNumberType_PhoneNumberTypeID\"\n"
    "DETAIL:  Key (\"PhoneNumberTypeID\")=(5) already exists.",
     PrimaryKeyErrorDetails(key_column="\"PhoneNumberTypeID\"", key_value="5")),
    ("E400_003: (psycopg2.errors.UniqueViolation) duplicate key value "
     "violates unique constraint \"PK_PersonPhone_BusinessEntityID_PhoneNumber_PhoneNumberTypeID\"\n"
    "DETAIL:  Key (\"BusinessEntityID\", \"PhoneNumber\", \"PhoneNumberTypeID\")=(20789, 575 049 461, 5) already exists.",
     PrimaryKeyErrorDetails(key_column="\"BusinessEntityID\", \"PhoneNumber\", \"PhoneNumberTypeID\"", key_value="20789, 575 049 461, 5"))
])
def test_get_primary_key_violence_details_should_return_expected_details(error_message: str,
                                                                         expected_details: PrimaryKeyErrorDetails) -> None:
    # Arrange
    # Act
    details = utils.get_primary_key_violence_details(error_message)

    # Assert
    assert details.key_column == expected_details.key_column
    assert details.key_value == expected_details.key_value


@pytest.mark.parametrize("error_message, expected_details", [
    ("E400_004: (psycopg2.errors.ForeignKeyViolation) insert or update on table \"PersonPhone\" "
     "violates foreign key constraint \"FK_PersonPhone_PhoneNumberType_PhoneNumberTypeID\"\n"
     "DETAIL:  Key (PhoneNumberTypeID)=(10) is not present in table \"PhoneNumberType\".",
     ForeignKeyErrorDetails(entity="PhoneNumberType", key_column="PhoneNumberTypeID", key_value="10")),
    ("E400_004: (psycopg2.errors.ForeignKeyViolation) insert or update on table \"PersonPhone\" "
     "violates foreign key constraint \"FK_PersonPhone_Person_BusinessEntityID\"\n"
     "DETAIL:  Key (BusinessEntityID)=(20786) is not present in table \"PhoneNumberType\".",
     ForeignKeyErrorDetails(entity="PhoneNumberType", key_column="BusinessEntityID", key_value="20786"))
])
def test_get_foreign_key_violence_details_should_return_expected_details(error_message: str,
                                                                         expected_details: ForeignKeyErrorDetails) -> None:
    # Arrange
    # Act
    details = utils.get_foreign_key_violence_details(error_message)

    # Assert
    assert details.entity == expected_details.entity
    assert details.key_column == expected_details.key_column
    assert details.key_value == expected_details.key_value
