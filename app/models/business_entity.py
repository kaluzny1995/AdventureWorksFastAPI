import uuid
import datetime as dt
from sqlmodel import SQLModel, Field, Column, Integer, String, DateTime


class BusinessEntity(SQLModel, table=True):
    business_entity_id: int = Field(sa_column=Column("BusinessEntityID", Integer, primary_key=True, nullable=False))
    rowguid: uuid.UUID = Field(sa_column=Column("rowguid", String, default=uuid.uuid4, nullable=False))
    modified_date: dt.datetime = Field(sa_column=Column("ModifiedDate", DateTime, default=dt.datetime.utcnow, nullable=False))

    __tablename__ = "BusinessEntity"
    __table_args__ = {'schema': "Person"}

    class Config:
        schema_extra = {
            "example": {
                "business_entity_id": 101,
                "rowguid": uuid.UUID("51480cef-b4c1-4f38-a53c-514723d9c5e9"),
                "modified_date": dt.datetime(2014, 1, 14, 0, 0, 0, 0)
            }
        }
