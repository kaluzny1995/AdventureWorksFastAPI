from typing import Optional, List

from app.models import PersonInput, Person


class IPersonProvider:
    """ Interface of person provider """

    def get_persons(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Person]:
        """ Returns list of all persons """
        raise NotImplementedError

    def get_person(self, person_id: int) -> Person:
        """ Returns person of given person_id """
        raise NotImplementedError

    def insert_person(self, person_input: PersonInput) -> int:
        """ Inserts person and returns new person person_id """
        raise NotImplementedError

    def update_person(self, person_id: int, person_input: PersonInput) -> int:
        """ Updates person of given person_id and return updated person person_id """
        raise NotImplementedError

    def delete_person(self, person_id: int) -> None:
        """ Deletes person of given person_id """
        raise NotImplementedError
