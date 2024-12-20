import uuid
import datetime as dt
from sqlmodel import SQLModel, Field, Column, Integer, String, DateTime

from app.config import TableDetailsConfig


tdc: TableDetailsConfig = TableDetailsConfig.from_json(entity="business_entity")

class BusinessEntity(SQLModel, table=True):
    business_entity_id: int = Field(sa_column=Column(tdc.columns[0], Integer, primary_key=True, nullable=False))
    rowguid: uuid.UUID = Field(sa_column=Column(tdc.columns[1], String, default=uuid.uuid4, nullable=False))
    modified_date: dt.datetime = Field(sa_column=Column(tdc.columns[2], DateTime, default=dt.datetime.utcnow, nullable=False))

    __tablename__ = tdc.table
    __table_args__ = {'schema': tdc.schema_name}

    class Config:
        schema_extra = {
            "example": {
                "business_entity_id": 101,
                "rowguid": uuid.UUID("51480cef-b4c1-4f38-a53c-514723d9c5e9"),
                "modified_date": dt.datetime(2014, 1, 14, 0, 0, 0, 0)
            }
        }
