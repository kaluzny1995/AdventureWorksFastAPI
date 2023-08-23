from typing import Optional, List

from app.models import BusinessEntity


class IBusinessEntityProvider:
    """ Interface of business entity provider """

    def get_business_entities(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[BusinessEntity]:
        """ Returns list of all business entities """
        raise NotImplementedError

    def get_business_entity(self, business_entity_id: int) -> BusinessEntity:
        """ Returns business entity of given business_entity_id """
        raise NotImplementedError

    def insert_business_entity(self) -> int:
        """ Inserts business entity and returns new business entity business_entity_id """
        raise NotImplementedError

    # No update method, no mutable fields

    def delete_business_entity(self, business_entity_id: int) -> None:
        """ Deletes business entity of given business_entity_id """
        raise NotImplementedError
