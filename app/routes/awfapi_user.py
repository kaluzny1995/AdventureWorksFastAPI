from fastapi import APIRouter, Body, Depends, status
from typing import List

from app import errors
from app.models import AWFAPIUserInput, AWFAPIUser,\
    AWFAPIViewedUser, AWFAPIRegisteredUser, AWFAPIChangedUserData, AWFAPIChangedUserCredentials,\
    ResponseMessage, get_response_models
from app.providers import AWFAPIUserProvider
from app.services import AWFAPIUserService

from app.oauth2_handlers import get_current_user, get_current_nonreadonly_user
from app.error_handlers import raise_400, raise_404, raise_500


router: APIRouter = APIRouter()

awfapi_user_provider: AWFAPIUserProvider = AWFAPIUserProvider()
awfapi_user_service: AWFAPIUserService = AWFAPIUserService()


@router.get("/all_awfapi_users", tags=["AWFAPI Users"],
            responses=get_response_models(List[AWFAPIUser], [200, 401, 500]), include_in_schema=False)
def get_awfapi_users(offset: int = 0, limit: int = 10,
                     _: AWFAPIUser = Depends(get_current_user)) -> List[AWFAPIUser]:
    try:
        awfapi_users = awfapi_user_provider.get_awfapi_users(limit, offset)
        return awfapi_users
    except Exception as e:
        raise_500(e)


@router.get("/get_awfapi_user/{awfapi_user_username}", tags=["AWFAPI Users"],
            responses=get_response_models(AWFAPIUser, [200, 401, 404, 500]), include_in_schema=False)
