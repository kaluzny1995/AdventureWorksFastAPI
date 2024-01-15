from typing import Optional, List

from app import errors
from app.providers import IPersonProvider, PersonProvider
from app.models import Person


class PersonService:
    person_provider: IPersonProvider

    def __init__(self, person_provider: Optional[IPersonProvider] = None):
        self.person_provider = person_provider or PersonProvider()

    def get_persons_by_phrases(self,
                               first_name_phrase: Optional[str] = None,
                               last_name_phrase: Optional[str] = None,
                               is_sorted: Optional[bool] = True) -> List[Person]:

        if first_name_phrase is not None and last_name_phrase is not None:
            found_persons = self.person_provider.get_persons(
                filters=f"first_name_phrase:{first_name_phrase},last_name_phrase:{last_name_phrase}")
        elif first_name_phrase is not None:
            found_persons = self.person_provider.get_persons(filters=f"first_name_phrase:{first_name_phrase}")
        elif last_name_phrase is not None:
            found_persons = self.person_provider.get_persons(filters=f"last_name_phrase:{last_name_phrase}")
        else:
            raise errors.EmptyFieldsError("Either first or last name phrase must be provided.")

        if len(found_persons) == 0:
            raise errors.NotFoundError("Persons of given phrases not found.")

        if is_sorted:
            found_persons = list(sorted(found_persons,
                                        key=lambda rp: (rp.last_name, rp.first_name, rp.middle_name or "")))

        return found_persons
