from typing import Optional, List

from app.models import EOrderType, PersonInput, Person
from app.providers import IPersonProvider


class PersonProviderStub(IPersonProvider):

    def __init__(self, data: List[Person]):
        super(PersonProviderStub, self).__init__()
        self.data = data

    def get_persons(self, filters: Optional[str] = None,
                    order_by: Optional[str] = None, order_type: Optional[EOrderType] = None,
                    limit: Optional[int] = None, offset: Optional[int] = None,
                    is_alternative: Optional[bool] = False) -> List[Person]:
        """ Returns list of appropriate persons """
        return self.data

    def count_persons(self, filters: Optional[str] = None) -> int:
        """ Returns count of appropriate persons """
        return len(self.data)

    def get_person(self, person_id: int) -> Person:
        """ Returns person of given person_id """
        pass

    def insert_person(self, person_input: PersonInput) -> int:
        """ Inserts person and returns new person person_id """
        pass

    def update_person(self, person_id: int, person_input: PersonInput) -> int:
        """ Updates person of given person_id and return updated person person_id """
        pass

    def delete_person(self, person_id: int) -> None:
        """ Deletes person of given person_id """
        pass
