from jose import jwt, JWTError, ExpiredSignatureError
from typing import Optional, Dict
import datetime as dt

from app import errors
from app.config import JWTAuthenticationConfig
from app.providers import IAWFAPIUserProvider, AWFAPIUserProvider
from app.services import AWFAPIUserService
from app.models import AWFAPIUser, TokenData, E401Unauthorized


class JWTAuthenticationService:
    jwt_auth_config: JWTAuthenticationConfig
    awfapi_user_provider: IAWFAPIUserProvider
    awfapi_user_service: AWFAPIUserService

    def __init__(self,
                 jwt_auth_config: Optional[JWTAuthenticationConfig] = None,
                 awfapi_user_provider: Optional[IAWFAPIUserProvider] = None,
                 awfapi_user_service: Optional[AWFAPIUserService] = None):
        self.jwt_auth_config = jwt_auth_config or JWTAuthenticationConfig.from_json()
        self.awfapi_user_provider = awfapi_user_provider or AWFAPIUserProvider()
        self.awfapi_user_service = awfapi_user_service or AWFAPIUserService()

    def authenticate_user(self, username: str, password: str) -> Optional[AWFAPIUser]:
        try:
            user = self.awfapi_user_provider.get_awfapi_user(username)
            if not self.awfapi_user_service.verify_password(password, user.hashed_password):
                raise errors.InvalidCredentialsError(f"{E401Unauthorized.INVALID_PASSWORD}: Invalid password.")

            return user
        except errors.NotFoundError:
            raise errors.InvalidCredentialsError(f"{E401Unauthorized.INVALID_USERNAME}: Invalid username.")

    def get_user_from_token(self, encoded_jwt: str) -> AWFAPIUser:
        try:
            payload = self.get_access_token_payload(encoded_jwt)
            username = payload.get("sub")
            if username is None:
                raise errors.InvalidCredentialsError(f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                                     f"Could not decode username from token.")

            token_data = TokenData(username=username)
            user = self.awfapi_user_provider.get_awfapi_user(token_data.username)
            return user

        except ExpiredSignatureError:
            raise errors.JWTTokenSignatureExpiredError(f"{E401Unauthorized.JWT_TOKEN_EXPIRED}: "
                                                       f"JWT token signature expired.")
        except (JWTError, errors.NotFoundError):
            raise errors.InvalidCredentialsError(f"{E401Unauthorized.INVALID_CREDENTIALS}: "
                                                 f"Could not validate credentials.")

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
            raise errors.JWTTokenSignatureExpiredError(f"{E401Unauthorized.JWT_TOKEN_EXPIRED}: "
                                                       f"JWT token signature expired.")
        except JWTError:
            raise errors.InvalidCredentialsError(f"{E401Unauthorized.INVALID_CREDENTIALS}: "
                                                 f"Could not validate credentials.")
