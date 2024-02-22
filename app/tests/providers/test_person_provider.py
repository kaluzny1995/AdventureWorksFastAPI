import pytest
import sqlalchemy
from sqlmodel import create_engine
from typing import List

from app.config import PostgresdbConnectionConfig
from app.models import PersonInput, EPersonType
from app.providers import BusinessEntityProvider, PersonProvider
from app import errors

from app.tests.fixtures.fixtures_tests import create_tables, drop_tables


connection_string: str = PostgresdbConnectionConfig.get_db_connection_string(test_suffix="_test")
db_engine: sqlalchemy.engine.Engine = create_engine(connection_string)
person_provider: PersonProvider = PersonProvider(connection_string,
                                                 BusinessEntityProvider(connection_string, db_engine), db_engine)


@pytest.mark.parametrize("persons", [
    [PersonInput(person_type=EPersonType.GC, name_style="0",
                 title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
                 email_promotion=1,
                 additional_contact_info="<contact_details>?</contact_details>",
                 demographics="<demographic_details>?</demographic_details>"),
     PersonInput(person_type=EPersonType.SP, name_style="0",
                 title="Ms.", first_name="Alice", last_name="Doe", suffix="Jr",
                 email_promotion=2,
                 additional_contact_info="<contact_details><num>32/1a</num></contact_details>",
                 demographics="<demographic_details><country>England</country></demographic_details>"),
     PersonInput(person_type=EPersonType.IN, first_name="Mark", last_name="Sharon")],
    [PersonInput(person_type=EPersonType.EM, first_name="Dzhejkob", last_name="Awaria")]
])
def test_get_persons_should_return_valid_objects(persons: List[PersonInput]) -> None:
    create_tables(db_engine)

    # Arrange
    for person in persons:
        person_provider.insert_person(person)

    # Act
    expected_persons = person_provider.get_persons()

    # Assert
    assert len(persons) == len(expected_persons)
    for p, ep in zip(persons, expected_persons):
        assert ep.business_entity_id is not None
        assert p.person_type == ep.person_type
        assert p.name_style == ep.name_style
        assert p.title == ep.title
        assert p.first_name == ep.first_name
        assert p.middle_name == ep.middle_name
        assert p.last_name == ep.last_name
        assert p.suffix == ep.suffix
        assert p.email_promotion == ep.email_promotion
        assert p.additional_contact_info == ep.additional_contact_info
        assert p.demographics == ep.demographics
        assert ep.rowguid is not None
        assert ep.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("persons, expected_count", [
    ([PersonInput(person_type=EPersonType.GC, name_style="0",
                 title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
                 email_promotion=1,
                 additional_contact_info="<contact_details>?</contact_details>",
                 demographics="<demographic_details>?</demographic_details>"),
     PersonInput(person_type=EPersonType.SP, name_style="0",
                 title="Ms.", first_name="Alice", last_name="Doe", suffix="Jr",
                 email_promotion=2,
                 additional_contact_info="<contact_details><num>32/1a</num></contact_details>",
                 demographics="<demographic_details><country>England</country></demographic_details>"),
     PersonInput(person_type=EPersonType.IN, first_name="Mark", last_name="Sharon")], 3),
    ([PersonInput(person_type=EPersonType.EM, first_name="Dzhejkob", last_name="Awaria")], 1)
])
def test_count_persons_should_return_expected_number(persons: List[PersonInput], expected_count: int) -> None:
    create_tables(db_engine)

    # Arrange
    for person in persons:
        person_provider.insert_person(person)

    # Act
    count = person_provider.count_persons()

    # Assert
    assert count == expected_count

    drop_tables(db_engine)


@pytest.mark.parametrize("person", [
    PersonInput(person_type=EPersonType.GC, name_style="0",
                title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
                email_promotion=1,
                additional_contact_info="<contact_details>?</contact_details>",
                demographics="<demographic_details>?</demographic_details>"),
    PersonInput(person_type=EPersonType.EM, first_name="Dzhejkob", last_name="Awaria")
])
def test_get_person_should_return_valid_object(person: PersonInput) -> None:
    create_tables(db_engine)

    # Arrange
    person_id = person_provider.insert_person(person)

    # Act
    expected_person = person_provider.get_person(person_id)

    # Assert
    assert expected_person.business_entity_id is not None
    assert person.person_type == expected_person.person_type
    assert person.name_style == expected_person.name_style
    assert person.title == expected_person.title
    assert person.first_name == expected_person.first_name
    assert person.middle_name == expected_person.middle_name
    assert person.last_name == expected_person.last_name
    assert person.suffix == expected_person.suffix
    assert person.email_promotion == expected_person.email_promotion
    assert person.additional_contact_info == expected_person.additional_contact_info
    assert person.demographics == expected_person.demographics
    assert expected_person.rowguid is not None
    assert expected_person.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("person, expected_error", [
    (PersonInput(person_type=EPersonType.EM, first_name="Dzhejkob", last_name="Awaria"), errors.NotFoundError)
])
def test_get_person_should_raise_expected_error(person: PersonInput, expected_error: Exception) -> None:
    create_tables(db_engine)

    # Arrange
    person_provider.insert_person(person)

    with pytest.raises(expected_error):
        # Act
        # Assert
        person_provider.get_person(-1)

    drop_tables(db_engine)


