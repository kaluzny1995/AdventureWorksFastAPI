from fastapi import APIRouter, Body, HTTPException
from typing import List

from app import errors
from app.models import PhoneNumberTypeInput, PhoneNumberType, Message
from app.providers import PhoneNumberTypeProvider

router = APIRouter()


@router.get("/all_phone_number_types", tags=["Phone Number Types"],
            responses={200: {"model": List[PhoneNumberType]}, 500: {"model": Message}})
def get_phone_number_types(offset: int = 0, limit: int = 10) -> List[PhoneNumberType]:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        phone_number_types = phone_number_type_provider.get_phone_number_types(limit, offset)
        return phone_number_types
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.get("/get_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
            responses={200: {"model": PhoneNumberType}, 404: {"model": Message}, 500: {"model": Message}})
def get_phone_number_type(phone_number_type_id: int) -> PhoneNumberType:
    phone_number_type_provider = PhoneNumberTypeProvider()
    try:
        phone_number_type = phone_number_type_provider.get_phone_number_type(phone_number_type_id)
        return phone_number_type
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404,
                            detail={
                                "info": "Phone number type not found",
                                "detail": f"Phone number type of given id {phone_number_type_id} was not found."
                            },
                            headers={"message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.post("/create_phone_number_type", tags=["Phone Number Types"],
             responses={201: {"model": PhoneNumberType}, 500: {"model": Message}}, status_code=201)
def create_phone_number_type(phone_number_type_input: PhoneNumberTypeInput = Body(...)) -> PhoneNumberType:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        new_phone_number_type_id = phone_number_type_provider.insert_phone_number_type(phone_number_type_input)
        new_phone_number_type = phone_number_type_provider.get_phone_number_type(new_phone_number_type_id)
        return new_phone_number_type
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.put("/update_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
            responses={200: {"model": PhoneNumberType}, 404: {"model": Message}, 500: {"model": Message}})
def update_phone_number_type(phone_number_type_id: int,
                             phone_number_type_input: PhoneNumberTypeInput = Body(...)) -> PhoneNumberType:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        updated_phone_number_type_id = phone_number_type_provider.update_phone_number_type(phone_number_type_id,
                                                                                           phone_number_type_input)
        updated_phone_number_type = phone_number_type_provider.get_phone_number_type(updated_phone_number_type_id)
        return updated_phone_number_type
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404,
                            detail={
                                "info": "Phone number type not found",
                                "detail": f"Phone number type of given id {phone_number_type_id} was not found."
                            },
                            headers={"message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.delete("/delete_phone_number_type/{phone_number_type_id}", tags=["Phone Number Types"],
               responses={200: {"model": Message}, 404: {"model": Message}, 500: {"model": Message}})
def delete_phone_number_type(phone_number_type_id: int) -> Message:
    try:
        phone_number_type_provider = PhoneNumberTypeProvider()
        phone_number_type_provider.delete_phone_number_type(phone_number_type_id)
        return Message(info="Phone number type deleted",
                       message=f"Phone number type of given id {phone_number_type_id} deleted.")
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404,
                            detail={
                                "info": "Phone number type not found",
                                "detail": f"Phone number type of given id {phone_number_type_id} was not found."
                            },
                            headers={"message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})
