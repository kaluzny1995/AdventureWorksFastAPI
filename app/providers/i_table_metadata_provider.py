from typing import Optional, List

from app.models import TableMetadata


class ITableMetadataProvider:
    """ Interface of person provider """

    def get_table_names(self) -> List[str]:
        """ Returns list of all table names """
        raise NotImplementedError

    def get_table_details(self, schema_name: Optional[str], table_name: Optional[str]) -> List[TableMetadata]:
        """ Returns list of table details filtered by its schema and table name """
        raise NotImplementedError
