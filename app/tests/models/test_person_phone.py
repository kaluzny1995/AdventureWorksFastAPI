import pytest
import datetime as dt

from app.models import PersonPhone, PersonPhoneInput


@pytest.mark.parametrize("business_entity_id, phone_number, phone_number_type_id, expected_person_phone_input", [
    (101, "71 345 07 96", 1, PersonPhoneInput(business_entity_id=101, phone_number="71 345 07 96", phone_number_type_id=1)),
    (102, "1 (11) 500 555-0120", 2, PersonPhoneInput(business_entity_id=102, phone_number="1 (11) 500 555-0120", phone_number_type_id=2)),
    (103, "000 000 000", 3, PersonPhoneInput(business_entity_id=103, phone_number="000 000 000", phone_number_type_id=3)),
])
def test_person_phone_input_constructor_should_create_valid_object(
        business_entity_id: int, phone_number: str, phone_number_type_id: int,
        expected_person_phone_input: PersonPhoneInput
) -> None:
    # Act
    person_phone_input = PersonPhoneInput(business_entity_id=business_entity_id, phone_number=phone_number,
                                          phone_number_type_id=phone_number_type_id)

    # Assert
    assert person_phone_input.business_entity_id == expected_person_phone_input.business_entity_id
    assert person_phone_input.phone_number == expected_person_phone_input.phone_number
    assert person_phone_input.phone_number_type_id == expected_person_phone_input.phone_number_type_id


@pytest.mark.parametrize("business_entity_id, phone_number, phone_number_type_id, modified_date, expected_person_phone", [
    (101, "71 345 07 96", 1, dt.datetime(2020, 1, 1, 0, 0, 0),
     PersonPhone(business_entity_id=101, phone_number="71 345 07 96", phone_number_type_id=1,
                 modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (102, "1 (11) 500 555-0120", 2, dt.datetime(2020, 1, 1, 0, 0, 0),
     PersonPhone(business_entity_id=102, phone_number="1 (11) 500 555-0120", phone_number_type_id=2,
                 modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (103, "000 000 000", 3, dt.datetime(2020, 1, 1, 0, 0, 0),
     PersonPhone(business_entity_id=103, phone_number="000 000 000", phone_number_type_id=3,
                 modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
])
def test_person_phone_constructor_should_create_valid_object(
        business_entity_id: int, phone_number: str, phone_number_type_id: int, modified_date: dt.datetime,
        expected_person_phone: PersonPhone
) -> None:
    # Act
    person_phone = PersonPhone(business_entity_id=business_entity_id, phone_number=phone_number,
                               phone_number_type_id=phone_number_type_id, modified_date=modified_date)

    # Assert
    assert person_phone.business_entity_id == expected_person_phone.business_entity_id
    assert person_phone.phone_number == expected_person_phone.phone_number
    assert person_phone.phone_number_type_id == expected_person_phone.phone_number_type_id
    assert person_phone.modified_date == expected_person_phone.modified_date


@pytest.mark.parametrize("person_phone, person_phone_input, expected_person_phone", [
    (PersonPhone(business_entity_id=101, phone_number="71 345 07 96", phone_number_type_id=1,
                 modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
     PersonPhoneInput(business_entity_id=102, phone_number="71 345 07 66", phone_number_type_id=1),
     PersonPhone(business_entity_id=102, phone_number="71 345 07 66", phone_number_type_id=1,
                 modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (PersonPhone(business_entity_id=101, phone_number="71 345 07 96", phone_number_type_id=1,
                 modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
     PersonPhoneInput(business_entity_id=101, phone_number="000 000 000", phone_number_type_id=2),
     PersonPhone(business_entity_id=101, phone_number="000 000 000", phone_number_type_id=2,
                 modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
])
def test_update_person_phone_from_input_return_valid_object(person_phone: PersonPhone, person_phone_input: PersonPhoneInput,
                                                            expected_person_phone: PersonPhone) -> None:
    # Arrange
    original_person_phone = PersonPhone(**person_phone.dict())
    # Act
    updated_person_phone = person_phone.update_from_input(person_phone_input)

    # Assert
    assert updated_person_phone.business_entity_id == expected_person_phone.business_entity_id
    assert updated_person_phone.phone_number == expected_person_phone.phone_number
    assert updated_person_phone.phone_number_type_id == expected_person_phone.phone_number_type_id
    assert original_person_phone.modified_date == expected_person_phone.modified_date
