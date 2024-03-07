import sqlalchemy
from sqlmodel import create_engine, Session, select
from typing import Optional, List

from app import errors
from app.config import PostgresdbConnectionConfig
from app.models import BusinessEntity, E404NotFound
from app.providers import IBusinessEntityProvider


class BusinessEntityProvider(IBusinessEntityProvider):
    connection_string: str
    db_engine: sqlalchemy.engine.Engine

    def __init__(self, connection_string: Optional[str] = None,
                 db_engine: Optional[sqlalchemy.engine.Engine] = None):
        self.connection_string = connection_string or PostgresdbConnectionConfig.get_db_connection_string()
        self.db_engine = db_engine or create_engine(self.connection_string)

    def get_business_entities(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[BusinessEntity]:
        with Session(self.db_engine) as db_session:
            statement = select(BusinessEntity)
            if offset is not None:
                statement = statement.offset(offset)
            if limit is not None:
                statement = statement.limit(limit)
            business_entities = db_session.execute(statement).all()
        business_entities = list(map(lambda p: p[0], business_entities))
        return business_entities

    def get_business_entity(self, business_entity_id: int) -> BusinessEntity:
        with Session(self.db_engine) as db_session:
            statement = select(BusinessEntity).where(BusinessEntity.business_entity_id == business_entity_id)
            business_entity = db_session.execute(statement).first()
        if business_entity is None:
            raise errors.NotFoundError(f"{E404NotFound.BUSINESS_ENTITY_NOT_FOUND}: "
                                       f"Business entity of id '{business_entity_id}' does not exist.")
        return business_entity[0]

    def insert_business_entity(self) -> int:
        business_entity = BusinessEntity()
        with Session(self.db_engine) as db_session:
            db_session.add(business_entity)
            db_session.commit()
            business_entity_id = business_entity.business_entity_id
        return business_entity_id

    # no update method for BusinessEntity, no mutable fields

    def delete_business_entity(self, business_entity_id: int) -> None:
        deleted_business_entity = self.get_business_entity(business_entity_id)
        with Session(self.db_engine) as db_session:
            db_session.delete(deleted_business_entity)
            db_session.commit()
