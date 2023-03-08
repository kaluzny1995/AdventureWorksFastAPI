import datetime as dt
from pydantic import BaseModel, validate_model


class AWFAPIUserInput(BaseModel):
    username: str
    full_name: str
    email: str
    is_disabled: bool
    hashed_password: str

    class Config:
        schema_extra = {
            "examples": {
                "first": {
                    "summary": "First example",
                    "description": "First AWFAPI user example",
                    "value": {
                        "username": "dzhawaria",
                        "full_name": "Dzhejkob Awaria",
                        "email": "dzh.awaria@gmail.com",
                        "is_disabled": False,
                        "hashed_password": "$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"
                    }
                },
                "second": {
                    "summary": "Second example",
                    "description": "Second AWFAPI user example",
                    "value": {
                        "username": "testuser",
                        "full_name": "Test AWFAPIUserInput",
                        "email": "test.user@test.user",
                        "is_disabled": True,
                        "hashed_password": "$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS"
                    }
                }
            }
        }


class AWFAPIUser(AWFAPIUserInput):
    date_created: dt.datetime
    date_modified: dt.datetime

    class Config:
        schema_extra = {
            "value": {
                "username": "dzhawaria",
                "full_name": "Dzhejkob Awaria",
                "email": "dzh.awaria@gmail.com",
                "is_disabled": False,
                "hashed_password": "$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6",
                "date_created": dt.datetime(2022, 12, 9, 12, 37, 22),
                "date_modified": dt.datetime(2023, 1, 27, 9, 19, 1)
            }
        }

    def update_from_input(self, awfapi_user_input: AWFAPIUserInput) -> 'AWFAPIUser':
        """ Updates the model from its input. """

        awfapi_user_input_dict = awfapi_user_input.dict()
        values, fields, error = validate_model(self.__class__, awfapi_user_input_dict)
        awfapi_user_hidden_fields = ["date_created", "date_modified"]

        if error is not None:
            wrong_fields = list(map(lambda e: e['loc'][0], error.errors()))
            if not all(map(lambda wf: wf in awfapi_user_hidden_fields, wrong_fields)):
                raise error

        for name in fields:
            value = values[name]
            setattr(self, name, value)

        return self
