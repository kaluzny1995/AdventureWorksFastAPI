import datetime as dt
import sqlalchemy
from pydantic import BaseModel
from sqlmodel import create_engine, Session, select
from sqlmodel.sql.expression import SelectOfScalar
from typing import Optional, List, Dict, Union, ClassVar

from app import utils, errors
from app.config import PostgresdbConnectionConfig
from app.providers import IPhoneNumberTypeProvider
from app.models import EOrderType, PhoneNumberType, PhoneNumberTypeInput, E400BadRequest, E404NotFound


class PhoneNumberTypeProvider(IPhoneNumberTypeProvider):
    connection_string: str
    db_engine: sqlalchemy.engine.Engine

    def __init__(self, connection_string: Optional[str] = None,
                 db_engine: Optional[sqlalchemy.engine.Engine] = None):
        self.connection_string = connection_string or PostgresdbConnectionConfig.get_db_connection_string()
        self.db_engine = db_engine or create_engine(self.connection_string)

    def get_phone_number_types(self, filters: Optional[str] = None,
                               order_by: Optional[str] = None, order_type: Optional[EOrderType] = None,
                               limit: Optional[int] = None, offset: Optional[int] = None) -> List[PhoneNumberType]:
        with Session(self.db_engine) as db_session:
            statement = select(PhoneNumberType)
            if filters is not None:
                phone_number_type_db_filter = PhoneNumberTypeDbFilter.from_filter_string(filters)
                statement = phone_number_type_db_filter.filter_phone_number_types(statement)
            if order_by is not None:
                phone_number_type_db_order = PhoneNumberTypeDbOrder(by=order_by, order=order_type)
                statement = phone_number_type_db_order.order_phone_number_types(statement)
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
            phone_number_types = db_session.execute(statement).all()
        phone_number_types = list(map(lambda pnt: pnt[0], phone_number_types))
        return phone_number_types

    def count_phone_number_types(self, filters: Optional[str] = None) -> int:
        with Session(self.db_engine) as db_session:
            statement = select(sqlalchemy.func.count()).select_from(PhoneNumberType)
            if filters is not None:
                phone_number_type_db_filter = PhoneNumberTypeDbFilter.from_filter_string(filters)
                statement = phone_number_type_db_filter.filter_phone_number_types(statement)
            phone_number_types_count = int(db_session.exec(statement).one())
        return phone_number_types_count

    def get_phone_number_type(self, phone_number_type_id: int) -> PhoneNumberType:
        with Session(self.db_engine) as db_session:
            statement = select(PhoneNumberType).where(PhoneNumberType.phone_number_type_id == phone_number_type_id)
            phone_number_type = db_session.execute(statement).first()
        if phone_number_type is None:
            raise errors.NotFoundError(f"{E404NotFound.PHONE_NUMBER_TYPE_NOT_FOUND}: "
                                       f"Phone number type of id '{phone_number_type_id}' does not exist.")
        return phone_number_type[0]

    def insert_phone_number_type(self, phone_number_type_input: PhoneNumberTypeInput) -> int:
        phone_number_type = PhoneNumberType(**phone_number_type_input.dict())
        with Session(self.db_engine) as db_session:
            db_session.add(phone_number_type)
            db_session.commit()
            phone_number_type_id = phone_number_type.phone_number_type_id
        return phone_number_type_id

    def update_phone_number_type(self, phone_number_type_id: int, phone_number_type_input: PhoneNumberTypeInput) -> int:
        updated_phone_number_type = self.get_phone_number_type(phone_number_type_id)
        updated_phone_number_type.update_from_input(phone_number_type_input)
        updated_phone_number_type.modified_date = dt.datetime.utcnow()
        with Session(self.db_engine) as db_session:
            db_session.add(updated_phone_number_type)
            db_session.commit()
            db_session.refresh(updated_phone_number_type)
        return updated_phone_number_type.phone_number_type_id

    def delete_phone_number_type(self, phone_number_type_id: int) -> None:
        deleted_phone_number_type = self.get_phone_number_type(phone_number_type_id)
        with Session(self.db_engine) as db_session:
            db_session.delete(deleted_phone_number_type)
            db_session.commit()


class PhoneNumberTypeDbFilter(BaseModel):
    name_phrase: Optional[str] = None

    @staticmethod
    def from_filter_string(filter_string: str) -> 'PhoneNumberTypeDbFilter':
        params = utils.get_filter_params(filter_string)

        existing_fields = list(map(lambda f: f in PhoneNumberTypeDbFilter.__fields__.keys(), params.keys()))
        if not all(existing_fields):
            raise errors.FilterNotFoundError(
                f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                f"Filter string contains fields: '{list(params.keys())}' "
                f"some of which do not exist in phone number type filtering fields: "
                f"{list(PhoneNumberTypeDbFilter.__fields__.keys())}.")

        return PhoneNumberTypeDbFilter(**params)

    def filter_phone_number_types(self, phone_number_type_statement: SelectOfScalar[PhoneNumberType]) -> SelectOfScalar[Union[PhoneNumberType, int]]:
        if self.name_phrase is not None:
            phone_number_type_statement = phone_number_type_statement.where(
                PhoneNumberType.name.ilike(f"%{self.name_phrase}%")
            )
        return phone_number_type_statement


class PhoneNumberTypeDbOrder(BaseModel):
    by: str
    order: EOrderType

    column_mapping: ClassVar[Dict[str, List[object]]] = dict({
        'phone_number_type_id': [PhoneNumberType.phone_number_type_id],
        'name': [PhoneNumberType.name],
        'modified_date': [PhoneNumberType.modified_date]
    })

    def order_phone_number_types(self, phone_number_type_statement: SelectOfScalar[PhoneNumberType]) -> SelectOfScalar[PhoneNumberType]:
        if self.by not in self.column_mapping.keys():
            raise errors.ColumnNotFoundError(f"{E400BadRequest.INVALID_ORDERING_COLUMN_NAME}: "
                                             f"Column does not exist in phone number types view ('{self.by}').")

        phone_number_type_attrs = self.column_mapping[self.by]
        order_statement = list(
            map(lambda a: a.asc() if self.order == EOrderType.ASC else a.desc(), phone_number_type_attrs))
        phone_number_type_statement = phone_number_type_statement.order_by(*order_statement)

        return phone_number_type_statement
