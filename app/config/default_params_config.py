import json
from pydantic import BaseModel
from typing import Optional

from app.models import EOrderType


class DefaultParamsConfig(BaseModel):
    filters: Optional[str]
    order_by: Optional[str]
    order_type: EOrderType
    offset: int
    limit: int

    class Config:
        frozen = True

    @staticmethod
    def from_json(entity: str) -> 'DefaultParamsConfig':
        with open("config.json", "r") as f:
            config = DefaultParamsConfig(**json.load(f)['default_params'][entity])
        return config
