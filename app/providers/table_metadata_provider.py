from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from typing import Optional, List

from app import errors
from app.config import PostgresdbConnectionConfig
from app.models import TableMetadata


class TableMetadataProvider:
    connection_string: str = PostgresdbConnectionConfig.get_db_connection_string()
    excluded_schema_names: List[str] = ["'public'", "'topology'", "'pg_catalog'", "'information_schema'"]
    db_engine = create_engine(connection_string)

    def get_table_names(self) -> List[str]:
        fields = ["table_schema", "table_name"]
        statement = text(
            f"SELECT DISTINCT {', '.join(fields)} "
            f"FROM information_schema.columns "
            f"WHERE table_catalog = 'postgres' AND table_schema NOT IN ({', '.join(self.excluded_schema_names)}) "
            f"ORDER BY table_schema, table_name ASC;"
        )
        with Session(self.db_engine) as db_session:
            db_results = db_session.execute(statement)
            table_names = list(map(lambda dbr: f"{dbr[0]}.{dbr[1]}", db_results))
        return table_names

    def get_table_details(self, schema_name: Optional[str], table_name: Optional[str]) -> List[TableMetadata]:
        fields = list(TableMetadata.__fields__.keys())
        apo = "'"
        statement = text(
            f"SELECT DISTINCT {', '.join(fields)} "
            f"FROM information_schema.columns "
            f"WHERE table_catalog = 'postgres' AND table_schema NOT IN ({', '.join(self.excluded_schema_names)}) "
            f"{f'AND table_schema={apo}{schema_name}{apo} ' if schema_name is not None else ''}"
            f"{f'AND table_name={apo}{table_name}{apo} ' if table_name is not None else ''}"
            f"ORDER BY table_schema, table_name, ordinal_position ASC;"
        )
        with Session(self.db_engine) as db_session:
            db_results = db_session.execute(statement)
            table_metadatas = list(map(lambda dbr: TableMetadata(**dict(zip(fields, dbr))), db_results))
            if len(table_metadatas) == 0:
                raise errors.NotFoundError(f"No tables found for given criteria "
                                           f"(schema_name: {schema_name} | table_name: {table_name}).")
        return table_metadatas
