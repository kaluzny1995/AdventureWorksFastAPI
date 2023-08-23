import json
from pydantic import BaseModel


class MongodbConnectionConfig(BaseModel):
    username: str
    password: str
    host: str
    port: int
    database: str
    collection: str

    class Config:
        frozen = True

    @staticmethod
    def from_json() -> 'MongodbConnectionConfig':
        with open("config.json", "r") as f:
            config = MongodbConnectionConfig(**json.load(f)['mongodb_connection'])
        return config

    @staticmethod
    def get_db_connection_string() -> str:
        mcc = MongodbConnectionConfig.from_json()
        return f"mongodb://{mcc.username}:{mcc.password}@{mcc.host}:{mcc.port}/?authMechanism=DEFAULT"

    @staticmethod
    def get_collection_name(test_suffix: str = "") -> str:
        mcc = MongodbConnectionConfig.from_json()
        return f"{mcc.collection}{test_suffix}"
