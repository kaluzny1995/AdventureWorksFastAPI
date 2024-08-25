import pytest
import datetime as dt
import uuid
from typing import Optional

from app.models import PhoneNumberType, PhoneNumberTypeInput


@pytest.mark.parametrize("name, expected_phone_number_type_input", [
    ("Cell", PhoneNumberTypeInput(name="Cell")),
    ("Mobile", PhoneNumberTypeInput(name="Mobile")),
    ("Home", PhoneNumberTypeInput(name="Home"))
])
def test_phone_number_type_input_constructor_should_create_valid_object(
        name: str,
        expected_phone_number_type_input: PhoneNumberTypeInput
) -> None:
    # Act
    phone_number_type_input = PhoneNumberTypeInput(name=name)

    # Assert
    assert phone_number_type_input.name == expected_phone_number_type_input.name


@pytest.mark.parametrize("phone_number_type_id, name, modified_date, expected_phone_number_type", [
    (101, "Cell", dt.datetime(2020, 1, 1, 0, 0, 0),
     PhoneNumberType(phone_number_type_id=101, name="Cell",
                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (101, "Mobile", dt.datetime(2020, 1, 1, 0, 0, 0),
     PhoneNumberType(phone_number_type_id=101, name="Mobile",
                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (101, "Home", dt.datetime(2020, 1, 1, 0, 0, 0),
     PhoneNumberType(phone_number_type_id=101, name="Home",
                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)))
])
def test_phone_number_type_constructor_should_create_valid_object(
        phone_number_type_id: int, name: str, modified_date: dt.datetime,
        expected_phone_number_type: PhoneNumberType
) -> None:
    # Act
    phone_number_type = PhoneNumberType(phone_number_type_id=phone_number_type_id, name=name,
                                        modified_date=modified_date)

    # Assert
    assert phone_number_type.phone_number_type_id == expected_phone_number_type.phone_number_type_id
    assert phone_number_type.name == expected_phone_number_type.name
    assert phone_number_type.modified_date == expected_phone_number_type.modified_date


@pytest.mark.parametrize("phone_number_type, phone_number_type_input, expected_phone_number_type", [
    (PhoneNumberType(phone_number_type_id=101, name="Cell",
                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
     PhoneNumberTypeInput(name="Mobile"),
     PhoneNumberType(phone_number_type_id=101, name="Mobile",
                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (PhoneNumberType(phone_number_type_id=101, name="Mobile",
                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
     PhoneNumberTypeInput(name="Home"),
     PhoneNumberType(phone_number_type_id=101, name="Home",
                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)))
])
def test_update_phone_number_type_from_input_return_valid_object(phone_number_type: PhoneNumberType,
                                                                 phone_number_type_input: PhoneNumberTypeInput,
                                                                 expected_phone_number_type: PhoneNumberType) -> None:
    # Arrange
    original_phone_number_type = PhoneNumberType(**phone_number_type.dict())
    # Act
    updated_phone_number_type = phone_number_type.update_from_input(phone_number_type_input)

    # Assert
    assert original_phone_number_type.phone_number_type_id == expected_phone_number_type.phone_number_type_id
    assert updated_phone_number_type.name == expected_phone_number_type.name
    assert original_phone_number_type.modified_date == expected_phone_number_type.modified_date
