import pytest
from typing import Optional, List
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIRegisteredUser, EOrderType, PhoneNumberTypeInput, PhoneNumberType,
                        E400BadRequest, E401Unauthorized)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PhoneNumberTypeFactory)

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import phone_number_type as phone_number_type_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user, phone_number_types_db
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token, insert_test_phone_number_types,
                                               create_tables, drop_tables, drop_collection)


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)

postgresdb_connection_string, postgresdb_engine = PostgresDBFactory.get_db_connection_details(test_suffix="_test")
phone_number_type_provider = PhoneNumberTypeFactory.get_provider(postgresdb_connection_string, postgresdb_engine)


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

    monkeypatch.setattr(phone_number_type_routes, 'phone_number_type_provider', phone_number_type_provider)

    insert_test_phone_number_types(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)
    drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, filters, order_by, order_type, offset, limit, expected_phone_number_types", [
    (awfapi_nonreadonly_user, None, None, "asc", 0, 3, [phone_number_types_db[0], phone_number_types_db[1], phone_number_types_db[2]]),
    (awfapi_nonreadonly_user, None, None, "asc", 1, 1, [phone_number_types_db[1]]),
    (awfapi_readonly_user, None, None, "asc", 0, 3, [phone_number_types_db[0], phone_number_types_db[1], phone_number_types_db[2]]),
    (awfapi_nonreadonly_user, "name_phrase:hom", None, "asc", 0, 10, [phone_number_types_db[2], phone_number_types_db[3], phone_number_types_db[4]]),
    (awfapi_nonreadonly_user, "name_phrase:hom", "name", "asc", 0, 10, [phone_number_types_db[2], phone_number_types_db[3], phone_number_types_db[4]]),
    (awfapi_nonreadonly_user, "name_phrase:hom", "name", "asc", 1, 1, [phone_number_types_db[3]]),
    (awfapi_nonreadonly_user, "name_phrase:hom", "name", "desc", 0, 10, [phone_number_types_db[4], phone_number_types_db[3], phone_number_types_db[2]]),
])
def test_get_phone_number_types_should_return_200_response(client, monkeypatch,
                                                           awfapi_registered_user: AWFAPIRegisteredUser,
                                                           filters: Optional[str],
                                                           order_by: Optional[str], order_type: Optional[EOrderType],
                                                           offset: int, limit: int,
                                                           expected_phone_number_types: List[PhoneNumberTypeInput]) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/get_phone_number_types",
                              params={'filters': filters,
                                      'order_by': order_by, 'order_type': order_type,
                                      'offset': offset, 'limit': limit},
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_dict = response.json()
        phone_number_types = list(map(lambda rd: PhoneNumberType(**rd), response_dict))
        assert len(phone_number_types) == len(expected_phone_number_types)
        for pnt, epnt in zip(phone_number_types, expected_phone_number_types):
            assert pnt.phone_number_type_id is not None
            assert pnt.name == epnt.name
            assert pnt.modified_date is not None

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
    (awfapi_readonly_user, "name:hom", None, "asc", 0, 0,
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['name']' some of which "
                                 f"do not exist in phone number type filtering fields: "
                                 f"['name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "name_phr:hom", None, "asc", 0, 0,
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['name_phr']' some of which "
                                 f"do not exist in phone number type filtering fields: "
                                 f"['name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "name_phrase", None, "asc", 0, 0,
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Invalid filter string: name_phrase.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, None, "name_phrase", "asc", 0, 0,
     ResponseMessage(title="Non-existing column for ordering.",
                     description=f"{E400BadRequest.INVALID_ORDERING_COLUMN_NAME}: "
                                 f"Column does not exist in phone number types view ('name_phrase').",
                     code=status.HTTP_400_BAD_REQUEST)),
])
def test_get_phone_number_types_should_return_400_response(client, monkeypatch,
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
        response = client.get("/get_phone_number_types",
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
def test_get_phone_number_types_should_return_401_response(client, monkeypatch,
                                                           filters: Optional[str],
                                                           order_by: Optional[str], order_type: Optional[EOrderType],
                                                           offset: int, limit: int,
                                                           expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get("/get_phone_number_types",
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
