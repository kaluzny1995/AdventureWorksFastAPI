import datetime as dt
from sqlmodel import create_engine, Session, select
from typing import Optional, List

from app import errors
from app.config import PostgresdbConnectionConfig
from app.models import PhoneNumberType, PhoneNumberTypeInput


class PhoneNumberTypeProvider:
    connection_string: str = PostgresdbConnectionConfig.get_db_connection_string()
    db_engine = create_engine(connection_string)

    def get_phone_number_types(self, limit: Optional[int], offset: Optional[int]) -> List[PhoneNumberType]:
        with Session(self.db_engine) as db_session:
            statement = select(PhoneNumberType)
            if offset is not None:
                statement = statement.offset(offset)
            if limit is not None:
                statement = statement.limit(limit)
            persons = db_session.execute(statement).all()
        persons = list(map(lambda p: p[0], persons))
        return persons

    def get_phone_number_type(self, phone_number_type_id: int) -> PhoneNumberType:
        with Session(self.db_engine) as db_session:
            statement = select(PhoneNumberType).where(PhoneNumberType.phone_number_type_id == phone_number_type_id)
            phone_number_type = db_session.execute(statement).first()
        if phone_number_type is None:
            raise errors.NotFoundError(f"Phone number type of id '{phone_number_type_id}' does not exist")
        return phone_number_type[0]

    def insert_phone_number_type(self, phone_number_type_input: PhoneNumberTypeInput) -> int:
        phone_number_type = PhoneNumberType(**phone_number_type_input.dict())
        with Session(self.db_engine) as db_session:
            db_session.add(phone_number_type)
            db_session.commit()
            phone_number_type_id = phone_number_type.phone_number_type_id
        return phone_number_type_id

    def update_phone_number_type(self, phone_number_type_id: int, phone_number_type_input: PhoneNumberTypeInput) -> int:
        updated_phone_number_type_id = self.get_phone_number_type(phone_number_type_id)
        updated_phone_number_type_id.update_from_input(phone_number_type_input)
        updated_phone_number_type_id.modified_date = dt.datetime.utcnow()
        with Session(self.db_engine) as db_session:
            db_session.add(updated_phone_number_type_id)
            db_session.commit()
            db_session.refresh(updated_phone_number_type_id)
        return updated_phone_number_type_id.phone_number_type_id

    def delete_phone_number_type(self, phone_number_type_id: int) -> None:
        deleted_phone_number_type = self.get_phone_number_type(phone_number_type_id)
        with Session(self.db_engine) as db_session:
            db_session.delete(deleted_phone_number_type)
            db_session.commit()
