import datetime as dt
import sqlalchemy
from pydantic import BaseModel
from sqlmodel import create_engine, Session, select
from sqlmodel.sql.expression import SelectOfScalar
from typing import Optional, List, Dict, Union, ClassVar

from app import utils, errors
from app.config import PostgresdbConnectionConfig
from app.providers import IPersonProvider, BusinessEntityProvider
from app.models import EOrderType, Person, PersonInput, E400BadRequest, E404NotFound


class PersonProvider(IPersonProvider):
    connection_string: str
    business_entity_provider: BusinessEntityProvider
    db_engine: sqlalchemy.engine.Engine

    def __init__(self, connection_string: Optional[str] = None,
                 business_entity_provider: Optional[BusinessEntityProvider] = None,
                 db_engine: Optional[sqlalchemy.engine.Engine] = None):
        super(PersonProvider, self).__init__()
        self.connection_string = connection_string or PostgresdbConnectionConfig.get_db_connection_string()
        self.business_entity_provider = business_entity_provider or BusinessEntityProvider()
        self.db_engine = db_engine or create_engine(self.connection_string)

    def get_persons(self, filters: Optional[str] = None,
                    order_by: Optional[str] = None, order_type: Optional[EOrderType] = None,
                    limit: Optional[int] = None, offset: Optional[int] = None) -> List[Person]:
        with Session(self.db_engine) as db_session:
            statement = select(Person)
            if filters is not None:
                person_db_filter = PersonDbFilter.from_filter_string(filters)
                statement = person_db_filter.filter_persons(statement)
            if order_by is not None:
                person_db_order = PersonDbOrder(by=order_by, order=order_type)
                statement = person_db_order.order_persons(statement)
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
            persons = db_session.execute(statement).all()
        persons = list(map(lambda p: p[0], persons))
        return persons

    def count_persons(self, filters: Optional[str] = None) -> int:
        with Session(self.db_engine) as db_session:
            statement = select(sqlalchemy.func.count()).select_from(Person)
            if filters is not None:
                person_db_filter = PersonDbFilter.from_filter_string(filters)
                statement = person_db_filter.filter_persons(statement)
            persons_count = int(db_session.exec(statement).one())
        return persons_count

    def get_person(self, person_id: int) -> Person:
        with Session(self.db_engine) as db_session:
            statement = select(Person).where(Person.business_entity_id == person_id)
            person = db_session.execute(statement).first()
        if person is None:
            raise errors.NotFoundError(f"{E404NotFound.PERSON_NOT_FOUND}: "
                                       f"Person of id '{person_id}' does not exist.")
        return person[0]

    def insert_person(self, person_input: PersonInput) -> int:
        business_entity_id = self.business_entity_provider.insert_business_entity()
        person = Person(business_entity_id=business_entity_id, **person_input.dict())
        person.validate_assignment(person_input)
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


class PersonDbFilter(BaseModel):
    person_type: Optional[str] = None
    first_name_phrase: Optional[str] = None
    last_name_phrase: Optional[str] = None

    @staticmethod
    def from_filter_string(filter_string: str) -> 'PersonDbFilter':
        params = utils.get_filter_params(filter_string)

        existing_fields = list(map(lambda f: f in PersonDbFilter.__fields__.keys(), params.keys()))
        if not all(existing_fields):
            raise errors.FilterNotFoundError(
                f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                f"Filter string contains fields: '{list(params.keys())}' "
                f"some of which do not exist in person filtering fields: {list(PersonDbFilter.__fields__.keys())}.")

        return PersonDbFilter(**params)

    def filter_persons(self, person_statement: SelectOfScalar[Person]) -> SelectOfScalar[Union[Person, int]]:
        if self.person_type is not None:
            person_statement = person_statement.where(Person.person_type == self.person_type)
        if self.first_name_phrase is not None:
            person_statement = person_statement.where(sqlalchemy.or_(
                Person.first_name.ilike(f"%{self.first_name_phrase}%"),
                Person.middle_name.ilike(f"%{self.first_name_phrase}%"))
            )
        if self.last_name_phrase is not None:
            person_statement = person_statement.where(Person.last_name.ilike(f"%{self.last_name_phrase}%"))
        return person_statement


class PersonDbOrder(BaseModel):
    by: str
    order: EOrderType

    column_mapping: ClassVar[Dict[str, List[object]]] = dict({
        'person_id': [Person.business_entity_id],
        'person_type': [Person.person_type],
        'name_style': [Person.name_style],
        'full_name': [Person.last_name, Person.first_name, Person.middle_name, Person.suffix, Person.title],
        'email_promotion': [Person.email_promotion],
        # 'additional_contact_info' cannot be ordered as there is no ordering operator for xml data type
        # 'demographics' cannot be ordered as there is no ordering operator for xml data type
        'rowguid': [Person.rowguid],
        'modified_date': [Person.modified_date]
    })

    def order_persons(self, person_statement: SelectOfScalar[Person]) -> SelectOfScalar[Person]:
        if self.by in ["additional_contact_info", "demographics"]:
            raise errors.ColumnNotFoundError(f"{E400BadRequest.ORDERING_NOT_SUPPORTED_FOR_COLUMN}: "
                                             f"Cannot order by column '{self.by}'. "
                                             f"PostgreSQL does not support ordering for 'xml' data type.")
        elif self.by not in self.column_mapping.keys():
            raise errors.ColumnNotFoundError(f"{E400BadRequest.INVALID_ORDERING_COLUMN_NAME}: "
                                             f"Column does not exist in persons view ('{self.by}').")

        person_attrs = self.column_mapping[self.by]
        order_statement = list(map(lambda a: a.asc() if self.order == EOrderType.ASC else a.desc(), person_attrs))
        person_statement = person_statement.order_by(*order_statement)

        return person_statement
