from pydantic import BaseModel

from app.config import JWTAuthenticationConfig
from app.providers import AWFAPIUserProvider
from app.services import AWFAPIUserService, JWTAuthenticationService


class JWTAuthenticationFactory(BaseModel):

    @staticmethod
    def get_service(awfapi_user_provider: AWFAPIUserProvider,
                    awfapi_user_service: AWFAPIUserService) -> JWTAuthenticationService:
        return JWTAuthenticationService(
            jwt_auth_config=JWTAuthenticationConfig.from_json(),
            awfapi_user_provider=awfapi_user_provider,
            awfapi_user_service=awfapi_user_service
        )
