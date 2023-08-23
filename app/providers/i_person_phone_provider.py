from typing import Optional, List, Tuple

from app.models import PersonPhone, PersonPhoneInput


class IPersonPhoneProvider:
    """ Interface of person phone provider """

    def get_person_phones(self, limit: Optional[int], offset: Optional[int]) -> List[PersonPhone]:
        """ Returns list of all person phones """
        raise NotImplementedError

    def get_person_phone(self, person_phone_id: Tuple[int, str, int]) -> PersonPhone:
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
