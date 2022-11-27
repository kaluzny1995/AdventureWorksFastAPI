import re
import traceback
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from typing import Optional

from app import utils


def raise_400(e: Exception):
    """ Raises 400 when the entity insertion/update violated the certain db constraints """
    e_message = str(e)
    print(e_message)
    if "ForeignKeyViolation" in e_message:
        foreign_key_details = utils.get_foreign_key_violence_details(e_message)
        raise HTTPException(status_code=400,
                            detail={
                                "info": f"Related entity id does not exist",
                                "detail": f"Related entity {foreign_key_details['entity']} "
                                          f"has no entry of given id "
                                          f"{foreign_key_details['key_column']}=({foreign_key_details['key_value']})."
                            },
                            headers={"message": foreign_key_details['line']})
    else:
        raise e


def raise_404(e: Exception, entity: str, entity_id: object, info: Optional[str] = None, detail: Optional[str] = None):
    """ Raises 404 when entity of given id or criteria was not found """
    if info is not None and detail is not None:
        raise HTTPException(status_code=404, detail={"info": info, "detail": detail}, headers={"message": str(e)})
    else:
        raise HTTPException(status_code=404,
                            detail={
                                "info": f"{entity} not found",
                                "detail": f"{entity} of given id {entity_id} was not found."
                            },
                            headers={"message": str(e)})


def raise_500(e: Exception):
    """ Raises 500 when other unknown error occurred """
    raise HTTPException(status_code=500,
                        detail={
                            "info": "Internal error occurred.",
                            "detail": f"An internal error occurred: {str(e)}"
                        },
                        headers={"message": str(e)})


async def custom_http_error_handler(request: Request, exc: StarletteHTTPException):
    print(f"Error occurred. {str(exc)}")
    if exc.status_code == 400:
        print("The requested object violated certain constraints.")
    elif exc.status_code == 404:
        print("The requested object was not found.")
    else:
        print(traceback.format_exc())
    return await http_exception_handler(request, exc)


async def custom_request_validation_error_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error occurred. {str(exc)}")
    print(traceback.format_exc())
    return await request_validation_exception_handler(request, exc)
