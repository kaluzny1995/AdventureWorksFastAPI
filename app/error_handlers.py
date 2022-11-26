import traceback
from fastapi import Request
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler


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
