from typing import Optional
from passlib.context import CryptContext

from app.models import AWFAPIUserInput,\
    AWFAPIViewedUser, AWFAPIRegisteredUser, AWFAPIChangedUserData, AWFAPIChangedUserCredentials
from app.providers import IAWFAPIUserProvider, AWFAPIUserProvider
from app import errors


class AWFAPIUserService:
    pwd_context: CryptContext
    awfapi_user_provider: IAWFAPIUserProvider

    def __init__(self, pwd_context: Optional[CryptContext] = None,
                 awfapi_user_provider: Optional[IAWFAPIUserProvider] = None):
        self.pwd_context = pwd_context or CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.awfapi_user_provider = awfapi_user_provider or AWFAPIUserProvider()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def view_awfapi_user(self, awfapi_user_username: str) -> 'AWFAPIViewedUser':
        awfapi_user = self.awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        return AWFAPIViewedUser(**awfapi_user.dict(exclude={"hashed_password"}))

    def register_awfapi_user(self, awfapi_registered_user: AWFAPIRegisteredUser) -> str:
        hashed_password = self.hash_password(awfapi_registered_user.password)

        awfapi_user_input_dict = awfapi_registered_user.dict(exclude={"password", "repeated_password"})
        awfapi_user_input_dict.update({"hashed_password": hashed_password})
        awfapi_user_input = AWFAPIUserInput(**awfapi_user_input_dict)

        return self.awfapi_user_provider.insert_awfapi_user(awfapi_user_input)

    def change_awfapi_user_data(self, awfapi_user_username: str,
                                awfapi_changed_user_data: AWFAPIChangedUserData) -> str:
        awfapi_user = self.awfapi_user_provider.get_awfapi_user(awfapi_user_username)

        awfapi_user_input_dict = awfapi_changed_user_data.dict()
        awfapi_user_input_dict.update({"username": awfapi_user.username,
                                       "hashed_password": awfapi_user.hashed_password})
        awfapi_user_input = AWFAPIUserInput(**awfapi_user_input_dict)

        return self.awfapi_user_provider.update_awfapi_user(awfapi_user_username, awfapi_user_input)

    def change_awfapi_user_credentials(self, awfapi_user_username: str,
                                       awfapi_changed_user_credentials: AWFAPIChangedUserCredentials) -> str:
        awfapi_user = self.awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        if not self.verify_password(awfapi_changed_user_credentials.current_password, awfapi_user.hashed_password):
            raise errors.InvalidCredentialsError("Wrong current password.")

        username = awfapi_user.username if awfapi_changed_user_credentials.new_username is None else \
            awfapi_changed_user_credentials.new_username
        hashed_password = awfapi_user.hashed_password if awfapi_changed_user_credentials.new_password is None else \
            self.hash_password(awfapi_changed_user_credentials.new_password)

        awfapi_user_input_dict = awfapi_user.dict(include={"full_name", "email", "is_readonly"})
        awfapi_user_input_dict.update({"username": username, "hashed_password": hashed_password})
        awfapi_user_input = AWFAPIUserInput(**awfapi_user_input_dict)

        return self.awfapi_user_provider.update_awfapi_user(awfapi_user_username, awfapi_user_input)

    def remove_awfapi_user_account(self, awfapi_user_username: str) -> None:
        self.awfapi_user_provider.delete_awfapi_user(awfapi_user_username)
