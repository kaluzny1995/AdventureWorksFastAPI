import traceback
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from typing import Optional


def raise_404(e: Exception, entity: str, entity_id: object, info: Optional[str] = None, detail: Optional[str] = None):
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
    raise HTTPException(status_code=500,
                        detail={
                            "info": "Internal error occurred.",
                            "detail": f"An internal error occurred: {str(e)}"
                        },
                        headers={"message": str(e)})


async def custom_http_error_handler(request: Request, exc: StarletteHTTPException):
    print(f"Error occured. {str(exc)}")
    if exc.status_code == 404:
        print("The requested object was not found.")
    else:
        print(traceback.format_exc())
    return await http_exception_handler(request, exc)


async def custom_request_validation_error_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error occured. {str(exc)}")
    print(traceback.format_exc())
    return await request_validation_exception_handler(request, exc)
