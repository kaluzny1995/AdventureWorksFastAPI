import sqlalchemy
from pydantic import BaseModel

from app.providers import PhoneNumberTypeProvider


class PhoneNumberTypeFactory(BaseModel):

    @staticmethod
    def get_provider(connection_string: str, db_engine: sqlalchemy.engine.Engine) -> PhoneNumberTypeProvider:
        return PhoneNumberTypeProvider(
            connection_string=connection_string,
            db_engine=db_engine
        )
