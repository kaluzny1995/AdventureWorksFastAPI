import pytest
from typing import Optional
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (CountMessage, ResponseMessage, AWFAPIRegisteredUser,
                        E400BadRequest, E401Unauthorized)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PersonFactory)

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app.routes import person as person_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_nonreadonly_user, awfapi_readonly_user
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token, insert_test_persons,
                                               create_tables, drop_tables, drop_collection)


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)

postgresdb_connection_string, postgresdb_engine = PostgresDBFactory.get_db_connection_details(test_suffix="_test")
person_provider = PersonFactory.get_provider(postgresdb_connection_string, postgresdb_engine)


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

    monkeypatch.setattr(person_routes, 'person_provider', person_provider)

    insert_test_persons(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)
    drop_tables(postgresdb_engine)


@pytest.mark.parametrize("awfapi_registered_user, filters, expected_message", [
    (awfapi_nonreadonly_user, None, CountMessage(entity="Person", count=10)),
    (awfapi_readonly_user, None, CountMessage(entity="Person", count=10)),
    (awfapi_nonreadonly_user, "person_type:GC", CountMessage(entity="Person", count=2)),
    (awfapi_nonreadonly_user, "person_type:SC,last_name_phrase:smi", CountMessage(entity="Person", count=3)),
    (awfapi_nonreadonly_user, "person_type:SC,first_name_phrase:ron,last_name_phrase:smi", CountMessage(entity="Person", count=2)),
])
def test_count_persons_should_return_200_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  filters: Optional[str],
                                                  expected_message: CountMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/count_persons", params={'filters': filters},
                              headers={'Authorization': f"Bearer {access_token}"})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        message = CountMessage(**response.json())
        assert message.entity == expected_message.entity
        assert message.count == expected_message.count

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("awfapi_registered_user, filters, expected_message", [
    (awfapi_readonly_user, "last_name:pph",
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['last_name']' some of which "
                                 f"do not exist in person filtering fields: "
                                 f"['person_type', 'first_name_phrase', 'last_name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "last_name_phrase:pph,first_name:ffh",
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['last_name_phrase', 'first_name']' some of which "
                                 f"do not exist in person filtering fields: "
                                 f"['person_type', 'first_name_phrase', 'last_name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "pers_type:GC",
     ResponseMessage(title="Non-existing fields in filter string.",
                     description=f"{E400BadRequest.INVALID_FIELDS_IN_FILTER_STRING}: "
                                 f"Filter string contains fields: '['pers_type']' some of which "
                                 f"do not exist in person filtering fields: "
                                 f"['person_type', 'first_name_phrase', 'last_name_phrase'].",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_type",
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Invalid filter string: person_type.",
                     code=status.HTTP_400_BAD_REQUEST)),
    (awfapi_readonly_user, "person_type:SC,last_name_phrase",
     ResponseMessage(title="Invalid filter string.",
                     description=f"{E400BadRequest.INVALID_FILTER_STRING}: "
                                 f"Invalid filter string: person_type:SC,last_name_phrase.",
                     code=status.HTTP_400_BAD_REQUEST))
])
def test_count_persons_should_return_400_response(client, monkeypatch,
                                                  awfapi_registered_user: AWFAPIRegisteredUser,
                                                  filters: Optional[str],
                                                  expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/count_persons", params={'filters': filters},
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


@pytest.mark.parametrize("filters, expected_message", [
    (None,
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_count_persons_should_return_401_response(client, monkeypatch,
                                                  filters: Optional[str],
                                                  expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get("/count_persons", params={'filters': filters})

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
