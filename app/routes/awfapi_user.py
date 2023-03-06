from fastapi import APIRouter, Body
from typing import List

from app import errors
from app.models import UserInput, User, Message
from app.providers import AWFAPIUserProvider

from app.error_handlers import raise_404, raise_500


router = APIRouter()


@router.get("/all_awfapi_users", tags=["AWFAPI Users"],
            responses={200: {"model": List[User]}, 500: {"model": Message}})
def get_awfapi_users(offset: int = 0, limit: int = 10) -> List[User]:
    try:
        awfapi_user_provider = AWFAPIUserProvider()
        awfapi_users = awfapi_user_provider.get_awfapi_users(limit, offset)
        return awfapi_users
    except Exception as e:
        raise_500(e)


@router.get("/get_awfapi_user/{awfapi_user_username}", tags=["AWFAPI Users"],
            responses={200: {"model": User}, 404: {"model": Message}, 500: {"model": Message}})
def get_awfapi_user(awfapi_user_username: str) -> User:
    try:
        awfapi_user_provider = AWFAPIUserProvider()
        awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        return awfapi_user
    except errors.NotFoundError as e:
        raise_404(e, "AWFAPI User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.post("/create_awfapi_user", tags=["AWFAPI Users"],
             responses={201: {"model": User}, 500: {"model": Message}}, status_code=201)
def create_awfapi_user(
        awfapi_user_input: UserInput = Body(None, examples=UserInput.Config.schema_extra["examples"])) -> User:
    try:
        awfapi_user_provider = AWFAPIUserProvider()
        new_awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user_input)
        new_awfapi_user = awfapi_user_provider.get_awfapi_user(new_awfapi_user_username)
        return new_awfapi_user
    except Exception as e:
        raise_500(e)


@router.put("/update_awfapi_user/{awfapi_user_username}", tags=["AWFAPI Users"],
            responses={200: {"model": User}, 404: {"model": Message}, 500: {"model": Message}})
def update_awfapi_user(
        awfapi_user_username: str,
        awfapi_user_input: UserInput = Body(None, examples=UserInput.Config.schema_extra["examples"])) -> User:
    try:
        awfapi_user_provider = AWFAPIUserProvider()
        updated_awfapi_user_username = awfapi_user_provider.update_awfapi_user(awfapi_user_username, awfapi_user_input)
        updated_awfapi_user = awfapi_user_provider.get_awfapi_user(updated_awfapi_user_username)
        return updated_awfapi_user
    except errors.NotFoundError as e:
        raise_404(e, "AWFAPI User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_awfapi_user/{awfapi_user_username}", tags=["AWFAPI Users"],
               responses={200: {"model": Message}, 404: {"model": Message}, 500: {"model": Message}})
def delete_awfapi_user(awfapi_user_username: str) -> Message:
    try:
        awfapi_user_provider = AWFAPIUserProvider()
        awfapi_user_provider.delete_awfapi_user(awfapi_user_username)
        return Message(info="Person deleted", message=f"AWFAPI user of given username {awfapi_user_username} deleted.")
    except errors.NotFoundError as e:
        raise_404(e, "AWFAPI User", awfapi_user_username)
    except Exception as e:
        raise_500(e)