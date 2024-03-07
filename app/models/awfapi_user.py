import datetime as dt
from pydantic import BaseModel, validate_model
from typing import Optional, Any

from app.models import E422UnprocessableEntity
from app import errors


class AWFAPIUserInput(BaseModel):
    username: str
    full_name: str
    email: str
    is_readonly: bool
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
                        "is_readonly": False,
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
                        "is_readonly": True,
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
                "is_readonly": False,
                "hashed_password": "$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6",
                "date_created": dt.datetime(2022, 12, 9, 12, 37, 22),
                "date_modified": dt.datetime(2023, 1, 27, 9, 19, 1)
            }
        }

    def validate_assignment(self, awfapi_user_input: AWFAPIUserInput) -> Any:
        """ Validates the model values assignment """
        awfapi_user_input_dict = awfapi_user_input.dict()
        values, fields, error = validate_model(self.__class__, awfapi_user_input_dict)
        awfapi_user_hidden_fields = ["date_created", "date_modified"]

        if error is not None:
            wrong_fields = list(map(lambda e: e['loc'][0], error.errors()))
            if not all(map(lambda wf: wf in awfapi_user_hidden_fields, wrong_fields)):
                raise errors.PydanticValidationError(f"{E422UnprocessableEntity.INVALID_AWFAPI_USER_VALUES}: {str(error)}")

        return values, fields

    def update_from_input(self, awfapi_user_input: AWFAPIUserInput) -> 'AWFAPIUser':
        """ Updates the model from its input. """

        values, fields = self.validate_assignment(awfapi_user_input)
        for name in fields:
            value = values[name]
            setattr(self, name, value)

        return self


class AWFAPIViewedUser(BaseModel):
    username: str
    full_name: str
    email: str
    is_readonly: bool
    date_created: dt.datetime
    date_modified: dt.datetime

    class Config:
        schema_extra = {
            "value": {
                "username": "dzhawaria",
                "full_name": "Dzhejkob Awaria",
                "email": "dzh.awaria@gmail.com",
                "is_readonly": False,
                "date_created": dt.datetime(2022, 12, 9, 12, 37, 22),
                "date_modified": dt.datetime(2023, 1, 27, 9, 19, 1)
            }
        }


class AWFAPIRegisteredUser(BaseModel):
    username: str
    password: str
    repeated_password: str
    full_name: str
    email: str
    is_readonly: bool

    class Config:
        schema_extra = {
            "examples": {
                "first": {
                    "summary": "First example",
                    "description": "First AWFAPI registered user example",
                    "value": {
                        "username": "dzhawaria",
                        "password": "awaria95",
                        "repeated_password": "awaria95",
                        "full_name": "Dzhejkob Awaria",
                        "email": "dzh.awaria@gmail.com",
                        "is_readonly": False
                    }
                },
                "second": {
                    "summary": "Second example",
                    "description": "Second AWFAPI registered user example",
                    "value": {
                        "username": "testuser",
                        "password": "testpassword",
                        "repeated_password": "testpassword",
                        "full_name": "Test AWFAPIUserInput",
                        "email": "test.user@test.user",
                        "is_readonly": True
                    }
                }
            }
        }


class AWFAPIChangedUserData(BaseModel):
    full_name: str
    email: str
    is_readonly: bool

    class Config:
        schema_extra = {
            "examples": {
                "first": {
                    "summary": "First example",
                    "description": "First AWFAPI changed user data example",
                    "value": {
                        "full_name": "Dzh Awaria",
                        "email": "dzhejkob.awaria@gmail.com",
                        "is_readonly": False
                    }
                },
                "second": {
                    "summary": "Second example",
                    "description": "Second AWFAPI changed user data example",
                    "value": {
                        "full_name": "Test AWFAPIUserInput2",
                        "email": "test2.user2@test.user",
                        "is_readonly": True
                    }
                }
            }
        }


class AWFAPIChangedUserCredentials(BaseModel):
    new_username: Optional[str]
    current_password: str
    new_password: Optional[str]
    repeated_password: Optional[str]

    class Config:
        schema_extra = {
            "examples": {
                "first": {
                    "summary": "First example",
                    "description": "First AWFAPI changed user credentials example",
                    "value": {
                        "new_username": "dzhejkobawaria",
                        "current_password": "awaria95",
                        "new_password": "dzhawaria95",
                        "repeated_password": "dzhawaria95"
                    }
                },
                "second": {
                    "summary": "Second example",
                    "description": "Second AWFAPI changed user credentials example",
                    "value": {
                        "current_password": "testpassword",
                        "new_password": "testpassword2",
                        "repeated_password": "testpassword2"
                    }
                },
                "third": {
                    "summary": "Third example",
                    "description": "Third AWFAPI changed user credentials example",
                    "value": {
                        "new_username": "testuser3",
                        "current_password": "testpassword2"
                    }
                }
            }
        }
