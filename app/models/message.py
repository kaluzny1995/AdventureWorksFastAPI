from pydantic import BaseModel


class Message(BaseModel):
    title: str
    description: str

    class Config:
        schema_extra = {
            "example": {
                "title": "Message title",
                "description": "Long description of message details."
            }
        }


class ResponseMessage(Message):
    code: int

    class Config:
        schema_extra = {
            "example": {
                "title": "Message title",
                "description": "Long description of message details.",
                "code": 200
            }
        }
