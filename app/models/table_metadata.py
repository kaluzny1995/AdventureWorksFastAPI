from pydantic import BaseModel
from typing import Optional

from app.models import EYesNo


class TableMetadata(BaseModel):
    table_catalog: str
    table_schema: str
    table_name: str
    column_name: str
    ordinal_position: int
    column_default: Optional[str] = None
    is_nullable: EYesNo
    data_type: str
    numeric_precision: Optional[int] = None
    numeric_precision_radix: Optional[int] = None
    numeric_scale: Optional[int] = None
    datetime_precision: Optional[int] = None
    is_updatable: EYesNo

    class Config:
        schema_extra = {
            "example": {
                "table_catalog": "postgres",
                "table_schema": "Purchasing",
                "table_name": "ShipMethod",
                "column_name": "ShipRate",
                "ordinal_position": 4,
                "column_default": "0.00",
                "is_nullable": EYesNo.NO,
                "data_type": "numeric",
                "numeric_precision": 19,
                "numeric_precision_radix": 10,
                "numeric_scale": 4,
                "datetime_precision": None,
                "is_updatable": EYesNo.YES
            }
        }
