import pymongo
from typing import Tuple
from pydantic import BaseModel

from app.providers import AWFAPIUserProvider
from app.services import AWFAPIUserService


class AWFAPIUserFactory(BaseModel):

    @staticmethod
    def get_provider(connection_string: str, collection_name: str,
                     db_engine: pymongo.MongoClient) -> AWFAPIUserProvider:
        return AWFAPIUserProvider(
            connection_string=connection_string,
            collection_name=collection_name,
            db_engine=db_engine
        )

    @staticmethod
    def get_service(provider: AWFAPIUserProvider) -> AWFAPIUserService:
        return AWFAPIUserService(awfapi_user_provider=provider)

    @staticmethod
    def get_provider_and_service(connection_string: str, collection_name: str,
                                 db_engine: pymongo.MongoClient) -> Tuple[AWFAPIUserProvider, AWFAPIUserService]:
        provider = AWFAPIUserFactory.get_provider(connection_string, collection_name, db_engine)
        service = AWFAPIUserFactory.get_service(provider)
        return provider, service
