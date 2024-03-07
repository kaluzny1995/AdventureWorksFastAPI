from typing import Optional, List

from app import errors
from app.providers import IPersonProvider, PersonProvider
from app.models import EOrderType, Person, E400BadRequest, E404NotFound


class PersonService:
    person_provider: IPersonProvider

    def __init__(self, person_provider: Optional[IPersonProvider] = None):
        self.person_provider = person_provider or PersonProvider()

    def get_persons_by_phrases(self,
                               first_name_phrase: Optional[str] = None,
                               last_name_phrase: Optional[str] = None,
                               is_ordered: Optional[bool] = True) -> List[Person]:

        if first_name_phrase is not None and last_name_phrase is not None:
            filter_string = f"first_name_phrase:{first_name_phrase},last_name_phrase:{last_name_phrase}"
        elif first_name_phrase is not None:
            filter_string = f"first_name_phrase:{first_name_phrase}"
        elif last_name_phrase is not None:
            filter_string = f"last_name_phrase:{last_name_phrase}"
        else:
            raise errors.EmptyFieldsError(f"{E400BadRequest.VALUES_NOT_PROVIDED}: "
                                          f"Either first or last name phrase must be provided.")

        found_persons = self.person_provider.get_persons(filters=filter_string,
                                                         order_by="full_name" if is_ordered else None,
                                                         order_type=EOrderType.ASC)

        if len(found_persons) == 0:
            raise errors.NotFoundError(f"{E404NotFound.PERSON_NOT_FOUND}: Persons of given phrases not found.")

        return found_persons
