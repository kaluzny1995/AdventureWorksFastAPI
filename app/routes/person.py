from fastapi import APIRouter, Body, HTTPException
from typing import List

from app import errors
from app.models import PersonInput, Person, Message
from app.providers import PersonProvider

router = APIRouter()


@router.get("/all_persons", tags=["Persons"], responses={200: {"model": List[Person]}, 500: {"model": Message}})
def get_persons(offset: int = 0, limit: int = 10) -> List[Person]:
    try:
        person_provider = PersonProvider()
        persons = person_provider.get_persons(limit, offset)
        return persons
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.get("/get_person/{person_id}", tags=["Persons"],
            responses={200: {"model": Person}, 404: {"model": Message}, 500: {"model": Message}})
def get_person(person_id: int) -> Person:
    person_provider = PersonProvider()
    try:
        person = person_provider.get_person(person_id)
        return person
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404,
                            detail={
                                "info": "Person not found",
                                "detail": f"Person of given id {person_id} was not found."
                            },
                            headers={"message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.post("/create_person", tags=["Persons"],
             responses={201: {"model": Person}, 500: {"model": Message}}, status_code=201)
def create_person(
        person_input: PersonInput = Body(None, examples=PersonInput.Config.schema_extra["examples"])) -> Person:
    try:
        person_provider = PersonProvider()
        new_person_id = person_provider.insert_person(person_input)
        new_person = person_provider.get_person(new_person_id)
        return new_person
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.put("/update_person/{person_id}", tags=["Persons"],
            responses={200: {"model": Person}, 404: {"model": Message}, 500: {"model": Message}})
def update_person(person_id: int,
                  person_input: PersonInput = Body(None,
                                                   examples=PersonInput.Config.schema_extra["examples"])) -> Person:
    try:
        person_provider = PersonProvider()
        updated_person_id = person_provider.update_person(person_id, person_input)
        updated_person = person_provider.get_person(updated_person_id)
        return updated_person
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404,
                            detail={
                                "info": "Person not found",
                                "detail": f"Person of given id {person_id} was not found."
                            },
                            headers={"message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.delete("/delete_person/{person_id}", tags=["Persons"],
               responses={200: {"model": Message}, 404: {"model": Message}, 500: {"model": Message}})
def delete_person(person_id: int) -> Message:
    try:
        person_provider = PersonProvider()
        person_provider.delete_person(person_id)
        return Message(info="Person deleted", message=f"Person of given id {person_id} deleted.")
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404,
                            detail={
                                "info": "Person not found",
                                "detail": f"Person of given id {person_id} was not found."
                            },
                            headers={"message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})
