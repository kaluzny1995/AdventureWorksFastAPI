from typing import Optional, List, Tuple

from app.models import EOrderType, PersonPhoneInput, Person, PhoneNumberType, PersonPhone
from app.providers import IPersonPhoneProvider


class PersonPhoneProviderStub(IPersonPhoneProvider):

    def __init__(self, data: List[PersonPhone]):
        super(PersonPhoneProviderStub, self).__init__()
        self.data = data

    def get_person_phones(self, filters: Optional[str] = None,
                    order_by: Optional[str] = None, order_type: Optional[EOrderType] = None,
                    limit: Optional[int] = None, offset: Optional[int] = None) -> List[Tuple[PersonPhone, None, None]]:
        """ Returns list of appropriate person phones """
        return list(map(lambda d: tuple((d, None, None)), self.data))

    def count_person_phones(self, filters: Optional[str] = None) -> int:
        """ Returns count of appropriate person phones """
        return len(self.data)

    def get_person_phone(self, person_phone_id: Tuple[int, str, int]) -> Tuple[PersonPhone, Person, PhoneNumberType]:
        """ Returns person phone of given person_phone_id """
        pass

    def insert_person(self, person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        """ Inserts person phone and returns new person phone person_phone_id """
        pass

    def update_person(self, person_phone_id: Tuple[int, str, int],
                            person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        """ Updates person phone of given person_phone_id and return updated person phone person_phone_id """
        pass

    def delete_person(self, person_phone_id: Tuple[int, str, int]) -> None:
        """ Deletes person phone of given person_phone_id """
        pass
