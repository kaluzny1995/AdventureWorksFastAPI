import traceback
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from typing import Optional

from app import utils
from app.models import EAuthenticationStatus


def raise_400(e: Exception):
    """ Raises 400 when the request contains bad information:
    * non-unique value of the certain field was provided
    * current user has readonly restricted access
    * user typed wrong current password while changing credentials
    * entity insertion/update violated the certain db constraints
    """
    e_message = str(e)
    print(e_message)

    if "already exists" in e_message:
        unique_field, value = utils.get_unique_field_name_from_message(e_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "title": f"Field '{unique_field}' uniqueness",
                                "detail": f"Field '{unique_field}' must have unique values. "
                                          f"Provided value '{value}' already exists."
                            })

    elif "readonly" in e_message:
        username = utils.get_username_from_message(e_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "title": f"Readonly access for '{username}'",
                                "detail": e_message
                            })

    elif "current password" in e_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "title": e_message,
                                "detail": f"User provided {e_message.lower()}"
                            })

    elif "ForeignKeyViolation" in e_message:
        foreign_key_details = utils.get_foreign_key_violence_details(e_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "title": "Related entity id does not exist",
                                "detail": f"Related entity {foreign_key_details['entity']} "
                                          f"has no entry of given id "
                                          f"{foreign_key_details['key_column']}=({foreign_key_details['key_value']})."
                            },
                            headers={"description": foreign_key_details['line']})

    else:
        raise e


def raise_401(e: Exception):
    """ Raises 401 when user is not authorized, authentication failed or access token has expired """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(e),
        headers={"WWW-Authenticate": "Bearer"}
    )


def raise_404(e: Exception, entity: str, entity_id: object, info: Optional[str] = None, detail: Optional[str] = None):
    """ Raises 404 when entity of given id or criteria was not found """
    if info is not None and detail is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={
                                "title": info,
                                "detail": detail
                            },
                            headers={"description": str(e)})
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail={
                                "title": f"{entity} not found",
                                "detail": f"{entity} of given id {entity_id} was not found."
                            },
                            headers={"description": str(e)})


def raise_500(e: Exception):
    """ Raises 500 when other unknown error occurred """
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={
                            "title": "Internal error occurred.",
                            "detail": f"An internal error occurred: {str(e)}"
                        },
                        headers={"description": str(e)})


async def custom_http_error_handler(request: Request, exc: StarletteHTTPException):

    if request.url.path == "/test" and exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # executed only for "/test" url endpoint, which checks the authentication status
        # if oauth2_scheme fails (i.e. JWT token is empty), then returns "Unauthenticated" description
        return JSONResponse(status_code=200, content=dict(message=EAuthenticationStatus.UNAUTHENTICATED))

    print(f"Error occurred. {str(exc)}")
    if exc.status_code == status.HTTP_400_BAD_REQUEST:
        print("The request contains bad information.")
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        print("The user is not authorized, authentication failed or access token has expired.")
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        print("The requested object was not found.")
    else:
        print(traceback.format_exc())
    return await http_exception_handler(request, exc)


async def custom_request_validation_error_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error occurred. {str(exc)}")
    print(traceback.format_exc())
    return await request_validation_exception_handler(request, exc)
