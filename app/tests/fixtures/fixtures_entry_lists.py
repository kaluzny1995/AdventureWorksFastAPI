import datetime as dt
from typing import List

from app.models import AWFAPIRegisteredUser, PersonInput, EPersonType, PhoneNumberTypeInput, PersonPhoneInput, PersonPhone


awfapi_nonreadonly_user: AWFAPIRegisteredUser = AWFAPIRegisteredUser(username="testuser", password="testpassword",
                                                                     repeated_password="testpassword",
                                                                     full_name="Test AWFAPIUserInput",
                                                                     email="test.user@test.user", is_readonly=False)
awfapi_readonly_user: AWFAPIRegisteredUser = AWFAPIRegisteredUser(username="testuser", password="testpassword",
                                                                  repeated_password="testpassword",
                                                                  full_name="Test AWFAPIUserInput",
                                                                  email="test.user@test.user", is_readonly=True)

persons_db: List[PersonInput] = [
    PersonInput(person_type=EPersonType.GC, first_name="John", last_name="Doe"),
    PersonInput(person_type=EPersonType.EM, first_name="John", last_name="Smith"),
    PersonInput(person_type=EPersonType.IN, first_name="John", last_name="Adams"),
    PersonInput(person_type=EPersonType.VC, first_name="John", middle_name="K", last_name="Adams"),
    PersonInput(person_type=EPersonType.SP, first_name="John", middle_name="J", last_name="Adams"),
    PersonInput(person_type=EPersonType.GC, first_name="Brian", last_name="Washer"),
    PersonInput(person_type=EPersonType.SC, first_name="Aaron", last_name="Dasmi"),
    PersonInput(person_type=EPersonType.SC, first_name="Aaron", last_name="Washington"),
    PersonInput(person_type=EPersonType.SC, first_name="Sharon", last_name="Smith"),
    PersonInput(person_type=EPersonType.SC, first_name="Claire", last_name="Smith"),
]

phone_number_types_db: List[PhoneNumberTypeInput] = [
    PhoneNumberTypeInput(name="Cell"),
    PhoneNumberTypeInput(name="Mobile"),
    PhoneNumberTypeInput(name="Home"),
    PhoneNumberTypeInput(name="Home 2"),
    PhoneNumberTypeInput(name="Home em."),
]

person_phones_db: List[PersonPhoneInput] = [
    PersonPhoneInput(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1),
    PersonPhoneInput(business_entity_id=1, phone_number="666 666 666", phone_number_type_id=1),
    PersonPhoneInput(business_entity_id=1, phone_number="999 000 999", phone_number_type_id=2),
    PersonPhoneInput(business_entity_id=4, phone_number="123456789", phone_number_type_id=3),
    PersonPhoneInput(business_entity_id=5, phone_number="338 94 95", phone_number_type_id=3),
    PersonPhoneInput(business_entity_id=5, phone_number="8880 23453", phone_number_type_id=4),
    PersonPhoneInput(business_entity_id=7, phone_number="71 334 34 34", phone_number_type_id=3),
    PersonPhoneInput(business_entity_id=8, phone_number="000 000 000", phone_number_type_id=5),
]

person_phones: List[PersonPhone] = [
    PersonPhone(business_entity_id=1, phone_number="000 000 000", phone_number_type_id=1,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    PersonPhone(business_entity_id=1, phone_number="666 666 666", phone_number_type_id=1,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    PersonPhone(business_entity_id=1, phone_number="999 000 999", phone_number_type_id=2,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    PersonPhone(business_entity_id=4, phone_number="123456789", phone_number_type_id=3,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    PersonPhone(business_entity_id=5, phone_number="338 94 95", phone_number_type_id=3,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    PersonPhone(business_entity_id=5, phone_number="8880 23453", phone_number_type_id=4,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    PersonPhone(business_entity_id=7, phone_number="71 334 34 34", phone_number_type_id=3,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
    PersonPhone(business_entity_id=8, phone_number="000 000 000", phone_number_type_id=5,
                modified_date=dt.datetime(2020, 1, 1, 0, 0, 0)),
]
