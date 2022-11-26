import datetime as dt
from sqlmodel import create_engine, Session, select
from typing import Optional, List

from app import errors
from app.config import PostgresdbConnectionConfig
from app.providers import BusinessEntityProvider
from app.models import Person, PersonInput


class PersonProvider:
    connection_string: str = PostgresdbConnectionConfig.get_db_connection_string()
    business_entity_provider: BusinessEntityProvider = BusinessEntityProvider()
    db_engine = create_engine(connection_string)

    def get_persons(self, limit: Optional[int], offset: Optional[int]) -> List[Person]:
        with Session(self.db_engine) as db_session:
            statement = select(Person)
            if offset is not None:
                statement = statement.offset(offset)
            if limit is not None:
                statement = statement.limit(limit)
            persons = db_session.execute(statement).all()
        persons = list(map(lambda p: p[0], persons))
        return persons

    def get_person(self, person_id: int) -> Person:
        with Session(self.db_engine) as db_session:
            statement = select(Person).where(Person.business_entity_id == person_id)
            person = db_session.execute(statement).first()
        if person is None:
            raise errors.NotFoundError(f"Person of id '{person_id}' does not exist")
        return person[0]

    def insert_person(self, person_input: PersonInput) -> int:
        business_entity_id = self.business_entity_provider.insert_business_entity()
        person = Person(business_entity_id=business_entity_id, **person_input.dict())
        with Session(self.db_engine) as db_session:
            db_session.add(person)
            db_session.commit()
            person_id = person.business_entity_id
        return person_id

    def update_person(self, person_id: int, person_input: PersonInput) -> int:
        updated_person = self.get_person(person_id)
        updated_person.update_from_input(person_input)
        updated_person.modified_date = dt.datetime.utcnow()
        with Session(self.db_engine) as db_session:
            db_session.add(updated_person)
            db_session.commit()
            db_session.refresh(updated_person)
        return updated_person.business_entity_id

    def delete_person(self, person_id: int) -> None:
        deleted_person = self.get_person(person_id)
        business_entity_id = deleted_person.business_entity_id
        with Session(self.db_engine) as db_session:
            db_session.delete(deleted_person)
            db_session.commit()
        self.business_entity_provider.delete_business_entity(business_entity_id)
