import sqlalchemy
from sqlmodel import create_engine
from typing import Tuple
from pydantic import BaseModel

from app.config import PostgresdbConnectionConfig


class PostgresDBFactory(BaseModel):

    @staticmethod
    def get_db_connection_details(test_suffix: str = "") -> Tuple[str, sqlalchemy.engine.Engine]:
        connection_string = PostgresdbConnectionConfig.get_db_connection_string(test_suffix)
        db_engine = create_engine(connection_string)

        return connection_string, db_engine
