import datetime as dt
from pydantic import BaseModel, validate_model
from sqlmodel import SQLModel, Field, Column, Integer, String, DateTime


class PersonPhoneInput(BaseModel):
    business_entity_id: int
    phone_number: str
    phone_number_type_id: int

    class Config:
        schema_extra = {
            "example": {
                "business_entity_id": 1,
                "phone_number": "(+00) 123 456 789",
                "phone_number_type_id": 1
            }
        }


class PersonPhone(SQLModel, table=True):
    business_entity_id: int = Field(sa_column=Column("BusinessEntityID", Integer, primary_key=True, nullable=False))
    phone_number: str = Field(sa_column=Column("PhoneNumber", String, primary_key=True, nullable=False))
    phone_number_type_id: int = Field(sa_column=Column("PhoneNumberTypeID", Integer, primary_key=True, nullable=False))
    modified_date: dt.datetime = Field(sa_column=Column("ModifiedDate", DateTime, default=dt.datetime.utcnow, nullable=False))

    __tablename__ = "PersonPhone"
    __table_args__ = {'schema': "Person"}

    class Config:
        schema_extra = {
            "example": {
                "business_entity_id": 101,
                "phone_number": "123 456 789",
                "phone_number_type_id": 1,
                "modified_date": dt.datetime(2014, 1, 14, 0, 0, 0, 0)
            }
        }

    def update_from_input(self, person_phone_input: PersonPhoneInput) -> 'PersonPhone':
        """ Updates the model from its input. """

        person_phone_input_dict = person_phone_input.dict()
        values, fields, error = validate_model(self.__class__, person_phone_input_dict)
        person_phone_hidden_fields = ["modified_date"]

        if error is not None:
            wrong_fields = list(map(lambda e: e['loc'][0], error.errors()))
            if not all(map(lambda wf: wf in person_phone_hidden_fields, wrong_fields)):
                raise error

        for name in fields:
            value = values[name]
            setattr(self, name, value)

        return self
