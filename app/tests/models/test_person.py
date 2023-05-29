import pytest
import datetime as dt
import uuid
from typing import Optional

from app.models import Person, PersonInput, EPersonType


@pytest.mark.parametrize("person_type, name_style, "
                         "title, first_name, middle_name, last_name, suffix, "
                         "email_promotion, additional_contact_info, demographics, "
                         "expected_person_input", [
                             (EPersonType.GC, "0", "Mr.", "John", "J.", "Doe", "Jr", 1,
                              "<contact_details>?</contact_details>", "<demographic_details>?</demographic_details>",
                              PersonInput(person_type=EPersonType.GC, name_style="0",
                                          title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
                                          email_promotion=1,
                                          additional_contact_info="<contact_details>?</contact_details>",
                                          demographics="<demographic_details>?</demographic_details>")),
                             (EPersonType.IN, "1", None, "Dzhejkob", None, "Awaria", None, 2, None, None,
                              PersonInput(person_type=EPersonType.IN, name_style="1",
                                          first_name="Dzhejkob", last_name="Awaria", email_promotion=2)),
                             (EPersonType.EM, "0", None, "Johnny", None, "Doey", None, 0, None, None,
                              PersonInput(person_type=EPersonType.EM, first_name="Johnny", last_name="Doey"))
                         ])
def test_person_input_constructor_should_create_valid_object(
        person_type: EPersonType, name_style: str,
        title: Optional[str], first_name: str, middle_name: Optional[str], last_name: str, suffix: Optional[str],
        email_promotion: int, additional_contact_info: Optional[str], demographics: Optional[str],
        expected_person_input: PersonInput
) -> None:
    # Act
    person_input = PersonInput(person_type=person_type, name_style=name_style,
                               title=title, first_name=first_name, middle_name=middle_name, last_name=last_name, suffix=suffix,
                               email_promotion=email_promotion,
                               additional_contact_info=additional_contact_info, demographics=demographics)

    # Assert
    assert person_input.person_type == expected_person_input.person_type
    assert person_input.name_style == expected_person_input.name_style
    assert person_input.title == expected_person_input.title
    assert person_input.first_name == expected_person_input.first_name
    assert person_input.middle_name == expected_person_input.middle_name
    assert person_input.last_name == expected_person_input.last_name
    assert person_input.suffix == expected_person_input.suffix
    assert person_input.email_promotion == expected_person_input.email_promotion
    assert person_input.additional_contact_info == expected_person_input.additional_contact_info
    assert person_input.demographics == expected_person_input.demographics


@pytest.mark.parametrize("business_entity_id, person_type, name_style, "
                         "title, first_name, middle_name, last_name, suffix, "
                         "email_promotion, additional_contact_info, demographics, rowguid, modified_date, "
                         "expected_person", [
                             (101, EPersonType.GC, "0", "Mr.", "John", "J.", "Doe", "Jr", 1,
                              "<contact_details>?</contact_details>", "<demographic_details>?</demographic_details>",
                              uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"), dt.datetime(2020, 1, 1, 0, 0, 0),
                              Person(business_entity_id=101, person_type=EPersonType.GC, name_style="0",
                                     title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
                                     email_promotion=1,
                                     additional_contact_info="<contact_details>?</contact_details>",
                                     demographics="<demographic_details>?</demographic_details>",
                                     rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
                                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
                             (101, EPersonType.IN, "1", None, "Dzhejkob", None, "Awaria", None, 2, None, None,
                              uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"), dt.datetime(2020, 1, 1, 0, 0, 0),
                              Person(business_entity_id=101, person_type=EPersonType.IN, name_style="1",
                                     first_name="Dzhejkob", last_name="Awaria", email_promotion=2,
                                     rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
                                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
                             (101, EPersonType.EM, "0", None, "Johnny", None, "Doey", None, 1, None, None,
                              uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"), dt.datetime(2020, 1, 1, 0, 0, 0),
                              Person(business_entity_id=101, person_type=EPersonType.EM, name_style="0",
                                     first_name="Johnny", last_name="Doey", email_promotion=1,
                                     rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
                                     modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)))
                         ])
def test_person_constructor_should_create_valid_object(
        business_entity_id: int, person_type: EPersonType, name_style: str,
        title: Optional[str], first_name: str, middle_name: Optional[str], last_name: str, suffix: Optional[str],
        email_promotion: int, additional_contact_info: Optional[str], demographics: Optional[str],
        rowguid: uuid.UUID, modified_date: dt.datetime,
        expected_person: Person
) -> None:
    # Act
    person = Person(business_entity_id=business_entity_id, person_type=person_type, name_style=name_style,
                    title=title, first_name=first_name, middle_name=middle_name, last_name=last_name, suffix=suffix,
                    email_promotion=email_promotion,
                    additional_contact_info=additional_contact_info, demographics=demographics,
                    rowguid=rowguid, modified_date=modified_date)

    # Assert
    assert person.business_entity_id == expected_person.business_entity_id
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
    assert person.rowguid == expected_person.rowguid
    assert person.modified_date == expected_person.modified_date


@pytest.mark.parametrize("person, person_input, expected_person", [
    (Person(business_entity_id=101, person_type=EPersonType.GC, name_style="0",
            title="Mr.", first_name="John", middle_name="J.", last_name="Doe", suffix="Jr",
            email_promotion=2,
            additional_contact_info="<contact_details>?</contact_details>",
            demographics="<demographic_details>?</demographic_details>",
            rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
            modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
     PersonInput(person_type=EPersonType.EM, name_style="1",
                 title="Mr", first_name="Dzhejkob", middle_name="J", last_name="Awaria", suffix="JMJ",
                 email_promotion=2,
                 additional_contact_info="<contact_details><state>PL</state></contact_details>",
                 demographics="<demographic_details><status>free</status></demographic_details>"),
     Person(business_entity_id=101, person_type=EPersonType.EM, name_style="1",
            title="Mr", first_name="Dzhejkob", middle_name="J", last_name="Awaria", suffix="JMJ",
            email_promotion=2,
            additional_contact_info="<contact_details><state>PL</state></contact_details>",
            demographics="<demographic_details><status>free</status></demographic_details>",
            rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
            modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (Person(business_entity_id=101, person_type=EPersonType.EM, name_style="1",
            first_name="Johnny", last_name="Doey", email_promotion=1,
            rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
            modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
     PersonInput(person_type=EPersonType.VC, first_name="Johnny D.", last_name="Doey M."),
     Person(business_entity_id=101, person_type=EPersonType.VC, name_style="0",
            first_name="Johnny D.", last_name="Doey M.", email_promotion=0,
            rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
            modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)))
])
def test_update_person_from_input_return_valid_object(person: Person, person_input: PersonInput,
                                                      expected_person: Person) -> None:
    # Arrange
    original_person = Person(**person.dict())
    # Act
    updated_person = person.update_from_input(person_input)

    # Assert
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
    assert original_person.modified_date == expected_person.modified_date
