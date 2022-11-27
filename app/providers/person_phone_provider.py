import datetime as dt
from sqlmodel import create_engine, Session, select
from sqlalchemy import and_
import sqlalchemy.exc
from typing import Optional, List, Tuple

from app import errors
from app.config import PostgresdbConnectionConfig
from app.models import PersonPhone, PersonPhoneInput


class PersonPhoneProvider:
    connection_string: str = PostgresdbConnectionConfig.get_db_connection_string()
    db_engine = create_engine(connection_string)

    def get_person_phones(self, limit: Optional[int], offset: Optional[int]) -> List[PersonPhone]:
        with Session(self.db_engine) as db_session:
            statement = select(PersonPhone)
            if offset is not None:
                statement = statement.offset(offset)
            if limit is not None:
                statement = statement.limit(limit)
            person_phones = db_session.execute(statement).all()
        person_phones = list(map(lambda p: p[0], person_phones))
        return person_phones

    def get_person_phone(self, person_phone_id: Tuple[int, str, int]) -> PersonPhone:
        with Session(self.db_engine) as db_session:
            statement = select(PersonPhone). \
                where(and_(PersonPhone.business_entity_id == person_phone_id[0],
                           PersonPhone.phone_number == person_phone_id[1],
                           PersonPhone.phone_number_type_id == person_phone_id[2]))
            print(statement)
            person_phone = db_session.execute(statement).first()
        if person_phone is None:
            raise errors.NotFoundError(f"Person phone of id '{person_phone_id}' does not exist")
        return person_phone[0]

    def insert_person_phone(self, person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        person_phone = PersonPhone(**person_phone_input.dict())
        try:
            with Session(self.db_engine) as db_session:
                db_session.add(person_phone)
                db_session.commit()
                person_phone_id = (person_phone.business_entity_id, person_phone.phone_number,
                                   person_phone.phone_number_type_id)
            return person_phone_id
        except sqlalchemy.exc.IntegrityError as e:
            raise errors.IntegrityError(str(e))

    def update_person_phone(self, person_phone_id: Tuple[int, str, int],
                            person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        updated_person_phone = self.get_person_phone(person_phone_id)
        updated_person_phone.update_from_input(person_phone_input)
        updated_person_phone.modified_date = dt.datetime.utcnow()
        try:
            with Session(self.db_engine) as db_session:
                db_session.add(updated_person_phone)
                db_session.commit()
                db_session.refresh(updated_person_phone)
                person_phone_id = (updated_person_phone.business_entity_id, updated_person_phone.phone_number,
                                   updated_person_phone.phone_number_type_id)
            return person_phone_id
        except sqlalchemy.exc.IntegrityError as e:
            raise errors.IntegrityError(str(e))

    def delete_person_phone(self, person_phone_id: Tuple[int, str, int]) -> None:
        deleted_person_phone = self.get_person_phone(person_phone_id)
        with Session(self.db_engine) as db_session:
            db_session.delete(deleted_person_phone)
            db_session.commit()
