import pytest
from typing import Optional, List
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIRegisteredUser, EOrderType, PersonPhoneInput, PersonPhone,
                        E400BadRequest, E401Unauthorized)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PersonPhoneFactory)

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person_phone as person_phone_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user, person_phones_db
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token,
                                               insert_test_persons, insert_test_phone_number_types,
                                               insert_test_person_phones,
                                               create_tables, drop_tables, drop_collection)


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)

postgresdb_connection_string, postgresdb_engine = PostgresDBFactory.get_db_connection_details(test_suffix="_test")
person_phone_provider = PersonPhoneFactory.get_provider(postgresdb_connection_string, postgresdb_engine)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def fixtures_before_test(monkeypatch: MonkeyPatch) -> None:
    create_tables(postgresdb_engine)

    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
    monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
    monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

    monkeypatch.setattr(person_phone_routes, 'person_phone_provider', person_phone_provider)

    insert_test_persons(postgresdb_engine, postgresdb_connection_string)
    insert_test_phone_number_types(postgresdb_engine, postgresdb_connection_string)
    insert_test_person_phones(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)
    drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, filters, order_by, order_type, offset, limit, "
                         "expected_person_phones", [
    (awfapi_nonreadonly_user, None, None, "asc", 0, 3,
     [person_phones_db[0], person_phones_db[1], person_phones_db[2]]),
    (awfapi_nonreadonly_user, None, None, "asc", 1, 1,
     [person_phones_db[1]]),
    (awfapi_readonly_user, None, None, "asc", 0, 3,
     [person_phones_db[0], person_phones_db[1], person_phones_db[2]]),
    (awfapi_nonreadonly_user, "person_ids:[1|2|3|4]", None, "asc", 0, 10,
     [person_phones_db[0], person_phones_db[1], person_phones_db[2], person_phones_db[3]]),
    (awfapi_nonreadonly_user, "phone_number_type_ids:[1|2]", None, "asc", 0, 10,
     [person_phones_db[0], person_phones_db[1], person_phones_db[2]]),
    (awfapi_nonreadonly_user, "person_ids:[4|5],phone_number_type_ids:[3]", None, "asc", 0, 10,
     [person_phones_db[3], person_phones_db[4]]),
    (awfapi_nonreadonly_user, "person_ids:[1|2|3|4]", "person_full_name", "asc", 0, 10,
     [person_phones_db[3], person_phones_db[0], person_phones_db[1], person_phones_db[2]]),
    (awfapi_nonreadonly_user, "person_ids:[1|2|3|4]", "phone_number", "asc", 0, 10,
     [person_phones_db[0], person_phones_db[3], person_phones_db[1], person_phones_db[2]]),
    (awfapi_nonreadonly_user, "person_ids:[1|2|3|4]", "phone_number_type_name", "asc", 0, 10,
     [person_phones_db[0], person_phones_db[1], person_phones_db[3], person_phones_db[2]]),
    (awfapi_nonreadonly_user, "person_ids:[1|2|3|4]", "phone_number_type_name", "desc", 0, 10,
     [person_phones_db[2], person_phones_db[3], person_phones_db[1], person_phones_db[0]]),
])
def test_get_person_phones_should_return_200_response(client, monkeypatch,
                                                      awfapi_registered_user: AWFAPIRegisteredUser,
                                                      filters: Optional[str],
                                                      order_by: Optional[str], order_type: Optional[EOrderType],
                                                      offset: int, limit: int,
                                                      expected_person_phones: List[PersonPhoneInput]) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/get_person_phones",
                              params={'filters': filters,
                                      'order_by': order_by, 'order_type': order_type,
                                      'offset': offset, 'limit': limit},
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_dict = response.json()
        person_phones = list(map(lambda rd: PersonPhone(**rd[0]), response_dict))
        assert len(person_phones) == len(expected_person_phones)
        for pp, epp in zip(person_phones, expected_person_phones):
            assert pp.business_entity_id == epp.business_entity_id
            assert pp.phone_number == epp.phone_number
            assert pp.phone_number_type_id == epp.phone_number_type_id
            assert pp.modified_date is not None

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, filters, order_by, order_type, offset, limit, expected_message", [
    (awfapi_readonly_user, None, None, "asc", -1, 0,
     ResponseMessage(title="Invalid value for SQL clause.",
                     description=f"{E400BadRequest.INVALID_SQL_VALUE}: Value '-1' is invalid for SKIP clause.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, None, None, "asc", 0, -1,
     ResponseMessage(title="Invalid value for SQL clause.",
                     description=f"{E400BadRequest.INVALID_SQL_VALUE}: Value '-1' is invalid for LIMIT clause.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_id:[20785|20777]", None, "asc", 0, 0,
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['person_id']' some of which "
                                 f"do not exist in person phone filtering fields: "
                                 f"['person_ids', 'phone_number_type_ids'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids:[20785|20777],phone_number_type_id:[1|2]", None, "asc", 0, 0,
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['person_ids', 'phone_number_type_id']' some of which "
                                 f"do not exist in person phone filtering fields: "
                                 f"['person_ids', 'phone_number_type_ids'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids", None, "asc", 0, 0,
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Invalid filter string: person_ids.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids:[20785[20777|20776|20775|20774]", None, "asc", 0, 0,
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Wrong value of list items: '20785[20777|20776|20775|20774'. Cannot contain '[' or ']'.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_ids:[20785,20777|20776|20775|20774],phone_number_type_ids:[1|2]", None, "asc", 0, 0,
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Invalid filter string: person_ids:[20785,20777|20776|20775|20774],phone_number_type_ids:[1|2].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, None, "person_id", "asc", 0, 0,
     ResponseMessage(title="Non-existing column for ordering.",
                     description=f"{E400BadRequest.INVALID_ORDERING_COLUMN_NAME}: "
                                 f"Column does not exist in person phones view ('person_id').",
                     code=status.HTTP_400_BAD_REQUEST)),
])
def test_get_person_phones_should_return_400_response(client, monkeypatch,
                                                      awfapi_registered_user: AWFAPIRegisteredUser,
                                                      filters: Optional[str],
                                                      order_by: Optional[str], order_type: Optional[EOrderType],
                                                      offset: int, limit: int,
                                                      expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/get_person_phones",
                              params={'filters': filters,
                                      'order_by': order_by, 'order_type': order_type,
                                      'offset': offset, 'limit': limit},
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        message = ResponseMessage(**response.json()['detail'])
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("filters, order_by, order_type, offset, limit, expected_message", [
    (None, None, "asc", 0, 3,
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_get_person_phones_should_return_401_response(client, monkeypatch,
                                                      filters: Optional[str],
                                                      order_by: Optional[str], order_type: Optional[EOrderType],
                                                      offset: int, limit: int,
                                                      expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get("/get_person_phones",
                              params={'filters': filters,
                                      'order_by': order_by, 'order_type': order_type,
                                      'offset': offset, 'limit': limit})

        # Assert
        message = ResponseMessage(**response.json())
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()
