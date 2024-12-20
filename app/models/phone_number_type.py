import datetime as dt
from pydantic import BaseModel, validate_model
from sqlmodel import SQLModel, Field, Column, Integer, String, DateTime
from typing import Any

from app.config import TableDetailsConfig
from app.models import E422UnprocessableEntity
from app import errors


tdc: TableDetailsConfig = TableDetailsConfig.from_json(entity="phone_number_type")


class PhoneNumberTypeInput(BaseModel):
    name: str

    class Config:
        schema_extra = {
            "examples": {
                "first": {
                    "summary": "First example",
                    "description": "First phone number type example",
                    "value": {
                        "name": "Remote work",
                    }
                },
                "second": {
                    "summary": "Second example",
                    "description": "Second phone number type example",
                    "value": {
                        "name": "Abroad work",
                    }
                }
            }
        }


class PhoneNumberType(SQLModel, table=True):
    phone_number_type_id: int = Field(sa_column=Column(tdc.columns[0], Integer, primary_key=True, nullable=False))
    name: str = Field(sa_column=Column(tdc.columns[1], String, nullable=False))
    modified_date: dt.datetime = Field(sa_column=Column(tdc.columns[2], DateTime, default=dt.datetime.utcnow, nullable=False))

    __tablename__ = tdc.table
    __table_args__ = {'schema': tdc.schema_name}

    class Config:
        schema_extra = {
            "example": {
                "phone_number_type_id": 101,
                "name": "Cell",
                "modified_date": dt.datetime(2014, 1, 14, 0, 0, 0, 0)
                }
        }

    def validate_assignment(self, phone_numer_type_input: PhoneNumberTypeInput) -> Any:
        """ Validates the model values assignment """

        phone_number_type_input_dict = phone_numer_type_input.dict()
        values, fields, error = validate_model(self.__class__, phone_number_type_input_dict)
        phone_number_type_hidden_fields = ["phone_number_type_id", "modified_date"]

        if error is not None:
            wrong_fields = list(map(lambda e: e['loc'][0], error.errors()))
            if not all(map(lambda wf: wf in phone_number_type_hidden_fields, wrong_fields)):
                raise errors.PydanticValidationError(f"{E422UnprocessableEntity.INVALID_PHONE_NUMBER_TYPE_VALUES}: "
                                                     f"{str(error)}")

        return values, fields

    def update_from_input(self, phone_numer_type_input: PhoneNumberTypeInput) -> 'PhoneNumberType':
        """ Updates the model from its input. """

        values, fields = self.validate_assignment(phone_numer_type_input)
        for name in fields:
            value = values[name]
            setattr(self, name, value)

        return self
