from passlib.context import CryptContext
from jose import jwt
from typing import Optional
import datetime as dt

from app.config import JWTAuthenticationConfig
from app.models.jwt_authentication import UserInDB


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

    def create_access_token(self, data: dict, expires_delta: Optional[dt.timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = dt.datetime.utcnow() + expires_delta
        else:
            expire = dt.datetime.utcnow() + dt.timedelta(minutes=self.jwt_auth_config.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_auth_config.secret_key, algorithm=self.jwt_auth_config.algorithm)
        return encoded_jwt
