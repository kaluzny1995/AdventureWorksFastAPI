from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, StarletteHTTPException

from app.routes import main_router, table_router, person_router, phone_number_type_router, person_phone_router
from app.error_handlers import custom_http_error_handler, custom_request_validation_error_handler


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)
app.include_router(table_router)
app.include_router(person_router)
app.include_router(phone_number_type_router)
app.include_router(person_phone_router)

app.add_exception_handler(StarletteHTTPException, custom_http_error_handler)
app.add_exception_handler(RequestValidationError, custom_request_validation_error_handler)
