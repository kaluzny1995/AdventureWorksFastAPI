from pydantic import BaseModel


class CountMessage(BaseModel):
    entity: str
    count: int

    class Config:
        schema_extra = {
            "example": {
                "entity": "Person",
                "count": 10
            }
        }


class ResponseMessage(BaseModel):
    title: str
    description: str
    code: int

    class Config:
        schema_extra = {
            "example": {
                "title": "Message title",
                "description": "Long description of message details.",
                "code": 200
            }
        }


class PrimaryKeyErrorDetails(BaseModel):
    key_column: str
    key_value: str

    class Config:
        schema_extra = {
            "example": {
                "key_column": "\"BusinessEntityID\", \"PhoneNumber\", \"PhoneNumberTypeID\"",
                "key_value": "20789, 001 002 003, 5"
            }
        }


class ForeignKeyErrorDetails(BaseModel):
    entity: str
    key_column: str
    key_value: str

    class Config:
        schema_extra = {
            "example": {
                "entity": "PhoneNumberType",
                "key_column": "PhoneNumberTypeID",
                "key_value": "10"
            }
        }
