from typing import Optional, List

from app.models import AWFAPIUserInput, AWFAPIUser


class IAWFAPIUserProvider:
    def get_awfapi_users(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[AWFAPIUser]:
        """ Returns list of all AWFAPI users """
        raise NotImplementedError

    def get_awfapi_user(self, username: str) -> AWFAPIUser:
        """ Returns AWFAPI user of given username """
        raise NotImplementedError

    def insert_awfapi_user(self, awfapi_user_input: AWFAPIUserInput) -> str:
        """ Inserts AWFAPI user and returns new AWFAPI user username """
        raise NotImplementedError

    def update_awfapi_user(self, username: str, awfapi_user_input: AWFAPIUserInput) -> str:
        """ Updates AWFAPI user of given person_id and return updated AWFAPI user username """
        raise NotImplementedError

    def delete_awfapi_user(self, username: str) -> None:
        """ Deletes AWFAPI user of given username """
        raise NotImplementedError
