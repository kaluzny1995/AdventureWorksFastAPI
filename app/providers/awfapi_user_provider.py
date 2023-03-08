import datetime as dt
import pymongo
from typing import Optional, List

from app import errors
from app.config import MongodbConnectionConfig
from app.models import AWFAPIUserInput, AWFAPIUser


class AWFAPIUserProvider:
    connection_string: str = MongodbConnectionConfig.get_db_connection_string()
    db_engine = pymongo.MongoClient(connection_string)

    def get_awfapi_users(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[AWFAPIUser]:
        awfapi_user_definitions = self.db_engine.awfapi.users.find()
        if offset is not None:
            awfapi_user_definitions = awfapi_user_definitions.skip(offset)
        if limit is not None:
            awfapi_user_definitions = awfapi_user_definitions.limit(limit)
        return list(map(lambda au: AWFAPIUser(**au), awfapi_user_definitions))

    def get_awfapi_user(self, username: str) -> AWFAPIUser:
        awfapi_user_definition = self.db_engine.awfapi.users.find_one({'username': {"$eq": username}})
        if awfapi_user_definition is None:
            raise errors.NotFoundError(f"AWFAPI user of username '{username}' does not exist")
        return AWFAPIUser(**awfapi_user_definition)

    def insert_awfapi_user(self, awfapi_user_input: AWFAPIUserInput) -> str:
        self.guard_unique_username(awfapi_user_input.username)
        self.guard_unique_email(awfapi_user_input.email)

        awfapi_user = AWFAPIUser(date_created=dt.datetime.utcnow(), date_modified=dt.datetime.utcnow(),
                                 **awfapi_user_input.dict())
        self.db_engine.awfapi.users.insert_one(awfapi_user.dict())
        return awfapi_user.username

    def update_awfapi_user(self, username: str, awfapi_user_input: AWFAPIUserInput) -> str:
        updated_awfapi_user = self.get_awfapi_user(username)
        self.guard_unique_username(awfapi_user_input.username, updated_awfapi_user.username)
        self.guard_unique_email(awfapi_user_input.email, updated_awfapi_user.email)

        updated_awfapi_user.update_from_input(awfapi_user_input)
        updated_awfapi_user.date_modified = dt.datetime.utcnow()
        self.db_engine.awfapi.users.update_one({'username': {"$eq": username}},
                                               {"$set": updated_awfapi_user.dict()})
        return updated_awfapi_user.username

    def delete_awfapi_user(self, username: str) -> None:
        self.get_awfapi_user(username)
        self.db_engine.awfapi.users.delete_one({'username': {"$eq": username}})

    def guard_unique_username(self, new_username: str, current_username: Optional[str] = None) -> None:
        awfapi_users = self.get_awfapi_users()
        other_usernames = list(map(lambda au: au.username,
                                   filter(lambda au: au.username != current_username, awfapi_users)))

        if new_username in other_usernames:
            raise errors.UsernameAlreadyExistsError(f"Provided username '{new_username}' already exists.")

    def guard_unique_email(self, new_email: str, current_email: Optional[str] = None) -> None:
        awfapi_users = self.get_awfapi_users()
        other_emails = list(map(lambda au: au.email,
                                filter(lambda au: au.email != current_email, awfapi_users)))

        if new_email in other_emails:
            raise errors.EmailAlreadyExistsError(f"Provided email '{new_email}' already exists.")
