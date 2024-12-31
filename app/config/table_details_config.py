import json
from pydantic import BaseModel
from typing import Optional, List, Dict


class ForeignKey(BaseModel):
    columns: List[str]
    schema_name: str
    table: str

    class Config:
        frozen = True


class TableKeys(BaseModel):
    primary: List[str]
    foreign: Optional[Dict[str, ForeignKey]]

    class Config:
        frozen = True


class TableDetailsConfig(BaseModel):
    schema_name: str
    table: str
    columns: List[str]
    keys: TableKeys

    class Config:
        frozen = True

    @staticmethod
    def from_json(entity: str) -> 'TableDetailsConfig':
        with open("config.json", "r") as f:
            config = TableDetailsConfig(**json.load(f)['table_details'][entity])
        return config

    def get_primary_key_strings(self) -> List[str]:
        return list(map(lambda k: f"\"{self.schema_name}\".\"{self.table}\".\"{k}\"", self.keys.primary))

    def get_foreign_key_strings(self, joined_entity: str) -> List[str]:
        fk = self.keys.foreign[joined_entity]
        return list(map(lambda k: f"\"{fk.schema_name}\".\"{fk.table}\".\"{k}\"", fk.columns))

    @staticmethod
    def get_foreign_key_join_condition(entity: str, joined_entity: str) -> str:
        table_foreign_key = TableDetailsConfig.from_json(entity).get_foreign_key_strings(joined_entity)
        joined_table_primary_key = TableDetailsConfig.from_json(joined_entity).get_primary_key_strings()
        zipped = list(zip(table_foreign_key, joined_table_primary_key))

        return " AND ".join(list(map(lambda z: f"{z[0]}={z[1]}", zipped)))
