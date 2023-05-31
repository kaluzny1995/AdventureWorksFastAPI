import pytest
import uuid
import datetime as dt
from typing import Optional, List

from app.models import Person, EPersonType
from app.services import PersonService
from app import errors

from app.tests.fixtures.fixtures_person_provider_stub import PersonProviderStub


persons: List[Person] = [
    Person(business_entity_id=101, person_type=EPersonType.GC, first_name="John", last_name="Doe",
           rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=102, person_type=EPersonType.EM, first_name="John", last_name="Smith",
           rowguid=uuid.UUID("d54e0552-c226-4c22-af3b-762ca854cdd3"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=103, person_type=EPersonType.IN, first_name="John", last_name="Adams",
           rowguid=uuid.UUID("08f5d3bd-82bf-49ba-baed-5616d41ccf24"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=104, person_type=EPersonType.VC, first_name="John", middle_name="K", last_name="Adams",
           rowguid=uuid.UUID("9cc28d7c-c5c4-4c1d-9e9f-b616f150c482"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=105, person_type=EPersonType.SP, first_name="John", middle_name="J", last_name="Adams",
           rowguid=uuid.UUID("548302a3-de74-4ee2-bf22-8d1b99bb733d"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=106, person_type=EPersonType.SC, first_name="Brian", last_name="Washer",
           rowguid=uuid.UUID("7bd00ca1-928f-4aff-947c-a28400a3b3a7"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=107, person_type=EPersonType.GC, first_name="Aaron", last_name="Dasmi",
           rowguid=uuid.UUID("5d985c90-d51c-4256-8c77-bf62247c0c5c"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=108, person_type=EPersonType.SC, first_name="Aaron", last_name="Washington",
           rowguid=uuid.UUID("5d661b5f-e018-4851-9444-f8fcc064b705"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=109, person_type=EPersonType.IN, first_name="Sharon", last_name="Smith",
           rowguid=uuid.UUID("d0a3b1a7-78b6-4cf5-b788-b735b4e95537"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    Person(business_entity_id=110, person_type=EPersonType.VC, first_name="Claire", last_name="Smith",
           rowguid=uuid.UUID("8ee9e7b7-89df-46a4-9c29-7c56270bd847"), modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
]
person_service: PersonService = PersonService(PersonProviderStub(persons))


@pytest.mark.parametrize("first_name_phrase, last_name_phrase, expected_persons, expected_error", [
    (None, None, [], errors.EmptyFieldsError),
    ("john", None, [persons[2], persons[4], persons[3], persons[0], persons[1]], None),
    (None, "ada", [persons[2], persons[4], persons[3]], None),
    ("ron", "smi", [persons[6], persons[8]], None)
])
def test_get_persons_by_phrases_should_return_valid_objects_or_raise_error(first_name_phrase: Optional[str],
                                                                           last_name_phrase: Optional[str],
                                                                           expected_persons: List[Person],
                                                                           expected_error: Exception) -> None:
    # Arrange
    if expected_error is None:
        # Act
        returned_persons = person_service.get_persons_by_phrases(first_name_phrase, last_name_phrase)

        # Assert
        assert len(returned_persons) == len(expected_persons)
        for rp, ep in zip(returned_persons, expected_persons):
            assert rp.business_entity_id == ep.business_entity_id
    else:
        # Act
        # Assert
        with pytest.raises(expected_error):
            person_service.get_persons_by_phrases(first_name_phrase, last_name_phrase)
