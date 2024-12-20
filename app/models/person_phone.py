import datetime as dt
from pydantic import BaseModel, validate_model
from sqlmodel import SQLModel, Field, Column, Integer, String, DateTime, ForeignKey
from typing import Any

from app.models import E422UnprocessableEntity, BusinessEntity, PhoneNumberType
from app import errors


class PersonPhoneInput(BaseModel):
    business_entity_id: int
    phone_number: str
    phone_number_type_id: int

    class Config:
        schema_extra = {
            "examples": {
                "first": {
                    "summary": "First example",
                    "description": "First phone number type example",
                    "value": {
                        "business_entity_id": 101,
                        "phone_number": "71 345 07 96",
                        "phone_number_type_id": 1
                    }
                },
                "second": {
                    "summary": "Second example",
                    "description": "Second phone number type example",
                    "value": {
                        "business_entity_id": 102,
                        "phone_number": "1 (11) 500 555-0120",
                        "phone_number_type_id": 2
                    }
                }
            }
        }


class PersonPhone(SQLModel, table=True):
    business_entity_id: int = Field(sa_column=Column("BusinessEntityID", Integer, ForeignKey(BusinessEntity.business_entity_id), primary_key=True, nullable=False))
    phone_number: str = Field(sa_column=Column("PhoneNumber", String, primary_key=True, nullable=False))
    phone_number_type_id: int = Field(sa_column=Column("PhoneNumberTypeID", Integer, ForeignKey(PhoneNumberType.phone_number_type_id), primary_key=True, nullable=False))
    modified_date: dt.datetime = Field(sa_column=Column("ModifiedDate", DateTime, default=dt.datetime.utcnow, nullable=False))

    __tablename__ = "PersonPhone"
    __table_args__ = {'schema': "Person"}

    class Config:
        schema_extra = {
            "examples": {
                "first": {
                    "summary": "First example",
                    "description": "First phone number type example",
                    "value": {
                        "business_entity_id": 101,
                        "phone_number": "71 345 07 96",
                        "phone_number_type_id": 1,
                        "modified_date": dt.datetime(2014, 1, 14, 0, 0, 0, 0)
                    }
                },
                "second": {
                    "summary": "Second example",
                    "description": "Second phone number type example",
                    "value": {
                        "business_entity_id": 102,
                        "phone_number": "1 (11) 500 555-0120",
                        "phone_number_type_id": 2,
                        "modified_date": dt.datetime(2014, 1, 14, 0, 0, 0, 0)
                    }
                }
            }
        }

    def validate_assignment(self, person_phone_input: PersonPhoneInput) -> Any:
        """ Validates the model values assignment """

        person_phone_input_dict = person_phone_input.dict()
        values, fields, error = validate_model(self.__class__, person_phone_input_dict)
        person_phone_hidden_fields = ["modified_date"]

        if error is not None:
            wrong_fields = list(map(lambda e: e['loc'][0], error.errors()))
            if not all(map(lambda wf: wf in person_phone_hidden_fields, wrong_fields)):
                raise errors.PydanticValidationError(f"{E422UnprocessableEntity.INVALID_PERSON_PHONE_VALUES}: "
                                                     f"{str(error)}")

        return values, fields

    def update_from_input(self, person_phone_input: PersonPhoneInput) -> 'PersonPhone':
        """ Updates the model from its input. """

        values, fields = self.validate_assignment(person_phone_input)
        for name in fields:
            value = values[name]
            setattr(self, name, value)

        return self
