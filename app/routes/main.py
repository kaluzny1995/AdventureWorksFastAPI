from fastapi import APIRouter, status

from app.models import ResponseMessage


router: APIRouter = APIRouter()


@router.get("/", include_in_schema=False)
@router.get("/hello", tags=["Hello FastAPI"], responses=dict({status.HTTP_200_OK: {"model": ResponseMessage}}))
def hello_fast_api() -> ResponseMessage:
    return ResponseMessage(title="Hello FastAPI", description="Successful response.", code=status.HTTP_200_OK)
