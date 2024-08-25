import pytest
import sqlalchemy
from sqlmodel import create_engine
from typing import List

from app.config import PostgresdbConnectionConfig
from app.models import PhoneNumberTypeInput
from app.providers import PhoneNumberTypeProvider
from app import errors

from app.tests.fixtures.fixtures_tests import create_tables, drop_tables


connection_string: str = PostgresdbConnectionConfig.get_db_connection_string(test_suffix="_test")
db_engine: sqlalchemy.engine.Engine = create_engine(connection_string)
phone_number_type_provider: PhoneNumberTypeProvider = PhoneNumberTypeProvider(connection_string, db_engine)


@pytest.mark.parametrize("phone_number_types", [
    [PhoneNumberTypeInput(name="Cell"),
     PhoneNumberTypeInput(name="Mobile"),
     PhoneNumberTypeInput(name="Home")],
    [PhoneNumberTypeInput(name="Cell")]
])
def test_get_phone_number_types_should_return_valid_objects(phone_number_types: List[PhoneNumberTypeInput]) -> None:
    create_tables(db_engine)

    # Arrange
    for phone_number_type in phone_number_types:
        phone_number_type_provider.insert_phone_number_type(phone_number_type)

    # Act
    expected_phone_number_types = phone_number_type_provider.get_phone_number_types()

    # Assert
    assert len(phone_number_types) == len(expected_phone_number_types)
    for pnt, epnt in zip(phone_number_types, expected_phone_number_types):
        assert epnt.phone_number_type_id is not None
        assert pnt.name == epnt.name
        assert epnt.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("phone_number_types, expected_count", [
    ([PhoneNumberTypeInput(name="Cell"),
      PhoneNumberTypeInput(name="Mobile"),
      PhoneNumberTypeInput(name="Home")], 3),
    ([PhoneNumberTypeInput(name="Cell")], 1)
])
def test_count_phone_number_types_should_return_expected_number(phone_number_types: List[PhoneNumberTypeInput],
                                                                expected_count: int) -> None:
    create_tables(db_engine)

    # Arrange
    for phone_number_type in phone_number_types:
        phone_number_type_provider.insert_phone_number_type(phone_number_type)

    # Act
    count = phone_number_type_provider.count_phone_number_types()

    # Assert
    assert count == expected_count

    drop_tables(db_engine)


@pytest.mark.parametrize("phone_number_type", [
    PhoneNumberTypeInput(name="Cell"),
    PhoneNumberTypeInput(name="Mobile")
])
def test_get_phone_number_type_should_return_valid_object(phone_number_type: PhoneNumberTypeInput) -> None:
    create_tables(db_engine)

    # Arrange
    phone_number_type_id = phone_number_type_provider.insert_phone_number_type(phone_number_type)

    # Act
    expected_phone_number_type = phone_number_type_provider.get_phone_number_type(phone_number_type_id)

    # Assert
    assert expected_phone_number_type.phone_number_type_id is not None
    assert phone_number_type.name == expected_phone_number_type.name
    assert expected_phone_number_type.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("phone_number_type, expected_error", [
    (PhoneNumberTypeInput(name="Cell"), errors.NotFoundError)
])
def test_get_phone_number_type_should_raise_expected_error(phone_number_type: PhoneNumberTypeInput,
                                                           expected_error: Exception) -> None:
    create_tables(db_engine)

    # Arrange
    phone_number_type_provider.insert_phone_number_type(phone_number_type)

    with pytest.raises(expected_error):
        # Act
        # Assert
        phone_number_type_provider.get_phone_number_type(-1)

    drop_tables(db_engine)


@pytest.mark.parametrize("phone_number_type", [
    PhoneNumberTypeInput(name="Cell"),
    PhoneNumberTypeInput(name="Mobile")
])
def test_insert_phone_number_type_should_insert_object(phone_number_type: PhoneNumberTypeInput) -> None:
    create_tables(db_engine)

    # Arrange
    # Act
    phone_number_type_id = phone_number_type_provider.insert_phone_number_type(phone_number_type)

    # Assert
    expected_phone_number_type = phone_number_type_provider.get_phone_number_type(phone_number_type_id)
    assert expected_phone_number_type.phone_number_type_id is not None
    assert phone_number_type.name == expected_phone_number_type.name
    assert expected_phone_number_type.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("phone_number_type, updated_phone_number_type", [
    (PhoneNumberTypeInput(name="Cell"),
     PhoneNumberTypeInput(name="Mobile")
     ),
    (PhoneNumberTypeInput(name="Mobile"),
     PhoneNumberTypeInput(name="Home"))
])
def test_update_phone_number_type_should_update_object(phone_number_type: PhoneNumberTypeInput,
                                                       updated_phone_number_type: PhoneNumberTypeInput) -> None:
    create_tables(db_engine)

    # Arrange
    phone_number_type_id = phone_number_type_provider.insert_phone_number_type(phone_number_type)
    original_phone_number_type = phone_number_type_provider.get_phone_number_type(phone_number_type_id)

    # Act
    updated_phone_number_type_id = phone_number_type_provider.update_phone_number_type(phone_number_type_id,
                                                                                       updated_phone_number_type)

    # Assert
    expected_phone_number_type = phone_number_type_provider.get_phone_number_type(updated_phone_number_type_id)
    assert original_phone_number_type.phone_number_type_id == expected_phone_number_type.phone_number_type_id
    assert updated_phone_number_type.name == expected_phone_number_type.name
    assert original_phone_number_type.modified_date <= expected_phone_number_type.modified_date

    drop_tables(db_engine)


@pytest.mark.parametrize("phone_number_type", [
    PhoneNumberTypeInput(name="Cell"),
    PhoneNumberTypeInput(name="Mobile")
])
def test_delete_phone_number_type_should_delete_object(phone_number_type: PhoneNumberTypeInput) -> None:
    create_tables(db_engine)

    # Arrange
    phone_number_type_id = phone_number_type_provider.insert_phone_number_type(phone_number_type)

    # Act
    phone_number_type_provider.delete_phone_number_type(phone_number_type_id)

    # Assert
    with pytest.raises(errors.NotFoundError):
        phone_number_type_provider.get_phone_number_type(phone_number_type_id)

    drop_tables(db_engine)
