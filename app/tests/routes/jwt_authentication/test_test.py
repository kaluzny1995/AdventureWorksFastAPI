import pytest
from typing import Optional
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import ResponseMessage, AWFAPIRegisteredUser
from app.factories import MongoDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory

from app.routes import jwt_authentication as jwt_authentication_routes

from app.tests.fixtures.fixtures_entry_lists import awfapi_readonly_user
from app.tests.fixtures.fixtures_tests import register_test_user, obtain_access_token, drop_collection


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def fixtures_before_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(jwt_authentication_routes, 'jwt_auth_service', jwt_authentication_service)


def fixtures_after_test() -> None:
    drop_collection(mongodb_engine, mongodb_collection_name)


@pytest.mark.parametrize("awfapi_registered_user, access_token, expected_message", [
    (awfapi_readonly_user, None,
     ResponseMessage(title="AUTHENTICATED",
                     description="Users authentication status: AUTHENTICATED.",
                     code=status.HTTP_200_OK)),
    (awfapi_readonly_user, "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY4NjE0MDY2Mn0.sr4CeMbhD12LYzDyAD67AzGReBwgo2jh4zBSLy0_9-I",
     ResponseMessage(title="EXPIRED",
                     description="Users authentication status: EXPIRED.",
                     code=status.HTTP_200_OK)),
    (awfapi_readonly_user, "fake_access_token",
     ResponseMessage(title="UNAUTHENTICATED",
                     description="Users authentication status: UNAUTHENTICATED.",
                     code=status.HTTP_200_OK))
])
def test_test_should_return_200_response(client, monkeypatch,
                                         awfapi_registered_user: AWFAPIRegisteredUser,
                                         access_token: Optional[str],
                                         expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)
        register_test_user(awfapi_user_service, awfapi_registered_user)
        if access_token is None:
            access_token = obtain_access_token(client, awfapi_registered_user)

        # Act
        response = client.get("/test", headers={
            'Authorization': f"Bearer {access_token}"
        })

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
