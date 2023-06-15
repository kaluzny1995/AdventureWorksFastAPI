from fastapi import APIRouter, Body, Depends, status
from typing import List

from app import errors
from app.models import AWFAPIUser, PersonPhoneInput, PersonPhone, ResponseMessage, get_response_models
from app.providers import PersonPhoneProvider

from app.oauth2_handlers import get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_400, raise_404, raise_500


router = APIRouter()

person_phone_provider = PersonPhoneProvider()


@router.get("/all_person_phones", tags=["Person Phones"],
            responses=get_response_models(List[PersonPhone], [200, 400, 401, 500]))
def get_person_phones(offset: int = 0, limit: int = 10,
                      _: AWFAPIUser = Depends(get_current_user)) -> List[PersonPhone]:
    try:
        person_phones = person_phone_provider.get_person_phones(limit, offset)
        return person_phones
    except Exception as e:
        raise_500(e)


@router.get("/get_person_phone/{person_id}/{phone_number}/{phone_number_type_id}", tags=["Person Phones"],
            responses=get_response_models(PersonPhone, [200, 400, 401, 404, 500]))
def get_person_phone(person_id: int, phone_number: str, phone_number_type_id: int,
                     _: AWFAPIUser = Depends(get_current_user)) -> PersonPhone:
    person_phone_id = (person_id, phone_number, phone_number_type_id)
    try:
        person_phone = person_phone_provider.get_person_phone(person_phone_id)
        return person_phone
    except errors.NotFoundError as e:
        raise_404(e, "Person phone", person_phone_id)
    except Exception as e:
        raise_500(e)


@router.post("/create_person_phone", tags=["Person Phones"],
             responses=get_response_models(PersonPhone, [201, 400, 401, 500]), status_code=status.HTTP_201_CREATED)
def create_person_phone(person_phone_input: PersonPhoneInput = Body(...),
                        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> PersonPhone:
    try:
        new_person_phone_id = person_phone_provider.insert_person_phone(person_phone_input)
        new_person_phone = person_phone_provider.get_person_phone(new_person_phone_id)
        return new_person_phone
    except errors.IntegrityError as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.put("/update_person_phone/{person_id}/{phone_number}/{phone_number_type_id}", tags=["Person Phones"],
            responses=get_response_models(PersonPhone, [200, 400, 401, 404, 500]))
def update_person_phone(person_id: int, phone_number: str, phone_number_type_id: int,
                        person_phone_input: PersonPhoneInput = Body(...),
                        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> PersonPhone:
    person_phone_id = (person_id, phone_number, phone_number_type_id)
    try:
        updated_person_phone_id = person_phone_provider.update_person_phone(person_phone_id, person_phone_input)
        updated_person_phone = person_phone_provider.get_person_phone(updated_person_phone_id)
        return updated_person_phone
    except errors.NotFoundError as e:
        raise_404(e, "Person phone", person_phone_id)
    except errors.IntegrityError as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_person_phone/{person_id}/{phone_number}/{phone_number_type_id}", tags=["Person Phones"],
               responses=get_response_models(ResponseMessage, [200, 400, 401, 404, 500]))
def delete_person_phone(person_id: int, phone_number: str, phone_number_type_id: int,
                        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> ResponseMessage:
    person_phone_id = (person_id, phone_number, phone_number_type_id)
    try:
        person_phone_provider.delete_person_phone(person_phone_id)
        return ResponseMessage(title="Person phone deleted.",
                               description=f"Person phone of given id {person_phone_id} deleted.",
                               code=status.HTTP_200_OK)
    except errors.NotFoundError as e:
        raise_404(e, "Person phone", person_phone_id)
    except Exception as e:
        raise_500(e)
