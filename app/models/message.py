from pydantic import BaseModel


class Message(BaseModel):
    info: str
    message: str

    class Config:
        schema_extra = {
            "example": {
                "info": "Message info",
                "message": "Long description of info details."
            }
        }
