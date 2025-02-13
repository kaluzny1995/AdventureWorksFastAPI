import pytest
from typing import List
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, AWFAPIUserInput, AWFAPIUser, AWFAPIRegisteredUser,
                        E401Unauthorized)
from app.factories import MongoDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory

from app.routes import jwt_authentication as jwt_authentication_routes
from app.routes import awfapi_user as awfapi_user_routes
from app import oauth2_handlers

from app.tests.fixtures.fixtures_entry_lists import awfapi_users_db, awfapi_nonreadonly_user, awfapi_readonly_user
from app.tests.fixtures.fixtures_tests import (register_test_user, obtain_access_token,
                                               insert_test_awfapi_users, drop_collection)


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def fixtures_before_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_provider', awfapi_user_provider)
    monkeypatch.setattr(awfapi_user_routes, 'awfapi_user_service', awfapi_user_service)
    monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)
    monkeypatch.setattr(oauth2_handlers, 'jwt_auth_service', jwt_authentication_service)

    insert_test_awfapi_users(mongodb_connection_string, mongodb_collection_name, mongodb_engine)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, offset, limit, expected_awfapi_users", [
    (awfapi_nonreadonly_user, 0, 3, [awfapi_users_db[0], awfapi_users_db[1], awfapi_users_db[2]]),
    (awfapi_nonreadonly_user, 1, 1, [awfapi_users_db[1]]),
    (awfapi_readonly_user, 0, 3, [awfapi_users_db[0], awfapi_users_db[1], awfapi_users_db[2]])
])
def test_get_awfapi_users_should_return_200_response(client, monkeypatch,
                                                     awfapi_registered_user: AWFAPIRegisteredUser,
                                                     offset: int, limit: int,
                                                     expected_awfapi_users: List[AWFAPIUserInput]) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/all_awfapi_users", params={'offset': offset, 'limit': limit}, headers={
            'Authorization': f"Bearer {access_token}"
        })

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_dict = response.json()
        awfapi_users = list(map(lambda rd: AWFAPIUser(**rd), response_dict))
        assert len(awfapi_users) == len(expected_awfapi_users)
        for au, eau in zip(awfapi_users, expected_awfapi_users):
            assert au.username == eau.username
            assert au.full_name == eau.full_name
            assert au.email == eau.email
            assert au.is_readonly == eau.is_readonly

    except Exception as e:
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


@pytest.mark.parametrize("offset, limit, expected_message", [
    (0, 3,
     ResponseMessage(title="JWT token not provided or wrong encoded.",
                     description=f"{E401Unauthorized.INVALID_JWT_TOKEN}: "
                                 f"User did not provide or the JWT token is wrongly encoded.",
                     code=status.HTTP_401_UNAUTHORIZED))
])
def test_get_awfapi_users_should_return_401_response(client, monkeypatch,
                                                     offset: int, limit: int,
                                                     expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get("/all_awfapi_users", params={'offset': offset, 'limit': limit})

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
