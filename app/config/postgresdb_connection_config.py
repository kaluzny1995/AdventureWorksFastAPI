import json
from pydantic import BaseModel


class PostgresdbConnectionConfig(BaseModel):
    username: str
    password: str
    host: str
    port: int
    database: str

    class Config:
        frozen = True

    @staticmethod
    def from_json() -> 'PostgresdbConnectionConfig':
        with open("config.json", "r") as f:
            config = PostgresdbConnectionConfig(**json.load(f)['postgresdb_connection'])
        return config

    @staticmethod
    def get_db_connection_string() -> str:
        pcc = PostgresdbConnectionConfig.from_json()
        return f"postgresql+psycopg2://{pcc.username}:{pcc.password}@{pcc.host}:{pcc.port}/{pcc.database}"