def get_awfapi_user(awfapi_user_username: str,
                    _: AWFAPIUser = Depends(get_current_user)) -> AWFAPIUser:
    try:
        awfapi_user = awfapi_user_provider.get_awfapi_user(awfapi_user_username)
        return awfapi_user
    except errors.NotFoundError as e:
        raise_404(e, "AWFAPI User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.post("/create_awfapi_user", tags=["AWFAPI Users"],
             responses=get_response_models(AWFAPIUser, [201, 400, 401, 500]),
             status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_awfapi_user(
        awfapi_user_input: AWFAPIUserInput = Body(None, examples=AWFAPIUserInput.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> AWFAPIUser:
    try:
        new_awfapi_user_username = awfapi_user_provider.insert_awfapi_user(awfapi_user_input)
        new_awfapi_user = awfapi_user_provider.get_awfapi_user(new_awfapi_user_username)
        return new_awfapi_user
    except (errors.UsernameAlreadyExistsError, errors.EmailAlreadyExistsError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.put("/update_awfapi_user/{awfapi_user_username}", tags=["AWFAPI Users"],
            responses=get_response_models(AWFAPIUser, [200, 400, 401, 404, 500]), include_in_schema=False)
def update_awfapi_user(
        awfapi_user_username: str,
        awfapi_user_input: AWFAPIUserInput = Body(None, examples=AWFAPIUserInput.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> AWFAPIUser:
    try:
        updated_awfapi_user_username = awfapi_user_provider.update_awfapi_user(awfapi_user_username, awfapi_user_input)
        updated_awfapi_user = awfapi_user_provider.get_awfapi_user(updated_awfapi_user_username)
        return updated_awfapi_user
    except (errors.UsernameAlreadyExistsError, errors.EmailAlreadyExistsError) as e:
        raise_400(e)
    except errors.NotFoundError as e:
        raise_404(e, "AWFAPI User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.delete("/delete_awfapi_user/{awfapi_user_username}", tags=["AWFAPI Users"],
               responses=get_response_models(ResponseMessage, [200, 400, 401, 404, 500]), include_in_schema=False)
def delete_awfapi_user(awfapi_user_username: str, _: AWFAPIUser = Depends(get_current_nonreadonly_user)) -> ResponseMessage:
    try:
        awfapi_user_provider.delete_awfapi_user(awfapi_user_username)
        return ResponseMessage(title="AWFAPI user deleted.",
                               description=f"AWFAPI user of given username '{awfapi_user_username}' deleted.",
                               code=status.HTTP_200_OK)
    except errors.NotFoundError as e:
        raise_404(e, "AWFAPI User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.get("/view_awfapi_user_profile/{awfapi_user_username}", tags=["AWFAPI Users"],
            responses=get_response_models(AWFAPIViewedUser, [200, 401, 404, 500]))
def view_awfapi_user_profile(awfapi_user_username: str,
                             _: AWFAPIUser = Depends(get_current_user)) -> AWFAPIViewedUser:
    try:
        return awfapi_user_service.view_awfapi_user(awfapi_user_username)
    except errors.NotFoundError as e:
        raise_404(e, "User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.post("/register_awfapi_user", tags=["AWFAPI Users"],
             responses=get_response_models(ResponseMessage, [201, 400, 500]), status_code=status.HTTP_201_CREATED)
def register_awfapi_user(
        awfapi_registered_user: AWFAPIRegisteredUser = Body(None, examples=AWFAPIRegisteredUser.Config.schema_extra["examples"])) -> ResponseMessage:
    try:
        new_awfapi_user_username = awfapi_user_service.register_awfapi_user(awfapi_registered_user)
        return ResponseMessage(title="User registered.",
                               description=f"New user '{new_awfapi_user_username}' registered.",
                               code=status.HTTP_201_CREATED)
    except (errors.UsernameAlreadyExistsError, errors.EmailAlreadyExistsError) as e:
        raise_400(e)
    except Exception as e:
        raise_500(e)


@router.put("/change_awfapi_user_data/{awfapi_user_username}", tags=["AWFAPI Users"],
            responses=get_response_models(ResponseMessage, [200, 400, 401, 404, 500]))
def change_awfapi_user_data(
        awfapi_user_username: str,
        awfapi_changed_user_data: AWFAPIChangedUserData = Body(None, examples=AWFAPIChangedUserData.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_user)) -> ResponseMessage:
    try:
        updated_awfapi_user_username = awfapi_user_service.change_awfapi_user_data(awfapi_user_username, awfapi_changed_user_data)
        return ResponseMessage(title="User data changed.",
                               description=f"Data of user '{updated_awfapi_user_username}' changed.",
                               code=status.HTTP_200_OK)
    except (errors.UsernameAlreadyExistsError, errors.EmailAlreadyExistsError, errors.InvalidCredentialsError) as e:
        raise_400(e)
    except errors.NotFoundError as e:
        raise_404(e, "User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.put("/change_awfapi_user_credentials/{awfapi_user_username}", tags=["AWFAPI Users"],
            responses=get_response_models(ResponseMessage, [200, 400, 401, 404, 500]))
def change_awfapi_user_credentials(
        awfapi_user_username: str,
        awfapi_changed_user_credentials: AWFAPIChangedUserCredentials = Body(None, examples=AWFAPIChangedUserCredentials.Config.schema_extra["examples"]),
        _: AWFAPIUser = Depends(get_current_user)) -> ResponseMessage:
    try:
        updated_awfapi_user_username = awfapi_user_service.change_awfapi_user_credentials(awfapi_user_username, awfapi_changed_user_credentials)
        return ResponseMessage(title="User credentials changed.",
                               description=f"Credentials of user '{updated_awfapi_user_username}' changed.",
                               code=status.HTTP_200_OK)
    except (errors.UsernameAlreadyExistsError, errors.EmailAlreadyExistsError, errors.InvalidCredentialsError) as e:
        raise_400(e)
    except errors.NotFoundError as e:
        raise_404(e, "User", awfapi_user_username)
    except Exception as e:
        raise_500(e)


@router.delete("/remove_awfapi_user_account/{awfapi_user_username}", tags=["AWFAPI Users"],
               responses=get_response_models(ResponseMessage, [200, 401, 404, 500]))
def remove_awfapi_user_account(awfapi_user_username: str, _: AWFAPIUser = Depends(get_current_user)) -> ResponseMessage:
    try:
        awfapi_user_service.remove_awfapi_user_account(awfapi_user_username)
        return ResponseMessage(title="Account removed.",
                               description=f"Account of user '{awfapi_user_username}' removed.",
                               code=status.HTTP_200_OK)
    except errors.NotFoundError as e:
        raise_404(e, "User", awfapi_user_username)
    except Exception as e:
        raise_500(e)
