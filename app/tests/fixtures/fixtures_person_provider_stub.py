from typing import Optional, List

from app.models import PersonInput, Person
from app.providers import IPersonProvider


class PersonProviderStub(IPersonProvider):

    def __init__(self, data: List[Person]):
        super(PersonProviderStub, self).__init__()
        self.data = data

    def get_persons(self, limit: Optional[int] = None, offset: Optional[int] = None):
        """ Returns list of all persons """
        return self.data

    def get_person(self, person_id: int):
        """ Returns person of given person_id """
        pass

    def insert_person(self, person_input: PersonInput):
        """ Inserts person and returns new person person_id """
        pass

    def update_person(self, person_id: int, person_input: PersonInput):
        """ Updates person of given person_id and return updated person person_id """
        pass

    def delete_person(self, person_id: int):
        """ Deletes person of given person_id """
        pass
