import datetime as dt
from typing import List

from app.models import (AWFAPIUserInput, AWFAPIRegisteredUser, PersonInput, EPersonType,
                        PhoneNumberTypeInput, PersonPhoneInput, PersonPhone)


awfapi_users_db = [
    AWFAPIUserInput(username="dzhawaria", full_name="Dzhejkob Awaria", email="dzh.awaria@gmail.com",
                    is_readonly=False, hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6"),
    AWFAPIUserInput(username="testuser2", full_name="Test User 2", email="test.user2@test.user",
                    is_readonly=True, hashed_password="$2b$12$dQfVWYA0ko8tjyqglzHd4.2i9lY4x48Q08YsVSMWEIpPqXXTGRkwS"),
    AWFAPIUserInput(username="testuser22", full_name="Test User 22", email="test.user22@test.user",
                    is_readonly=True, hashed_password="$2b$12$Mvf8/LwNEue1qQrh.UUAruWnIOaIYgYIAQ3vtEqOYQg7/xlJ.XSB6")
]

awfapi_user: AWFAPIUserInput = AWFAPIUserInput(username="testuser", full_name="Test User",
                                               email="test.user@test.user", is_readonly=True,
                                               hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6")
awfapi_user2: AWFAPIUserInput = AWFAPIUserInput(username="testuser2", full_name="Test User 2",
                                                email="test.user2@test.user", is_readonly=True,
                                                hashed_password="$2b$12$1MPiN.NRShpEI/WzKmsPLemaT3d6paLBXi3t3KFBHFlyXUrKgixF6")

awfapi_nonreadonly_user: AWFAPIRegisteredUser = AWFAPIRegisteredUser(username="testuser", password="testpassword",
                                                                     repeated_password="testpassword",
                                                                     full_name="Test AWFAPIUserInput",
                                                                     email="test.user@test.user", is_readonly=False)
awfapi_nonreadonly_user2: AWFAPIRegisteredUser = AWFAPIRegisteredUser(username="testuser2", password="testpassword2",
                                                                      repeated_password="testpassword2",
                                                                      full_name="Test User 2",
                                                                      email="test.user2@test.user", is_readonly=False)
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
