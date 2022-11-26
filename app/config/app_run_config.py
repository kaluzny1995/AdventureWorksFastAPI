import json
from pydantic import BaseModel


class AppRunConfig(BaseModel):
    host: str
    port: int
    reload: bool
    log_level: str

    class Config:
        frozen = True

    @staticmethod
    def from_json() -> 'AppRunConfig':
        with open("config.json", "r") as f:
            config = AppRunConfig(**json.load(f)['app_run'])
        return config
