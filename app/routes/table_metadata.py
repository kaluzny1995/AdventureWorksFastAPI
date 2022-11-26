from fastapi import APIRouter, HTTPException
from typing import Optional, List

from app import errors
from app.models import Message, TableMetadata
from app.providers import TableMetadataProvider


router = APIRouter()


@router.get("/table/names", tags=["Tables"], responses={200: {"model": List[str]}, 500: {"model": Message}})
def get_table_names() -> List[str]:
    try:
        table_metadata_provider = TableMetadataProvider()
        table_names = table_metadata_provider.get_table_names()
        return table_names
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})


@router.get("/table/metadatas", tags=["Tables"],
            responses={200: {"model": List[TableMetadata]}, 404: {"model": Message}, 500: {"model": Message}})
def get_table_metadatas(schema_name: Optional[str] = None, table_name: Optional[str] = None):
    try:
        table_metadata_provider = TableMetadataProvider()
        table_metadatas = table_metadata_provider.get_table_details(schema_name, table_name)
        return table_metadatas
    except errors.NotFoundError as e:
        raise HTTPException(status_code=404,
                            detail={
                                "info": "Tables not found",
                                "detail": f"No tables found for given criteria "
                                          f"(schema_name: {schema_name} | table_name: {table_name})."
                            },
                            headers={"message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail={
                                "info": "Internal error occurred.",
                                "detail": f"An internal error occurred: {str(e)}"
                            },
                            headers={"message": str(e)})
