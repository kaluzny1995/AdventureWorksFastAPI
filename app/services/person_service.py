from typing import Optional

from app import errors
from app.providers import PersonProvider


class PersonService:
    person_provider: PersonProvider = PersonProvider()

    def get_persons_by_phrases(self, first_name_phrase: Optional[str], last_name_phrase: Optional[str]):
        if first_name_phrase is None and last_name_phrase is None:
            raise errors.EmptyFieldsError()

        all_persons = self.person_provider.get_persons()

        if first_name_phrase is not None and last_name_phrase is not None:
            relevant_persons = list(filter(
                lambda p: first_name_phrase.lower() in p.first_name.lower() and
                last_name_phrase.lower() in p.last_name.lower(), all_persons))
        elif first_name_phrase is not None:
            relevant_persons = list(filter(lambda p: first_name_phrase.lower() in p.first_name.lower(), all_persons))
        else:
            relevant_persons = list(filter(lambda p: last_name_phrase.lower() in p.last_name.lower(), all_persons))

        relevant_persons = list(sorted(relevant_persons,
                                       key=lambda rp: (rp.last_name, rp.first_name, rp.middle_name or "")))

        return relevant_persons