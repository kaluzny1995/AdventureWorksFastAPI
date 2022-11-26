from fastapi import APIRouter
from typing import Dict


router = APIRouter()


@router.get("/", include_in_schema=False)
@router.get("/hello", tags=["Hello FastAPI"])
def hello_fast_api() -> Dict[str, str]:
    return dict(message="Hello FastAPI!")
