from typing import Optional, List

from app.models import EOrderType, PhoneNumberTypeInput, PhoneNumberType
from app.providers import IPhoneNumberTypeProvider


class PhoneNumberTypeProviderStub(IPhoneNumberTypeProvider):

    def __init__(self, data: List[PhoneNumberType]):
        super(PhoneNumberTypeProviderStub, self).__init__()
        self.data = data

    def get_phone_number_types(self, filters: Optional[str] = None,
                               order_by: Optional[str] = None, order_type: Optional[EOrderType] = None,
                               limit: Optional[int] = None, offset: Optional[int] = None) -> List[PhoneNumberType]:
        """ Returns list of appropriate phone number types """
        return self.data

    def count_phone_number_types(self, filters: Optional[str] = None) -> int:
        """ Returns count of appropriate phone number types """
        return len(self.data)

    def get_phone_number_type(self, phone_number_type_id: int) -> PhoneNumberType:
        """ Returns phone number type of given phone_number_type_id """
        pass

    def insert_phone_number_type(self, phone_number_type_input: PhoneNumberTypeInput) -> int:
        """ Inserts phone number type and returns new phone number type phone_number_type_id """
        pass

    def update_phone_number_type(self, phone_number_type_id: int, phone_number_type_input: PhoneNumberTypeInput) -> int:
        """ Updates phone number type of given phone_number_type_id and returns updated phone number type phone_number_type_id """
        pass

    def delete_phone_number_type(self, phone_number_type_id: int) -> None:
        """ Deletes phone number type of given phone_number_type_id """
        pass
