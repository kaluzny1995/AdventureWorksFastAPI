from fastapi import APIRouter, Body, Depends, status
from typing import Optional, List

from app import errors
from app.config import DefaultParamsConfig
from app.models import EOrderType, AWFAPIUser, PersonInput, Person, CountMessage, ResponseMessage, get_response_models
from app.providers import PersonProvider
from app.services import PersonService

from app.oauth2_handlers import get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_400, raise_404, raise_422, raise_500


router = APIRouter()

default_params = DefaultParamsConfig.from_json(entity="person")
person_provider = PersonProvider()
person_service = PersonService()


@router.get("/get_persons", tags=["Persons"],
            responses=get_response_models(List[Person], [200, 400, 401, 500]))
def get_persons(filters: Optional[str] = default_params.filters,
                order_by: Optional[str] = default_params.order_by,
                order_type: Optional[EOrderType] = default_params.order_type,
                offset: int = default_params.offset,
                limit: int = default_params.limit,
                _: AWFAPIUser = Depends(get_current_user)) -> List[Person]:
    if filters == "":
        filters = None
    if order_by == "":
        order_by = None

    try:
        persons = person_provider.get_persons(filters, order_by, order_type, limit, offset)
        return persons
    except (errors.InvalidFilterStringError, errors.FilterNotFoundError,
            errors.ColumnNotFoundError, errors.InvalidSQLValueError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.get("/count_persons", tags=["Persons"],
            responses=get_response_models(List[Person], [200, 400, 401, 500]))
def count_persons(filters: Optional[str] = default_params.filters,
                  _: AWFAPIUser = Depends(get_current_user)) -> CountMessage:
    if filters == "":
        filters = None
    try:
        persons_count = person_provider.count_persons(filters)
        return CountMessage(entity="Person", count=persons_count)
    except (errors.InvalidFilterStringError, errors.FilterNotFoundError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.get("/get_person/{person_id}", tags=["Persons"],
            responses=get_response_models(Person, [200, 401, 404, 500]))
def get_person(person_id: int,
               _: AWFAPIUser = Depends(get_current_user)) -> Person:
    try:
        person = person_provider.get_person(person_id)
        return person
    except errors.NotFoundError as e:
        raise_404(e, "Person", person_id)
    except Exception as e:
        raise_500(e)


@router.post("/create_person", tags=["Persons"],
             responses=get_response_models(Person, [201, 400, 401, 422, 500]), status_code=status.HTTP_201_CREATED)
def create_person(
        person_input: PersonInput = Body(None, examples=PersonInput.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Person:
    try:
        new_person_id = person_provider.insert_person(person_input)
        new_person = person_provider.get_person(new_person_id)
        return new_person
    except errors.PydanticValidationError as e:
        raise_422(e)
    except Exception as e:
        raise_500(e)


@router.put("/update_person/{person_id}", tags=["Persons"],
            responses=get_response_models(Person, [200, 400, 401, 404, 422, 500]))
def update_person(person_id: int,
                  person_input: PersonInput = Body(None, examples=PersonInput.Config.schema_extra["examples"]),
                  _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> Person:
    try:
        updated_person_id = person_provider.update_person(person_id, person_input)
        updated_person = person_provider.get_person(updated_person_id)
        return updated_person
    except errors.NotFoundError as e:
        raise_404(e, "Person", person_id)
    except errors.PydanticValidationError as e:
        raise_422(e)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_person/{person_id}", tags=["Persons"],
               responses=get_response_models(ResponseMessage, [200, 400, 401, 404, 500]))
def delete_person(person_id: int,
                  _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> ResponseMessage:
    try:
        person_provider.delete_person(person_id)
        return ResponseMessage(title="Person deleted.",
                               description=f"Person of given id '{person_id}' deleted.",
                               code=status.HTTP_200_OK)
    except errors.NotFoundError as e:
        raise_404(e, "Person", person_id)
    except Exception as e:
        raise_500(e)


@router.get("/search_by_phrases", tags=["Persons"],
            responses=get_response_models(List[Person], [200, 400, 404, 500]))
def search_by_phrases(first_name_phrase: Optional[str] = None,
                      last_name_phrase: Optional[str] = None,
                      is_ordered: Optional[bool] = True) -> List[Person]:
    if first_name_phrase == "":
        first_name_phrase = None
    if last_name_phrase == "":
        last_name_phrase = None
    try:
        persons = person_service.get_persons_by_phrases(first_name_phrase, last_name_phrase, is_ordered)
        return persons
    except errors.EmptyFieldsError as e:
        raise_400(e)
    except errors.NotFoundError as e:
        raise_404(e, "Persons", "all",
                  info="Persons not found",
                  detail=f"No persons found for given phrases"
                         f"(first_name_phrase: {first_name_phrase} | last_name_phrase: {last_name_phrase}).")
    except Exception as e:
        raise_500(e)
