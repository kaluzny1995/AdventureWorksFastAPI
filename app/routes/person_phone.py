from fastapi import APIRouter, Body, Depends, status
from typing import Optional, Tuple, List

from app import errors
from app.config import DefaultParamsConfig
from app.models import (EOrderType, AWFAPIUser, PhoneNumberType, Person, PersonPhoneInput, PersonPhone,
                        CountMessage, ResponseMessage, get_response_models)
from app.providers import PersonPhoneProvider

from app.oauth2_handlers import get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_400, raise_404, raise_422, raise_500


router: APIRouter = APIRouter()

default_params: DefaultParamsConfig = DefaultParamsConfig.from_json(entity="person_phone")
person_phone_provider: PersonPhoneProvider = PersonPhoneProvider()


@router.get("/get_person_phones", tags=["Person Phones"],
            responses=get_response_models(List[Tuple[PersonPhone, Person, PhoneNumberType]], [200, 400, 401, 500]))
def get_person_phones(filters: Optional[str] = default_params.filters,
                      order_by: Optional[str] = default_params.order_by,
                      order_type: Optional[EOrderType] = default_params.order_type,
                      offset: int = default_params.offset, limit: int = default_params.limit,
                      _: AWFAPIUser = Depends(get_current_user)) -> List[Tuple[PersonPhone, Person, PhoneNumberType]]:
    if filters == "":
        filters = None
    if order_by == "":
        order_by = None

    try:
        person_phones = person_phone_provider.get_person_phones(filters, order_by, order_type, limit, offset)
        return person_phones
    except (errors.InvalidFilterStringError, errors.FilterNotFoundError,
            errors.ColumnNotFoundError, errors.InvalidSQLValueError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.get("/count_person_phones", tags=["Person Phones"],
            responses=get_response_models(CountMessage, [200, 400, 401, 500]))
def count_persons(filters: Optional[str] = default_params.filters,
                  _: AWFAPIUser = Depends(get_current_user)) -> CountMessage:
    if filters == "":
        filters = None
    try:
        person_phones_count = person_phone_provider.count_person_phones(filters)
        return CountMessage(entity="Person phone", count=person_phones_count)
    except (errors.InvalidFilterStringError, errors.FilterNotFoundError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.get("/get_person_phone/{person_id}/{phone_number}/{phone_number_type_id}", tags=["Person Phones"],
            responses=get_response_models(Tuple[PersonPhone, Person, PhoneNumberType], [200, 400, 401, 404, 500]))
def get_person_phone(person_id: int, phone_number: str, phone_number_type_id: int,
                     _: AWFAPIUser = Depends(get_current_user)) -> Tuple[PersonPhone, Person, PhoneNumberType]:
    person_phone_id = tuple((person_id, phone_number, phone_number_type_id))
    try:
        person_phone = person_phone_provider.get_person_phone(person_phone_id)
        return person_phone
    except errors.NotFoundError as e:
        raise_404(e, "Person phone", person_phone_id)
    except Exception as e:
        raise_500(e)


@router.post("/create_person_phone", tags=["Person Phones"],
             responses=get_response_models(PersonPhone, [201, 400, 401, 422, 500]), status_code=status.HTTP_201_CREATED)
def create_person_phone(
        person_phone_input: PersonPhoneInput = Body(None, examples=PersonPhoneInput.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Tuple[PersonPhone, Person, PhoneNumberType]:
    try:
        new_person_phone_id = person_phone_provider.insert_person_phone(person_phone_input)
        new_person_phone = person_phone_provider.get_person_phone(new_person_phone_id)
        return new_person_phone
    except errors.IntegrityError as e:
        raise_400(e)
    except errors.PydanticValidationError as e:
        raise_422(e)
    except Exception as e:
        raise_500(e)


@router.put("/update_person_phone/{person_id}/{phone_number}/{phone_number_type_id}", tags=["Person Phones"],
            responses=get_response_models(PersonPhone, [200, 400, 401, 404, 422, 500]))
def update_person_phone(
        person_id: int, phone_number: str, phone_number_type_id: int,
        person_phone_input: PersonPhoneInput = Body(None, examples=PersonPhoneInput.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Tuple[PersonPhone, Person, PhoneNumberType]:
    person_phone_id = tuple((person_id, phone_number, phone_number_type_id))
    try:
        updated_person_phone_id = person_phone_provider.update_person_phone(person_phone_id, person_phone_input)
        updated_person_phone = person_phone_provider.get_person_phone(updated_person_phone_id)
        return updated_person_phone
    except errors.NotFoundError as e:
        raise_404(e, "Person phone", person_phone_id)
    except errors.PydanticValidationError as e:
        raise_422(e)
    except errors.IntegrityError as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_person_phone/{person_id}/{phone_number}/{phone_number_type_id}", tags=["Person Phones"],
               responses=get_response_models(ResponseMessage, [200, 400, 401, 404, 500]))
def delete_person_phone(person_id: int, phone_number: str, phone_number_type_id: int,
                        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> ResponseMessage:
    person_phone_id = tuple((person_id, phone_number, phone_number_type_id))
    try:
        person_phone_provider.delete_person_phone(person_phone_id)
        return ResponseMessage(title="Person phone deleted.",
                               description=f"Person phone of given id {person_phone_id} deleted.",
                               code=status.HTTP_200_OK)
    except errors.NotFoundError as e:
        raise_404(e, "Person phone", person_phone_id)
    except Exception as e:
        raise_500(e)
