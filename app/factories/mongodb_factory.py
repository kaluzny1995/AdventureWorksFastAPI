import pymongo
from typing import Tuple
from pydantic import BaseModel

from app.config import MongodbConnectionConfig


class MongoDBFactory(BaseModel):

    @staticmethod
    def get_db_connection_details(test_suffix: str = "") -> Tuple[str, str, pymongo.MongoClient]:
        connection_string = MongodbConnectionConfig.get_db_connection_string()
        collection_name = MongodbConnectionConfig.get_collection_name(test_suffix)
        db_engine = pymongo.MongoClient(connection_string)

        return connection_string, collection_name, db_engine
