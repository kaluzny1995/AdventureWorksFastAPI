import pytest
from typing import List

from app.models import PersonPhone
from app.services import PersonPhoneService

from app.tests.fixtures.fixtures_entry_lists import person_phones
from app.tests.fixtures.fixtures_person_phone_provider_stub import PersonPhoneProviderStub


@pytest.mark.parametrize("person_id, expected_person_phones", [
    (1, [person_phones[0], person_phones[1], person_phones[2]]),
    (4, [person_phones[3]]),
    (6, []),
    (8, [person_phones[7]]),
])
def test_get_persons_person_phones_should_return_valid_objects(person_id: int,
                                                               expected_person_phones: List[PersonPhone]):
    # Arrange
    person_phone_service: PersonPhoneService = PersonPhoneService(PersonPhoneProviderStub(expected_person_phones))
    # Act
    returned_person_phones = person_phone_service.get_persons_person_phones(person_id)
    # Assert
    assert len(returned_person_phones) == len(expected_person_phones)
    for rpp, epp in zip(returned_person_phones, expected_person_phones):
        assert rpp[0].business_entity_id == epp.business_entity_id
        assert rpp[0].phone_number == epp.phone_number
        assert rpp[0].phone_number_type_id == epp.phone_number_type_id


@pytest.mark.parametrize("phone_number_type_id, expected_person_phones", [
    (1, [person_phones[0], person_phones[1]]),
    (2, [person_phones[2]]),
    (3, [person_phones[3], person_phones[4], person_phones[6]]),
    (6, []),
])
def test_get_phone_number_types_person_phones_should_return_valid_objects(phone_number_type_id: int,
                                                                          expected_person_phones: List[PersonPhone]):
    # Arrange
    person_phone_service: PersonPhoneService = PersonPhoneService(PersonPhoneProviderStub(expected_person_phones))
    # Act
    returned_person_phones = person_phone_service.get_phone_number_types_person_phones(phone_number_type_id)
    # Assert
    assert len(returned_person_phones) == len(expected_person_phones)
    for rpp, epp in zip(returned_person_phones, expected_person_phones):
        assert rpp[0].business_entity_id == epp.business_entity_id
        assert rpp[0].phone_number == epp.phone_number
        assert rpp[0].phone_number_type_id == epp.phone_number_type_id
