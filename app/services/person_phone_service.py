from typing import Optional, List, Tuple

from app import errors
from app.providers import IPersonPhoneProvider, PersonPhoneProvider
from app.models import E400BadRequest, Person, PhoneNumberType, PersonPhone


class PersonPhoneService:
    person_phone_provider: IPersonPhoneProvider

    def __init__(self, person_phone_provider: Optional[IPersonPhoneProvider] = None):
        self.person_phone_provider = person_phone_provider or PersonPhoneProvider()

    def get_persons_person_phones(self, person_id: int) -> List[Tuple[PersonPhone, Person, PhoneNumberType]]:
        """ Returns list of person phones assigned to a person of given person_id """
        filter_string = f"person_ids:[{person_id}]"

        return self.person_phone_provider.get_person_phones(filters=filter_string)

    def get_phone_number_types_person_phones(self, phone_number_type_id: int) -> List[Tuple[PersonPhone, Person, PhoneNumberType]]:
        """ Returns list of person phones assigned to a phone number type of given phone_number_type_id """
        filter_string = f"phone_number_type_ids:[{phone_number_type_id}]"

        return self.person_phone_provider.get_person_phones(filters=filter_string)

    def has_person_person_phones(self, person_id: int) -> None:
        """ Checks if person of given person_id has person phones assigned and raises error if so """
        person_phones = self.get_persons_person_phones(person_id)

        if len(person_phones) != 0:
            raise errors.ExistingDependentEntityError(f"{E400BadRequest.EXISTING_DEPENDENT_ENTITY}: "
                                                      f"Cannot delete person of id '{person_id}', because there are "
                                                      f"existing person phone entries which are dependent on that person. "
                                                      f"Dependent {len(person_phones)} person phone entries must be deleted first.")

    def has_phone_number_type_person_phones(self, phone_number_type_id: int) -> None:
        """ Checks if phone number type of given phone_number_type_id has person phones assigned and raises error if so """
        person_phones = self.get_phone_number_types_person_phones(phone_number_type_id)

        if len(person_phones) != 0:
            raise errors.ExistingDependentEntityError(f"{E400BadRequest.EXISTING_DEPENDENT_ENTITY}: "
                                                      f"Cannot delete phone number type of id '{phone_number_type_id}', because there are "
                                                      f"existing person phone entries which are dependent on that phone number type. "
                                                      f"Dependent {len(person_phones)} person phone entries must be deleted first.")
