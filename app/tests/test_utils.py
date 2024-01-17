from typing import Dict
import pytest

from app.models import ForeignKeyErrorDetails
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


@pytest.mark.parametrize("error_message, expected_username", [
    ("Current user 'testuser' has readonly restricted access.", "testuser"),
    ("Current user 'testuser2' has readonly restricted access.", "testuser2"),
    ("Current user 'testuser22' has readonly restricted access.", "testuser22")
])
def test_get_username_from_message_should_return_expected_username(error_message: str,
                                                                   expected_username: str) -> None:
    # Arrange
    # Act
    username = utils.get_username_from_message(error_message)

    # Assert
    assert username == expected_username


@pytest.mark.parametrize("error_message, expected_field_name, expected_field_value", [
    ("Provided username 'testuser' already exists.", "username", "testuser"),
    ("Provided email 'test.user@test.com' already exists.", "email", "test.user@test.com"),
    ("Provided uuid '12340987-1908' already exists.", "uuid", "12340987-1908")
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
    ("""1 validation error for Request
    body -> first_name
      field required (type=value_error.missing)""", False,
     "1 validation error for Request",
     dict(first_name="field required")),
    ("""4 validation errors for Person
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
    ("""4 validation errors for Person
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
    ("(psycopg2.errors.ForeignKeyViolation) insert or update on table \"PersonPhone\" violates foreign key constraint "
     "\"FK_PersonPhone_PhoneNumberType_PhoneNumberTypeID\"\n"
     "DETAIL:  Key (PhoneNumberTypeID)=(10) is not present in table \"PhoneNumberType\".",
     ForeignKeyErrorDetails(line="DETAIL:  Key (PhoneNumberTypeID)=(10) is not present in table \"PhoneNumberType\".",
                            entity="PhoneNumberType", key_column="PhoneNumberTypeID", key_value="10")),
    ("(psycopg2.errors.ForeignKeyViolation) insert or update on table \"PersonPhone\" violates foreign key constraint "
     "\"FK_PersonPhone_Person_BusinessEntityID\"\n"
     "DETAIL:  Key (BusinessEntityID)=(20786) is not present in table \"PhoneNumberType\".",
     ForeignKeyErrorDetails(line="DETAIL:  Key (BusinessEntityID)=(20786) is not present in table \"PhoneNumberType\".",
                            entity="PhoneNumberType", key_column="BusinessEntityID", key_value="20786"))
])
def test_get_foreign_key_violence_details_should_return_expected_details(error_message: str,
                                                                         expected_details: ForeignKeyErrorDetails) -> None:
    # Arrange
    # Act
    details = utils.get_foreign_key_violence_details(error_message)

    # Assert
    assert details.line == expected_details.line
    assert details.entity == expected_details.entity
    assert details.key_column == expected_details.key_column
    assert details.key_value == expected_details.key_value
