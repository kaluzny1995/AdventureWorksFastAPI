from fastapi import APIRouter
from typing import Optional, List

from app import errors
from app.models import Message, TableMetadata
from app.providers import TableMetadataProvider

from app.error_handlers import raise_404, raise_500


router = APIRouter()


@router.get("/table/names", tags=["Tables"], responses={200: {"model": List[str]}, 500: {"model": Message}})
def get_table_names() -> List[str]:
    try:
        table_metadata_provider = TableMetadataProvider()
        table_names = table_metadata_provider.get_table_names()
        return table_names
    except Exception as e:
        raise_500(e)


@router.get("/table/metadatas", tags=["Tables"],
            responses={200: {"model": List[TableMetadata]}, 404: {"model": Message}, 500: {"model": Message}})
def get_table_metadatas(schema_name: Optional[str] = None, table_name: Optional[str] = None):
    try:
        table_metadata_provider = TableMetadataProvider()
        table_metadatas = table_metadata_provider.get_table_details(schema_name, table_name)
        return table_metadatas
    except errors.NotFoundError as e:
        raise_404(e, "Tables", "all",
                  info="Tables not found",
                  detail=f"No tables found for given criteria "
                         f"(schema_name: {schema_name} | table_name: {table_name}).")
    except Exception as e:
        raise_500(e)
