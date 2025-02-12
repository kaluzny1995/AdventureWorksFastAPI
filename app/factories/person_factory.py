import sqlalchemy
from typing import Tuple
from pydantic import BaseModel

from app.providers import BusinessEntityProvider, PersonProvider
from app.services import PersonService


class PersonFactory(BaseModel):

    @staticmethod
    def get_provider(connection_string: str, db_engine: sqlalchemy.engine.Engine) -> PersonProvider:
        return PersonProvider(
            connection_string=connection_string,
            business_entity_provider=BusinessEntityProvider(
                connection_string=connection_string,
                db_engine=db_engine
            ),
            db_engine=db_engine
        )

    @staticmethod
    def get_service(provider: PersonProvider) -> PersonService:
        return PersonService(person_provider=provider)

    @staticmethod
    def get_provider_and_service(connection_string: str, db_engine: sqlalchemy.engine.Engine
                                 ) -> Tuple[PersonProvider, PersonService]:
        provider = PersonFactory.get_provider(connection_string, db_engine)
        service = PersonFactory.get_service(provider)
        return provider, service
