from fastapi import APIRouter, Body, Depends, status
from typing import Optional, List

from app import errors
from app.config import DefaultQueryParamsConfig
from app.models import (EOrderType, AWFAPIUser, PhoneNumberTypeInput, PhoneNumberType,
                        CountMessage, ResponseMessage, get_response_models)
from app.providers import PhoneNumberTypeProvider

from app.oauth2_handlers import get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_400, raise_404, raise_422, raise_500


router: APIRouter = APIRouter()

default_params: DefaultQueryParamsConfig = DefaultQueryParamsConfig.from_json(entity="phone_number_type")
phone_number_type_provider: PhoneNumberTypeProvider = PhoneNumberTypeProvider()


@router.get("/get_phone_number_types", tags=["Phone Number Types"],
            responses=get_response_models(List[PhoneNumberType], [200, 400, 401, 500]))
def get_phone_number_types(filters: Optional[str] = default_params.filters,
                           order_by: Optional[str] = default_params.order_by,
                           order_type: Optional[EOrderType] = default_params.order_type,
                           offset: int = default_params.offset,
                           limit: int = default_params.limit,
                           _: AWFAPIUser = Depends(get_current_user)) -> List[PhoneNumberType]:
    if filters == "":
        filters = None
    if order_by == "":
        order_by = None

    try:
        phone_number_types = phone_number_type_provider.get_phone_number_types(filters, order_by, order_type,
                                                                               limit, offset)
        return phone_number_types
    except (errors.InvalidFilterStringError, errors.FilterNotFoundError,
            errors.ColumnNotFoundError, errors.InvalidSQLValueError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.get("/count_phone_number_types", tags=["Phone Number Types"],
            responses=get_response_models(CountMessage, [200, 400, 401, 500]))
def count_phone_number_types(filters: Optional[str] = default_params.filters,
                             _: AWFAPIUser = Depends(get_current_user)) -> CountMessage:
    if filters == "":
        filters = None
    try:
        phone_number_types_count = phone_number_type_provider.count_phone_number_types(filters)
        return CountMessage(entity="Phone number type", count=phone_number_types_count)
    except (errors.InvalidFilterStringError, errors.FilterNotFoundError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.get("/get_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
            responses=get_response_models(PhoneNumberType, [200, 400, 401, 404, 500]))
def get_phone_number_type(phone_number_type_id: int,
                          _: AWFAPIUser = Depends(get_current_user)) -> PhoneNumberType:
    try:
        phone_number_type = phone_number_type_provider.get_phone_number_type(phone_number_type_id)
        return phone_number_type
    except errors.NotFoundError as e:
        raise_404(e, "Phone number type", phone_number_type_id)
    except Exception as e:
        raise_500(e)


@router.post("/create_phone_number_type", tags=["Phone Number Types"],
             responses=get_response_models(PhoneNumberType, [201, 400, 401, 422, 500]),
             status_code=status.HTTP_201_CREATED)
def create_phone_number_type(
        phone_number_type_input: PhoneNumberTypeInput = Body(None, examples=PhoneNumberTypeInput.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> PhoneNumberType:
    try:
        new_phone_number_type_id = phone_number_type_provider.insert_phone_number_type(phone_number_type_input)
        new_phone_number_type = phone_number_type_provider.get_phone_number_type(new_phone_number_type_id)
        return new_phone_number_type
    except errors.PydanticValidationError as e:
        raise_422(e)
    except Exception as e:
        raise_500(e)


@router.put("/update_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
            responses=get_response_models(PhoneNumberType, [200, 400, 401, 404, 422, 500]))
def update_phone_number_type(phone_number_type_id: int,
                             phone_number_type_input: PhoneNumberTypeInput = Body(None, examples=PhoneNumberTypeInput.Config.schema_extra["examples"]),
                             _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> PhoneNumberType:
    try:
        updated_phone_number_type_id = phone_number_type_provider.update_phone_number_type(phone_number_type_id, phone_number_type_input)
        updated_phone_number = phone_number_type_provider.get_phone_number_type(updated_phone_number_type_id)
        return updated_phone_number
    except errors.NotFoundError as e:
        raise_404(e, "Phone number type", phone_number_type_id)
    except errors.PydanticValidationError as e:
        raise_422(e)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
               responses=get_response_models(ResponseMessage, [200, 400, 401, 404, 500]))
def delete_phone_number_type(phone_number_type_id: int,
                             _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> ResponseMessage:
    try:
        phone_number_type_provider.delete_phone_number_type(phone_number_type_id)
        return ResponseMessage(title="Phone number type deleted.",
                               description=f"Phone number type of given id '{phone_number_type_id}' deleted.",
                               code=status.HTTP_200_OK)
    except errors.NotFoundError as e:
        raise_404(e, "Phone number type", phone_number_type_id)
    except Exception as e:
        raise_500(e)
