import json
from typing import List
from pydantic import BaseModel


class CORSMiddlewareConfig(BaseModel):
    allow_origins: List[str]
    allow_credentials: bool
    allow_methods: List[str]
    allow_headers: List[str]

    class Config:
        frozen = True

    @staticmethod
    def from_json() -> 'CORSMiddlewareConfig':
        with open("config.json", "r") as f:
            config = CORSMiddlewareConfig(**json.load(f)['cors_middleware'])
        return config
