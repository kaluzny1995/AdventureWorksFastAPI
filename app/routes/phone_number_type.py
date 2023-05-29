from fastapi import APIRouter, Body, Depends, status
from typing import List

from app import errors
from app.models import AWFAPIUser, PhoneNumberTypeInput, PhoneNumberType, Message, get_response_models
from app.providers import PhoneNumberTypeProvider

from app.oauth2_handlers import get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_404, raise_500


router = APIRouter()


@router.get("/all_phone_number_types", tags=["Phone Number Types"],
            responses=get_response_models(List[PhoneNumberType], [200, 400, 401, 500]))
def get_phone_number_types(offset: int = 0, limit: int = 10,
                           _: AWFAPIUser = Depends(get_current_user)) -> List[PhoneNumberType]:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        phone_number_types = phone_number_type_provider.get_phone_number_types(limit, offset)
        return phone_number_types
    except Exception as e:
        raise_500(e)


@router.get("/get_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
            responses=get_response_models(PhoneNumberType, [200, 400, 401, 404, 500]))
def get_phone_number_type(phone_number_type_id: int,
                          _: AWFAPIUser = Depends(get_current_user)) -> PhoneNumberType:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        phone_number_type = phone_number_type_provider.get_phone_number_type(phone_number_type_id)
        return phone_number_type
    except errors.NotFoundError as e:
        raise_404(e, "Phone number type", phone_number_type_id)
    except Exception as e:
        raise_500(e)


@router.post("/create_phone_number_type", tags=["Phone Number Types"],
             responses=get_response_models(PhoneNumberType, [201, 400, 401, 500]), status_code=status.HTTP_201_CREATED)
def create_phone_number_type(phone_number_type_input: PhoneNumberTypeInput = Body(...),
                             _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> PhoneNumberType:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        new_phone_number_type_id = phone_number_type_provider.insert_phone_number_type(phone_number_type_input)
        new_phone_number_type = phone_number_type_provider.get_phone_number_type(new_phone_number_type_id)
        return new_phone_number_type
    except Exception as e:
        raise_500(e)


@router.put("/update_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
            responses=get_response_models(PhoneNumberType, [200, 400, 401, 404, 500]))
def update_phone_number_type(phone_number_type_id: int,
                             phone_number_type_input: PhoneNumberTypeInput = Body(...),
                             _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> PhoneNumberType:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        updated_phone_number_type_id = phone_number_type_provider.update_phone_number_type(phone_number_type_id,
                                                                                           phone_number_type_input)
        updated_phone_number_type = phone_number_type_provider.get_phone_number_type(updated_phone_number_type_id)
        return updated_phone_number_type
    except errors.NotFoundError as e:
        raise_404(e, "Phone number type", phone_number_type_id)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
               responses=get_response_models(Message, [200, 400, 401, 404, 500]))
def delete_phone_number_type(phone_number_type_id: int,
                             _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Message:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        phone_number_type_provider.delete_phone_number_type(phone_number_type_id)
        return Message(info="Phone number type deleted",
                       message=f"Phone number type of given id {phone_number_type_id} deleted.")
    except errors.NotFoundError as e:
        raise_404(e, "Phone number type", phone_number_type_id)
    except Exception as e:
        raise_500(e)
