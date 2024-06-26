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
