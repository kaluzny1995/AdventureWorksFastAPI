import sqlalchemy
from typing import Tuple
from pydantic import BaseModel

from app.providers import PersonPhoneProvider
from app.services import PersonPhoneService


class PersonPhoneFactory(BaseModel):

    @staticmethod
    def get_provider(connection_string: str, db_engine: sqlalchemy.engine.Engine) -> PersonPhoneProvider:
        return PersonPhoneProvider(
            connection_string=connection_string,
            db_engine=db_engine
        )

    @staticmethod
    def get_service(provider: PersonPhoneProvider) -> PersonPhoneService:
        return PersonPhoneService(person_phone_provider=provider)

    @staticmethod
    def get_provider_and_service(connection_string: str, db_engine: sqlalchemy.engine.Engine
                                 ) -> Tuple[PersonPhoneProvider, PersonPhoneService]:
        provider = PersonPhoneFactory.get_provider(connection_string, db_engine)
        service = PersonPhoneFactory.get_service(provider)
        return provider, service
