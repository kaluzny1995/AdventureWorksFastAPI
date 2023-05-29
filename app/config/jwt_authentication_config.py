import json
from pydantic import BaseModel


class JWTAuthenticationConfig(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    class Config:
        frozen = True

    @staticmethod
    def from_json() -> 'JWTAuthenticationConfig':
        with open("config.json", "r") as f:
            config = JWTAuthenticationConfig(**json.load(f)['jwt_auth_config'])
        return config
