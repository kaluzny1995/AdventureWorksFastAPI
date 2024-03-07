import uuid
import datetime as dt
from pydantic import BaseModel, validate_model
from sqlmodel import SQLModel, Field, Column, Integer, String, DateTime
from typing import Any, Optional

from app.models import EPersonType, E422UnprocessableEntity
from app import errors


class PersonInput(BaseModel):
    person_type: EPersonType
    name_style: str = "0"
    title: Optional[str]
    first_name: str
    middle_name: Optional[str]
    last_name: str
    suffix: Optional[str]
    email_promotion: int = 0
    additional_contact_info: Optional[str]
    demographics: Optional[str]

    class Config:
        schema_extra = {
            "examples": {
                "simple": {
                    "summary": "Simple example",
                    "description": "Only required person fields",
                    "value": {
                        "person_type": EPersonType.GC,
                        "first_name": "John",
                        "last_name": "Doe",
                    }
                },
                "full": {
                    "summary": "All fields example",
                    "description": "All available person fields",
                    "value": {
                        "person_type": EPersonType.GC,
                        "name_style": "0",
                        "title": "Mr.",
                        "first_name": "John",
                        "middle_name": "J.",
                        "last_name": "Doe",
                        "suffix": "Jr",
                        "email_promotion": 1,
                        "additional_contact_info": "<contact_details>?</contact_details>",
                        "demographics": "<demographic_details>?</demographic_details>"
                    }
                }
            }
        }


class Person(SQLModel, table=True):
    business_entity_id: int = Field(sa_column=Column("BusinessEntityID", Integer, primary_key=True, nullable=False))
    person_type: EPersonType = Field(sa_column=Column("PersonType", String, nullable=False))
    name_style: str = Field(sa_column=Column("NameStyle", String, default="0", nullable=False))
    title: Optional[str] = Field(sa_column=Column("Title", String, nullable=True))
    first_name: str = Field(sa_column=Column("FirstName", String, nullable=False))
    middle_name: Optional[str] = Field(sa_column=Column("MiddleName", String, nullable=True))
    last_name: str = Field(sa_column=Column("LastName", String, nullable=False))
    suffix: Optional[str] = Field(sa_column=Column("Suffix", String, nullable=True))
    email_promotion: int = Field(sa_column=Column("EmailPromotion", Integer, default=0, nullable=False), ge=0, le=2)
    additional_contact_info: Optional[str] = Field(sa_column=Column("AdditionalContactInfo", String, nullable=True))
    demographics: Optional[str] = Field(sa_column=Column("Demographics", String, nullable=True))
    rowguid: uuid.UUID = Field(sa_column=Column("rowguid", String, default=uuid.uuid4, nullable=False))
    modified_date: dt.datetime = Field(sa_column=Column("ModifiedDate", DateTime, default=dt.datetime.utcnow, nullable=False))

    __tablename__ = "Person"
    __table_args__ = {'schema': "Person"}

    class Config:
        schema_extra = {
            "example": {
                "business_entity_id": 101,
                "person_type": EPersonType.GC,
                "name_style": "0",
                "title": "Mr.",
                "first_name": "John",
                "middle_name": "Tom",
                "last_name": "Doe",
                "suffix": "Jr",
                "email_promotion": 2,
                "additional_contact_info": "<contact_details>?</contact_details>",
                "demographics": "<demographic_details>?</demographic_details>",
                "rowguid": uuid.UUID("51480cef-b4c1-4f38-a53c-514723d9c5e9"),
                "modified_date": dt.datetime(2014, 1, 14, 0, 0, 0, 0)
                }
        }

    def validate_assignment(self, person_input: PersonInput) -> Any:
        """ Validates the model values assignment """

        person_input_dict = person_input.dict()
        values, fields, error = validate_model(self.__class__, person_input_dict)
        person_hidden_fields = ["business_entity_id", "rowguid", "modified_date"]

        if error is not None:
            wrong_fields = list(map(lambda e: e['loc'][0], error.errors()))
            if not all(map(lambda wf: wf in person_hidden_fields, wrong_fields)):
                raise errors.PydanticValidationError(f"{E422UnprocessableEntity.INVALID_PERSON_VALUES}: "
                                                     f"{str(error)}")

        return values, fields

    def update_from_input(self, person_input: PersonInput) -> 'Person':
        """ Updates the model from its input. """

        values, fields = self.validate_assignment(person_input)
        for name in fields:
            value = values[name]
            setattr(self, name, value)

        return self
