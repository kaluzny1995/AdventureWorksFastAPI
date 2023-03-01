from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Optional, Dict
import datetime as dt

from app import errors
from app.config import JWTAuthenticationConfig
from app.models.jwt_authentication import UserInDB, TokenData

from app.temp_db import temp_users_db


class JWTAuthenticationService:
    jwt_auth_config: JWTAuthenticationConfig = JWTAuthenticationConfig.from_json()
    pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def get_user(self, db: dict, username: str) -> Optional[UserInDB]:
        if username in db:
            user_dict = db[username]
            return UserInDB(**user_dict)
        return None

    def authenticate_user(self, db: dict, username: str, password: str) -> Optional[UserInDB]:
        user = self.get_user(db, username)
        if user is None:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def get_user_from_token(self, encoded_jwt: str) -> UserInDB:
        try:
            payload = self.get_access_token_payload(encoded_jwt)
            username: str = payload.get("sub")
            if username is None:
                raise errors.InvalidCredentialsError("Could not decode username from token.")

            token_data = TokenData(username=username)
            user = self.get_user(temp_users_db, username=token_data.username)  # Implement users db provider
            if user is None:
                raise errors.InvalidCredentialsError("Could not found the user in database.")

            return user

        except ExpiredSignatureError:
            raise errors.JWTTokenSignatureExpiredError("JWT token signature expired.")
        except JWTError:
            raise errors.InvalidCredentialsError("Could not validate credentials.")

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = dt.datetime.utcnow() + dt.timedelta(minutes=self.jwt_auth_config.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_auth_config.secret_key, algorithm=self.jwt_auth_config.algorithm)
        return encoded_jwt

    def get_access_token_payload(self, encoded_jwt: str) -> Dict[str, str]:
        try:
            return jwt.decode(encoded_jwt, self.jwt_auth_config.secret_key, algorithms=[self.jwt_auth_config.algorithm])
        except ExpiredSignatureError:
            raise errors.JWTTokenSignatureExpiredError("JWT token signature expired.")
        except JWTError:
            raise errors.InvalidCredentialsError("Could not validate credentials.")
