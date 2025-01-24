import traceback
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from typing import Optional

from app import utils
from app.models import EAuthenticationStatus, ResponseMessage, E401Unauthorized, E400BadRequest


def raise_400(e: Exception):
    """ Raises 400 when the request contains bad information:
    * non-unique value of the certain field was provided
    * a certain value is invalid for certain SQL clause (ex. LIMIT -1 or SKIP -1)
    * current user has readonly restricted access
    * user typed wrong current password while changing credentials
    * entity insertion/update violated the certain db constraints
    * object filter string is invalid or contains non-existing filtering fields
    * related fields have empty values (ex. at least one of them must be provided)
    """
    e_message = str(e)
    e_400_code = E400BadRequest(e_message[:8])

    if e_400_code == E400BadRequest.UNIQUE_CONSTRAINT_VIOLATION:
        field, value = utils.get_unique_field_details_from_message(e_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title=f"Unique constraint violation. "
                                                         f"Value '{value}' for field '{field}' already exists.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Unique constraint violation."})

    elif e_400_code == E400BadRequest.INVALID_SQL_VALUE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Invalid value for SQL clause.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Invalid value for SQL clause."})

    elif e_400_code == E400BadRequest.READONLY_ACCESS_FOR_USER:
        username = utils.get_username_from_message(e_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title=f"Readonly access for '{username}'.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Attempt of readonly access violation."})

    elif e_400_code == E400BadRequest.WRONG_CURRENT_PASSWORD:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title=f"Wrong current password.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Wrong current password."})

    elif e_400_code == E400BadRequest.PRIMARY_KEY_CONSTRAINT_VIOLATION:
        primary_key_details = utils.get_primary_key_violence_details(e_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Primary key constraint violation. "
                                                         f"Primary key '{primary_key_details.key_column}'="
                                                         f"({primary_key_details.key_value}) already exists.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Primary key constraint violation."})

    elif e_400_code == E400BadRequest.FOREIGN_KEY_CONSTRAINT_VIOLATION:
        foreign_key_details = utils.get_foreign_key_violence_details(e_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Foreign key constraint violation. "
                                                         f"Entity '{foreign_key_details.entity}' with "
                                                         f"'{foreign_key_details.key_column}'="
                                                         f"({foreign_key_details.key_value}) does not exist.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Foreign key constraint violation."})

    elif e_400_code == E400BadRequest.INVALID_FILTER_STRING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Invalid filter string.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Invalid filter string."})

    elif e_400_code == E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Non-existing fields in filter string.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Non-existing fields in filter string."})

    elif e_400_code == E400BadRequest.VALUES_NOT_PROVIDED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Missing values.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Missing values."})

    elif e_400_code == E400BadRequest.INVALID_ORDERING_COLUMN_NAME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Non-existing column for ordering.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Non-existing column for ordering."})

    elif e_400_code == E400BadRequest.ORDERING_NOT_SUPPORTED_FOR_COLUMN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Unsupported ordering for this data type.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Unsupported ordering for this data type."})

    elif e_400_code == E400BadRequest.EXISTING_DEPENDENT_ENTITY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=ResponseMessage(title="Existing dependent entity.",
                                                   description=e_message,
                                                   code=status.HTTP_400_BAD_REQUEST).dict(),
                            headers={"description": "Existing dependent entity."})

    else:
        raise_500(e)


def raise_401(e: Exception):
    """ Raises 401 when user is not authorized, authentication failed or access token has expired """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ResponseMessage(title="Not authorized.",
                               description=str(e),
                               code=status.HTTP_401_UNAUTHORIZED).dict(),
        headers={"description": "Not authorized."}
    )


def raise_404(e: Exception, entity: str, entity_id: object, info: Optional[str] = None, detail: Optional[str] = None):
    """ Raises 404 when entity of given id or criteria was not found """
    if info is not None and detail is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=ResponseMessage(title=f"{info} | {detail}",
                                                   description=str(e),
                                                   code=status.HTTP_404_NOT_FOUND).dict(),
                            headers={"description": "Entity not found."})
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=ResponseMessage(title=f"Entity '{entity}' of id '{entity_id}' not found.",
                                                   description=str(e),
                                                   code=status.HTTP_404_NOT_FOUND).dict(),
                            headers={"description": "Entity not found."})


def raise_422(e: Exception):
    """ Raises 422 when validation error occur during pydantic object creation """
    title, details = utils.get_validation_error_details_from_message(str(e), is_required_skipped=True)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=ResponseMessage(title=f"Pydantic validation error: {title} | {details}",
                                               description=str(e),
                                               code=status.HTTP_422_UNPROCESSABLE_ENTITY).dict(),
                        headers={"description": "Pydantic validation error."})


def raise_500(e: Exception):
    """ Raises 500 when other unknown error occurred """
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=ResponseMessage(title="Internal error occurred.",
                                               description=f"An internal error occurred: {str(e)}",
                                               code=status.HTTP_500_INTERNAL_SERVER_ERROR).dict(),
                        headers={"description": "Internal error occurred."})


async def custom_http_error_handler(request: Request, exc: StarletteHTTPException) -> Response:
    """ Handles each HTTP exception """
    if "//" in utils.get_endpoint_url_param_string(request.url.path) and exc.detail == "Not Found":
        # executed if user provides empty string in a positional endpoint parameter
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content=ResponseMessage(
                                title="Empty string in positional parameter.",
                                description=f"{E400BadRequest.EMPTY_STRING_IN_PARAMETER}: "
                                            f"Each of the positional endpoint parameters cannot be empty string.",
                                code=status.HTTP_400_BAD_REQUEST
                            ).dict())

    if request.url.path == "/test" and exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # executed only for "/test" url endpoint, which checks the authentication status
        # if oauth2_scheme fails (i.e. JWT token is empty), then returns "Unauthenticated" description
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=ResponseMessage(
                                title=EAuthenticationStatus.UNAUTHENTICATED,
                                description=f"Users authentication status: {EAuthenticationStatus.UNAUTHENTICATED}.",
                                code=status.HTTP_200_OK
                            ).dict())

    if exc.headers.get("WWW-Authenticate", None) is not None:
        # executed if oauth2_scheme fails (i.e. JWT token is empty) and then returns 401 response
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content=ResponseMessage(
                                title="JWT token not provided or wrong encoded.",
                                description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                            f"User did not provide or the JWT token is wrongly encoded.",
                                code=status.HTTP_401_UNAUTHORIZED
                            ).dict())

    print(f"Error occurred. {str(exc)}")
    if exc.status_code == status.HTTP_400_BAD_REQUEST:
        print("The request contains bad information.")
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        print("The user is not authorized, authentication failed or access token has expired.")
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        print("The requested object was not found.")
    elif exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        print("The validation of an object failed.")
    else:
        print(traceback.format_exc())
    return await http_exception_handler(request, exc)


async def custom_request_validation_error_handler(request: Request, exc: RequestValidationError) -> Response:
    """ Handles each validation error occurring during request sending"""
    print(f"Request validation error occurred.\n{str(exc)}")
    return await request_validation_exception_handler(request, exc)
