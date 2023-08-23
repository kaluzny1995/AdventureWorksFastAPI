from typing import Optional, List

from app.models import PhoneNumberType, PhoneNumberTypeInput


class IPhoneNumberTypeProvider:
    """ Interface of phone number type provider """

    def get_phone_number_types(self, limit: Optional[int], offset: Optional[int]) -> List[PhoneNumberType]:
        """ Returns list of all phone number types """
        raise NotImplementedError

    def get_phone_number_type(self, phone_number_type_id: int) -> PhoneNumberType:
        """ Returns phone number type of given phone_number_type_id """
        raise NotImplementedError

    def insert_phone_number_type(self, phone_number_type_input: PhoneNumberTypeInput) -> int:
        """ Inserts phone number type and returns new phone number type phone_number_type_input """
        raise NotImplementedError

    def update_phone_number_type(self, phone_number_type_id: int, phone_number_type_input: PhoneNumberTypeInput) -> int:
        """ Updates person phone of given person_phone_id and returns updated person phone person_phone_id """
        raise NotImplementedError

    def delete_phone_number_type(self, phone_number_type_id: int) -> None:
        """ Deletes person phone of given person_phone_id """
        raise NotImplementedError
