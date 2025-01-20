import pytest
import sqlalchemy
from sqlmodel import create_engine
from typing import List

from app.config import PostgresdbConnectionConfig
from app.models import PersonPhoneInput
from app.providers import PersonPhoneProvider
from app import errors

from app.tests.fixtures.fixtures_tests import (create_tables, drop_tables,
                                               insert_test_persons, insert_test_phone_number_types,
                                               insert_test_person_phones)


connection_string: str = PostgresdbConnectionConfig.get_db_connection_string(test_suffix="_test")
db_engine: sqlalchemy.engine.Engine = create_engine(connection_string)
person_phone_provider: PersonPhoneProvider = PersonPhoneProvider(connection_string, db_engine)


@pytest.mark.parametrize("person_phones", [
    [PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1),
     PersonPhoneInput(business_entity_id=1, phone_number="666 666 666", phone_number_type_id=1),
     PersonPhoneInput(business_entity_id=1, phone_number="999 000 999", phone_number_type_id=2),
     PersonPhoneInput(business_entity_id=4, phone_number="123456789", phone_number_type_id=3)],
    [PersonPhoneInput(business_entity_id=5, phone_number="338 94 95", phone_number_type_id=3)]
])
def test_get_person_phones_should_return_valid_objects(person_phones: List[PersonPhoneInput]) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    for person_phone in person_phones:
        person_phone_provider.insert_person_phone(person_phone)

    # Act
    expected_person_phones = person_phone_provider.get_person_phones()

    # Assert
    assert len(person_phones) == len(expected_person_phones)
    for pp, epp in zip(person_phones, expected_person_phones):
        assert pp.business_entity_id == epp[0].business_entity_id
        assert pp.phone_number == epp[0].phone_number
        assert pp.phone_number_type_id == epp[0].phone_number_type_id
        assert epp[0].modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phones, expected_count", [
    ([PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1),
     PersonPhoneInput(business_entity_id=1, phone_number="666 666 666", phone_number_type_id=1),
     PersonPhoneInput(business_entity_id=1, phone_number="999 000 999", phone_number_type_id=2),
     PersonPhoneInput(business_entity_id=4, phone_number="123456789", phone_number_type_id=3)], 4),
    ([PersonPhoneInput(business_entity_id=5, phone_number="338 94 95", phone_number_type_id=3)], 1)
])
def test_count_person_phones_should_return_expected_number(person_phones: List[PersonPhoneInput], expected_count: int) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    for person_phone in person_phones:
        person_phone_provider.insert_person_phone(person_phone)

    # Act
    count = person_phone_provider.count_person_phones()

    # Assert
    assert count == expected_count

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phone", [
    PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1),
    PersonPhoneInput(business_entity_id=5, phone_number="338 94 95", phone_number_type_id=3)
])
def test_get_person_phone_should_return_valid_object(person_phone: PersonPhoneInput) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    person_phone_id = person_phone_provider.insert_person_phone(person_phone)

    # Act
    expected_person_phone = person_phone_provider.get_person_phone(person_phone_id)

    # Assert
    assert person_phone.business_entity_id == expected_person_phone[0].business_entity_id
    assert person_phone.phone_number == expected_person_phone[0].phone_number
    assert person_phone.phone_number_type_id == expected_person_phone[0].phone_number_type_id
    assert expected_person_phone[0].modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phone, expected_error", [
    (PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1), errors.NotFoundError)
])
def test_get_person_phone_should_raise_expected_error(person_phone: PersonPhoneInput, expected_error: Exception) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    person_phone_provider.insert_person_phone(person_phone)

    with pytest.raises(expected_error):
        # Act
        # Assert
        person_phone_provider.get_person_phone(tuple((-1, "", -1)))

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phone", [
    PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1),
    PersonPhoneInput(business_entity_id=5, phone_number="338 94 95", phone_number_type_id=3)
])
def test_insert_person_phone_should_insert_object(person_phone: PersonPhoneInput) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    # Act
    person_phone_id = person_phone_provider.insert_person_phone(person_phone)

    # Assert
    expected_person_phone = person_phone_provider.get_person_phone(person_phone_id)
    assert person_phone.business_entity_id == expected_person_phone[0].business_entity_id
    assert person_phone.phone_number == expected_person_phone[0].phone_number
    assert person_phone.phone_number_type_id == expected_person_phone[0].phone_number_type_id
    assert expected_person_phone[0].modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phone, expected_error", [
    (PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1), errors.IntegrityError),
    (PersonPhoneInput(business_entity_id=11, phone_number="000 000 000", phone_number_type_id=5), errors.IntegrityError),
    (PersonPhoneInput(business_entity_id=10, phone_number="000 000 000", phone_number_type_id=6), errors.IntegrityError)
])
def test_insert_person_phone_should_raise_expected_error(person_phone: PersonPhoneInput, expected_error: Exception):
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    insert_test_person_phones(db_engine, connection_string)
    with pytest.raises(expected_error):
        # Act
        # Assert
        person_phone_provider.insert_person_phone(person_phone)

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phone, updated_person_phone", [
    (PersonPhoneInput(business_entity_id=1, phone_number="000 000 123", phone_number_type_id=1),
     PersonPhoneInput(business_entity_id=1, phone_number="000 123 000", phone_number_type_id=1)),
    (PersonPhoneInput(business_entity_id=2, phone_number="000 000 000", phone_number_type_id=2),
     PersonPhoneInput(business_entity_id=3, phone_number="000 000 000", phone_number_type_id=3)),
])
def test_update_person_phone_should_update_object(person_phone: PersonPhoneInput,
                                                  updated_person_phone: PersonPhoneInput) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    person_phone_id = person_phone_provider.insert_person_phone(person_phone)
    original_person_phone = person_phone_provider.get_person_phone(person_phone_id)

    # Act
    updated_person_phone_id = person_phone_provider.update_person_phone(person_phone_id, updated_person_phone)

    # Assert
    expected_person_phone = person_phone_provider.get_person_phone(updated_person_phone_id)
    assert updated_person_phone.business_entity_id == expected_person_phone[0].business_entity_id
    assert updated_person_phone.phone_number == expected_person_phone[0].phone_number
    assert updated_person_phone.phone_number_type_id == expected_person_phone[0].phone_number_type_id
    assert original_person_phone[0].modified_date <= expected_person_phone[0].modified_date

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phone, updated_person_phone, expected_error", [
    (PersonPhoneInput(business_entity_id=1, phone_number="000 000 123", phone_number_type_id=1),
     PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1), errors.IntegrityError),
    (PersonPhoneInput(business_entity_id=2, phone_number="000 000 000", phone_number_type_id=2),
     PersonPhoneInput(business_entity_id=11, phone_number="000 000 000", phone_number_type_id=2), errors.IntegrityError),
    (PersonPhoneInput(business_entity_id=2, phone_number="000 000 000", phone_number_type_id=2),
     PersonPhoneInput(business_entity_id=2, phone_number="000 000 000", phone_number_type_id=6), errors.IntegrityError)
])
def test_update_person_phone_should_raise_expected_error(person_phone: PersonPhoneInput,
                                                         updated_person_phone: PersonPhoneInput,
                                                         expected_error: Exception) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    insert_test_person_phones(db_engine, connection_string)

    person_phone_id = person_phone_provider.insert_person_phone(person_phone)
    with pytest.raises(expected_error):
        # Act
        # Assert
        person_phone_provider.update_person_phone(person_phone_id, updated_person_phone)

    drop_tables(db_engine)


@pytest.mark.parametrize("person_phone", [
    PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1),
    PersonPhoneInput(business_entity_id=5, phone_number="338 94 95", phone_number_type_id=3)
])
def test_delete_person_phone_should_delete_object(person_phone: PersonPhoneInput) -> None:
    create_tables(db_engine)
    insert_test_persons(db_engine, connection_string)
    insert_test_phone_number_types(db_engine, connection_string)

    # Arrange
    person_phone_id = person_phone_provider.insert_person_phone(person_phone)

    # Act
    person_phone_provider.delete_person_phone(person_phone_id)

    # Assert
    with pytest.raises(errors.NotFoundError):
        person_phone_provider.get_person_phone(person_phone_id)

    drop_tables(db_engine)
