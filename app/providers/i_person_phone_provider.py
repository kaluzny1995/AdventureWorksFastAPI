from typing import Optional, List, Tuple

from app.models import EOrderType, Person, PhoneNumberType, PersonPhone, PersonPhoneInput


class IPersonPhoneProvider:
    """ Interface of person phone provider """

    def get_person_phones(self, filters: Optional[str] = None,
                          order_by: Optional[str] = None, order_type: Optional[EOrderType] = None,
                          limit: Optional[int] = None, offset: Optional[int] = None
                          ) -> List[Tuple[PersonPhone, Person, PhoneNumberType]]:
        """ Returns list of appropriate person phones with its person and phone number type """
        raise NotImplementedError

    def count_person_phones(self, filters: Optional[str] = None) -> int:
        """ Returns count of appropriate person phones """
        raise NotImplementedError

    def get_person_phone(self, person_phone_id: Tuple[int, str, int]) -> Tuple[PersonPhone, Person, PhoneNumberType]:
        """ Returns person phone of given person_phone_id """
        raise NotImplementedError

    def insert_person_phone(self, person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        """ Inserts person phone and returns new person phone person_phone_id """
        raise NotImplementedError

    def update_person_phone(self, person_phone_id: Tuple[int, str, int],
                            person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        """ Updates person phone of given person_phone_id and returns updated person phone person_phone_id """
        raise NotImplementedError

    def delete_person_phone(self, person_phone_id: Tuple[int, str, int]) -> None:
        """ Deletes person phone of given person_phone_id """
        raise NotImplementedError