@pytest.mark.parametrize("person", [
    PersonInput(person_type=EPersonType.IN, first_name="Mark", last_name="Sharon"),
    PersonInput(person_type=EPersonType.EM, first_name="Dzhejkob", last_name="Awaria")
])
def test_insert_person_should_insert_object(person: PersonInput) -> None:
    create_tables(db_engine)

    # Arrange
    # Act
    person_id = person_provider.insert_person(person)

    # Assert
    expected_person = person_provider.get_person(person_id)
    assert expected_person.business_entity_id is not None
    assert person.person_type == expected_person.person_type
    assert person.name_style == expected_person.name_style
    assert person.title == expected_person.title
    assert person.first_name == expected_person.first_name
    assert person.middle_name == expected_person.middle_name
    assert person.last_name == expected_person.last_name
    assert person.suffix == expected_person.suffix
    assert person.email_promotion == expected_person.email_promotion
    assert person.additional_contact_info == expected_person.additional_contact_info
    assert person.demographics == expected_person.demographics
    assert expected_person.rowguid is not None
    assert expected_person.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("person, updated_person", [
    (PersonInput(person_type=EPersonType.GC, name_style="0",
                 title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
                 email_promotion=1,
                 additional_contact_info="<contact_details>?</contact_details>",
                 demographics="<demographic_details>?</demographic_details>"),
     PersonInput(person_type=EPersonType.IN, name_style="1",
                 first_name="Johnny", last_name="Doey", suffix="JMJ",
                 email_promotion=2,
                 additional_contact_info="<contact_details><city>Los Angeles</city><state>CA</state></contact_details>",
                 demographics="<demographic_details><age>45</age></demographic_details>")
     ),
    (PersonInput(person_type=EPersonType.EM, first_name="Dzhejkob", last_name="Awaria"),
     PersonInput(person_type=EPersonType.GC, first_name="Dzejkob", last_name="Avaria"))
])
def test_update_person_should_update_object(person: PersonInput, updated_person: PersonInput) -> None:
    create_tables(db_engine)

    # Arrange
    person_id = person_provider.insert_person(person)
    original_person = person_provider.get_person(person_id)

    # Act
    updated_person_id = person_provider.update_person(person_id, updated_person)

    # Assert
    expected_person = person_provider.get_person(updated_person_id)
    assert original_person.business_entity_id == expected_person.business_entity_id
    assert updated_person.person_type == expected_person.person_type
    assert updated_person.name_style == expected_person.name_style
    assert updated_person.title == expected_person.title
    assert updated_person.first_name == expected_person.first_name
    assert updated_person.middle_name == expected_person.middle_name
    assert updated_person.last_name == expected_person.last_name
    assert updated_person.suffix == expected_person.suffix
    assert updated_person.email_promotion == expected_person.email_promotion
    assert updated_person.additional_contact_info == expected_person.additional_contact_info
    assert updated_person.demographics == expected_person.demographics
    assert original_person.rowguid == expected_person.rowguid
    assert original_person.modified_date <= expected_person.modified_date

    drop_tables(db_engine)


@pytest.mark.parametrize("person", [
    PersonInput(person_type=EPersonType.GC, name_style="0",
                title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
                email_promotion=1,
                additional_contact_info="<contact_details>?</contact_details>",
                demographics="<demographic_details>?</demographic_details>"),
    PersonInput(person_type=EPersonType.EM, first_name="Dzhejkob", last_name="Awaria")
])
def test_delete_person_should_delete_object(person: PersonInput) -> None:
    create_tables(db_engine)

    # Arrange
    person_id = person_provider.insert_person(person)

    # Act
    person_provider.delete_person(person_id)

    # Assert
    with pytest.raises(errors.NotFoundError):
        person_provider.get_person(person_id)

    drop_tables(db_engine)
