import datetime as dt
import pymongo
from typing import Optional, List

from app import errors
from app.config import MongodbConnectionConfig
from app.models import AWFAPIUserInput, AWFAPIUser, E400BadRequest, E404NotFound
from app.providers import IAWFAPIUserProvider


class AWFAPIUserProvider(IAWFAPIUserProvider):
    connection_string: str
    collection_name: str
    db_engine: pymongo.MongoClient

    def __init__(self, connection_string: Optional[str] = None, collection_name: Optional[str] = None,
                 db_engine: Optional[pymongo.MongoClient] = None):
        super(AWFAPIUserProvider, self).__init__()
        self.connection_string = connection_string or MongodbConnectionConfig.get_db_connection_string()
        self.collection_name = collection_name or MongodbConnectionConfig.get_collection_name()
        self.db_engine = db_engine or pymongo.MongoClient(self.connection_string)

    def get_awfapi_users(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[AWFAPIUser]:
        awfapi_user_definitions = self.db_engine.awfapi[self.collection_name].find()
        if offset is not None:
            awfapi_user_definitions = awfapi_user_definitions.skip(offset)
        if limit is not None:
            awfapi_user_definitions = awfapi_user_definitions.limit(limit)
        return list(map(lambda au: AWFAPIUser(**au), awfapi_user_definitions))

    def get_awfapi_user(self, username: str) -> AWFAPIUser:
        awfapi_user_definition = self.db_engine.awfapi[self.collection_name].find_one({'username': {"$eq": username}})
        if awfapi_user_definition is None:
            raise errors.NotFoundError(f"{E404NotFound.AWFAPI_USER_NOT_FOUND}: "
                                       f"AWFAPI user of username '{username}' does not exist.")
        return AWFAPIUser(**awfapi_user_definition)

    def insert_awfapi_user(self, awfapi_user_input: AWFAPIUserInput) -> str:
        self.__guard_unique_username(awfapi_user_input.username)
        self.__guard_unique_email(awfapi_user_input.email)

        awfapi_user = AWFAPIUser(date_created=dt.datetime.utcnow(), date_modified=dt.datetime.utcnow(),
                                 **awfapi_user_input.dict())
        awfapi_user.validate_assignment(awfapi_user_input)
        self.db_engine.awfapi[self.collection_name].insert_one(awfapi_user.dict())
        return awfapi_user.username

    def update_awfapi_user(self, username: str, awfapi_user_input: AWFAPIUserInput) -> str:
        updated_awfapi_user = self.get_awfapi_user(username)
        self.__guard_unique_username(awfapi_user_input.username, updated_awfapi_user.username)
        self.__guard_unique_email(awfapi_user_input.email, updated_awfapi_user.email)

        updated_awfapi_user.update_from_input(awfapi_user_input)
        updated_awfapi_user.date_modified = dt.datetime.utcnow()
        self.db_engine.awfapi[self.collection_name].update_one({'username': {"$eq": username}},
                                                               {"$set": updated_awfapi_user.dict()})
        return updated_awfapi_user.username

    def delete_awfapi_user(self, username: str) -> None:
        self.get_awfapi_user(username)
        self.db_engine.awfapi[self.collection_name].delete_one({'username': {"$eq": username}})

    def __guard_unique_username(self, new_username: str, current_username: Optional[str] = None) -> None:
        awfapi_users = self.get_awfapi_users()
        other_usernames = list(map(lambda au: au.username,
                                   filter(lambda au: au.username != current_username, awfapi_users)))

        if new_username in other_usernames:
            raise errors.UsernameAlreadyExistsError(f"{E400BadRequest.UNIQUE_CONSTRAINT_VIOLATION}: "
                                                    f"[username] [{new_username}] "
                                                    f"Field 'username' must have unique values. "
                                                    f"Provided username '{new_username}' already exists.")

    def __guard_unique_email(self, new_email: str, current_email: Optional[str] = None) -> None:
        awfapi_users = self.get_awfapi_users()
        other_emails = list(map(lambda au: au.email,
                                filter(lambda au: au.email != current_email, awfapi_users)))

        if new_email in other_emails:
            raise errors.EmailAlreadyExistsError(f"{E400BadRequest.UNIQUE_CONSTRAINT_VIOLATION}: "
                                                 f"[email] [{new_email}] "
                                                 f"Field 'email' must have unique values. "
                                                 f"Provided email '{new_email}' already exists.")
