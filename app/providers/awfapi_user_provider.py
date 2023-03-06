import datetime as dt
import pymongo
from typing import Optional, List

from app import errors
from app.config import MongodbConnectionConfig
from app.models import UserInput, User


class AWFAPIUserProvider:
    connection_string: str = MongodbConnectionConfig.get_db_connection_string()
    db_engine = pymongo.MongoClient(connection_string)

    def get_awfapi_users(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[User]:
        awfapi_user_definitions = self.db_engine.awfapi.users.find()
        if offset is not None:
            awfapi_user_definitions = awfapi_user_definitions.skip(offset)
        if limit is not None:
            awfapi_user_definitions = awfapi_user_definitions.limit(limit)
        return list(map(lambda au: User(**au), awfapi_user_definitions))

    def get_awfapi_user(self, username: str) -> User:
        awfapi_user_definition = self.db_engine.awfapi.users.find_one({'username': {"$eq": username}})
        if awfapi_user_definition is None:
            raise errors.NotFoundError(f"AWFAPI user of username '{username}' does not exist")
        return User(**awfapi_user_definition)

    def insert_awfapi_user(self, awfapi_user_input: UserInput) -> str:
        awfapi_user = User(date_created=dt.datetime.utcnow(), date_modified=dt.datetime.utcnow(),
                           **awfapi_user_input.dict())
        self.db_engine.awfapi.users.insert_one(awfapi_user.dict())
        return awfapi_user.username

    def update_awfapi_user(self, username: str, awfapi_user_input: UserInput) -> str:
        updated_awfapi_user = self.get_awfapi_user(username)
        updated_awfapi_user.update_from_input(awfapi_user_input)
        updated_awfapi_user.date_modified = dt.datetime.utcnow()
        self.db_engine.awfapi.users.update_one({'username': {"$eq": username}},
                                               {"$set": updated_awfapi_user.dict()})
        return updated_awfapi_user.username

    def delete_awfapi_user(self, username: str) -> None:
        self.get_awfapi_user(username)
        self.db_engine.awfapi.users.delete_one({'username': {"$eq": username}})
