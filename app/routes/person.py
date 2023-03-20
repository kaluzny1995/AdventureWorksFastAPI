from fastapi import APIRouter, Body, Depends, status
from typing import Optional, List

from app import errors
from app.models import AWFAPIUser, PersonInput, Person, Message, get_response_models
from app.providers import PersonProvider
from app.services import PersonService

from app.oauth2_handlers import get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_404, raise_500


router = APIRouter()


@router.get("/all_persons", tags=["Persons"],
            responses=get_response_models(List[Person], [200, 400, 401, 500]))
def get_persons(offset: int = 0, limit: int = 10,
                _: AWFAPIUser = Depends(get_current_user)) -> List[Person]:
    try:
        person_provider = PersonProvider()
        persons = person_provider.get_persons(limit, offset)
        return persons
    except Exception as e:
        raise_500(e)


@router.get("/get_person/{person_id}", tags=["Persons"],
            responses=get_response_models(Person, [200, 400, 401, 404, 500]))
def get_person(person_id: int,
               _: AWFAPIUser = Depends(get_current_user)) -> Person:
    try:
        person_provider = PersonProvider()
        person = person_provider.get_person(person_id)
        return person
    except errors.NotFoundError as e:
        raise_404(e, "Person", person_id)
    except Exception as e:
        raise_500(e)


@router.post("/create_person", tags=["Persons"],
             responses=get_response_models(Person, [201, 400, 401, 500]), status_code=status.HTTP_201_CREATED)
def create_person(
        person_input: PersonInput = Body(None, examples=PersonInput.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Person:
    try:
        person_provider = PersonProvider()
        new_person_id = person_provider.insert_person(person_input)
        new_person = person_provider.get_person(new_person_id)
        return new_person
    except Exception as e:
        raise_500(e)


@router.put("/update_person/{person_id}", tags=["Persons"],
            responses=get_response_models(Person, [200, 400, 401, 404, 500]))
def update_person(person_id: int,
                  person_input: PersonInput = Body(None, examples=PersonInput.Config.schema_extra["examples"]),
                  _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Person:
    try:
        person_provider = PersonProvider()
        updated_person_id = person_provider.update_person(person_id, person_input)
        updated_person = person_provider.get_person(updated_person_id)
        return updated_person
    except errors.NotFoundError as e:
        raise_404(e, "Person", person_id)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_person/{person_id}", tags=["Persons"],
               responses=get_response_models(Message, [200, 400, 401, 404, 500]))
def delete_person(person_id: int,
                  _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Message:
    try:
        person_provider = PersonProvider()
        person_provider.delete_person(person_id)
        return Message(info="Person deleted", message=f"Person of given id {person_id} deleted.")
    except errors.NotFoundError as e:
        raise_404(e, "Person", person_id)
    except Exception as e:
        raise_500(e)


@router.get("/search_by_phrases", tags=["Persons"],
            responses=get_response_models(List[Person], [200, 404, 500]))
def search_by_phrases(first_name_phrase: Optional[str] = None, last_name_phrase: Optional[str] = None):
    try:
        person_service = PersonService()
        persons = person_service.get_persons_by_phrases(first_name_phrase, last_name_phrase)
        return persons
    except errors.EmptyFieldsError as e:
        raise_404(e, "Persons", "all",
                  info="No phrases provided",
                  detail=f"Searching impossible. Provide a phrase for first and/or last name.")
    except errors.NotFoundError as e:
        raise_404(e, "Persons", "all",
                  info="Persons not found",
                  detail=f"No persons found for given phrases"
                         f"(first_name_phrase: {first_name_phrase} | last_name_phrase: {last_name_phrase}).")
    except Exception as e:
        raise_500(e)
