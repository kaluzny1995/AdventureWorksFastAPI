import datetime as dt
import sqlalchemy
from pydantic import BaseModel
from sqlmodel import create_engine, Session, select, text
from sqlmodel.sql.expression import SelectOfScalar
from typing import Optional, List, Tuple, Dict, Union, ClassVar

from app import utils, errors
from app.config import PostgresdbConnectionConfig
from app.providers import IPersonPhoneProvider
from app.models import (EConstraintViolation, EOrderType, Person, PhoneNumberType, PersonPhone, PersonPhoneInput,
                        E400BadRequest, E404NotFound)


class PersonPhoneProvider(IPersonPhoneProvider):
    connection_string: str
    db_engine: sqlalchemy.engine.Engine

    def __init__(self, connection_string: Optional[str] = None,
                 db_engine: Optional[sqlalchemy.engine.Engine] = None):
        self.connection_string = connection_string or PostgresdbConnectionConfig.get_db_connection_string()
        self.db_engine = db_engine or create_engine(self.connection_string)

    def get_person_phones(self, filters: Optional[str] = None,
                          order_by: Optional[str] = None, order_type: Optional[EOrderType] = None,
                          limit: Optional[int] = None, offset: Optional[int] = None
                          ) -> List[Tuple[PersonPhone, Person, PhoneNumberType]]:
        with Session(self.db_engine) as db_session:
            statement = select(PersonPhone, Person, PhoneNumberType).select_from(PersonPhone)
            if filters is not None:
                person_phone_db_filter = PersonPhoneDbFilter.from_filter_string(filters)
                statement = person_phone_db_filter.filter_person_phones(statement)
            if order_by is not None:
                person_phone_db_order = PersonPhoneDbOrder(by=order_by, order=order_type)
                statement = person_phone_db_order.order_person_phones(statement)
            if offset is not None:
                if offset < 0:
                    raise errors.InvalidSQLValueError(f"{E400BadRequest.INVALID_SQL_VALUE}: "
                                                      f"Value '{offset}' is invalid for SKIP clause.")
                statement = statement.offset(offset)
            if limit is not None:
                if limit < 0:
                    raise errors.InvalidSQLValueError(f"{E400BadRequest.INVALID_SQL_VALUE}: "
                                                      f"Value '{limit}' is invalid for LIMIT clause.")
                statement = statement.limit(limit)

            statement = statement\
                .join(Person, onclause=text("\"Person\".\"PersonPhone\".\"BusinessEntityID\"=\"Person\".\"Person\".\"BusinessEntityID\""))\
                .join(PhoneNumberType, onclause=text("\"Person\".\"PersonPhone\".\"PhoneNumberTypeID\"=\"Person\".\"PhoneNumberType\".\"PhoneNumberTypeID\""))
            person_phones = db_session.execute(statement).all()
        person_phones = list(map(lambda p: (p[0], p[1], p[2]), person_phones))
        return person_phones

    def count_person_phones(self, filters: Optional[str] = None) -> int:
        with Session(self.db_engine) as db_session:
            statement = select(sqlalchemy.func.count()).select_from(PersonPhone)
            if filters is not None:
                person_phone_db_filter = PersonPhoneDbFilter.from_filter_string(filters)
                statement = person_phone_db_filter.filter_person_phones(statement)
            persons_count = int(db_session.exec(statement).one())
        return persons_count

    def get_person_phone(self, person_phone_id: Tuple[int, str, int]) -> Tuple[PersonPhone, Person, PhoneNumberType]:
        with (Session(self.db_engine) as db_session):
            statement = select(PersonPhone, Person, PhoneNumberType).select_from(PersonPhone)\
                .where(sqlalchemy.and_(PersonPhone.business_entity_id == person_phone_id[0],
                                       PersonPhone.phone_number == person_phone_id[1],
                                       PersonPhone.phone_number_type_id == person_phone_id[2]))

            statement = statement\
                .join(Person, onclause=text("\"Person\".\"PersonPhone\".\"BusinessEntityID\"=\"Person\".\"Person\".\"BusinessEntityID\""))\
                .join(PhoneNumberType, onclause=text("\"Person\".\"PersonPhone\".\"PhoneNumberTypeID\"=\"Person\".\"PhoneNumberType\".\"PhoneNumberTypeID\""))
            person_phone = db_session.execute(statement).first()
        if person_phone is None:
            raise errors.NotFoundError(f"{E404NotFound.PERSON_PHONE_NOT_FOUND}: "
                                       f"Person phone of id '{person_phone_id}' does not exist.")
        return tuple((person_phone[0], person_phone[1], person_phone[2]))

    def insert_person_phone(self, person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        person_phone = PersonPhone(**person_phone_input.dict())
        try:
            with Session(self.db_engine) as db_session:
                db_session.add(person_phone)
                db_session.commit()
                person_phone_id = tuple((person_phone.business_entity_id, person_phone.phone_number,
                                         person_phone.phone_number_type_id))
            return person_phone_id
        except sqlalchemy.exc.IntegrityError as e:
            if EConstraintViolation.UNIQUE_VIOLATION in str(e):
                raise errors.IntegrityError(f"{E400BadRequest.PRIMARY_KEY_CONSTRAINT_VIOLATION}: {str(e)}")
            elif EConstraintViolation.FOREIGN_KEY_VIOLATION in str(e):
                raise errors.IntegrityError(f"{E400BadRequest.FOREIGN_KEY_CONSTRAINT_VIOLATION}: {str(e)}")

    def update_person_phone(self, person_phone_id: Tuple[int, str, int],
                            person_phone_input: PersonPhoneInput) -> Tuple[int, str, int]:
        updated_person_phone = self.get_person_phone(person_phone_id)[0]
        updated_person_phone.update_from_input(person_phone_input)
        updated_person_phone.modified_date = dt.datetime.utcnow()
        try:
            with Session(self.db_engine) as db_session:
                db_session.add(updated_person_phone)
                db_session.commit()
                db_session.refresh(updated_person_phone)
                person_phone_id = tuple((updated_person_phone.business_entity_id, updated_person_phone.phone_number,
                                         updated_person_phone.phone_number_type_id))
            return person_phone_id
        except sqlalchemy.exc.IntegrityError as e:
            if EConstraintViolation.UNIQUE_VIOLATION in str(e):
                raise errors.IntegrityError(f"{E400BadRequest.PRIMARY_KEY_CONSTRAINT_VIOLATION}: {str(e)}")
            elif EConstraintViolation.FOREIGN_KEY_VIOLATION in str(e):
                raise errors.IntegrityError(f"{E400BadRequest.FOREIGN_KEY_CONSTRAINT_VIOLATION}: {str(e)}")

    def delete_person_phone(self, person_phone_id: Tuple[int, str, int]) -> None:
        deleted_person_phone = self.get_person_phone(person_phone_id)[0]
        with Session(self.db_engine) as db_session:
            db_session.delete(deleted_person_phone)
            db_session.commit()


class PersonPhoneDbFilter(BaseModel):
    person_ids: Optional[List[int]] = None
    phone_number_type_ids: Optional[List[int]] = None

    @staticmethod
    def from_filter_string(filter_string: str) -> 'PersonPhoneDbFilter':
        params = utils.adjust_filter_params(utils.get_filter_params(filter_string))

        existing_fields = list(map(lambda f: f in PersonPhoneDbFilter.__fields__.keys(), params.keys()))
        if not all(existing_fields):
            raise errors.FilterNotFoundError(
                f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                f"Filter string contains fields: '{list(params.keys())}' "
                f"some of which do not exist in person filtering fields: {list(PersonPhoneDbFilter.__fields__.keys())}.")

        return PersonPhoneDbFilter(**params)

    def filter_person_phones(self, person_phone_statement: SelectOfScalar[Tuple[PersonPhone, Person, PhoneNumberType]]) -> SelectOfScalar[Union[Tuple[PersonPhone, Person, PhoneNumberType], int]]:
        if self.person_ids is not None:
            person_phone_statement = person_phone_statement.where(PersonPhone.business_entity_id.in_(self.person_ids))
        if self.phone_number_type_ids is not None:
            person_phone_statement = person_phone_statement.where(PersonPhone.phone_number_type_id.in_(self.phone_number_type_ids))
        return person_phone_statement


class PersonPhoneDbOrder(BaseModel):
    by: str
    order: EOrderType

    column_mapping: ClassVar[Dict[str, List[object]]] = dict({
        'person_full_name': [Person.last_name, Person.first_name, Person.middle_name,
                             Person.suffix, Person.title, Person.business_entity_id,
                             PhoneNumberType.name, PersonPhone.phone_number],
        'phone_number': [PersonPhone.phone_number, PersonPhone.business_entity_id, PersonPhone.phone_number_type_id],
        'phone_number_type_name': [PhoneNumberType.name, PersonPhone.business_entity_id, PersonPhone.phone_number],
        'modified_date': [Person.modified_date]
    })

    def order_person_phones(self, person_phone_statement: SelectOfScalar[Tuple[PersonPhone, Person, PhoneNumberType]]) -> SelectOfScalar[Tuple[PersonPhone, Person, PhoneNumberType]]:
        if self.by not in self.column_mapping.keys():
            raise errors.ColumnNotFoundError(f"{E400BadRequest.INVALID_ORDERING_COLUMN_NAME}: "
                                             f"Column does not exist in person phones view ('{self.by}').")

        person_phone_attrs = self.column_mapping[self.by]
        order_statement = list(map(lambda a: a.asc() if self.order == EOrderType.ASC else a.desc(), person_phone_attrs))
        person_phone_statement = person_phone_statement.order_by(*order_statement)

        return person_phone_statement
