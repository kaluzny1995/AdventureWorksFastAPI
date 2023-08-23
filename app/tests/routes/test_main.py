import pytest
from fastapi import status
from starlette.testclient import TestClient

from app.models import ResponseMessage


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("endpoint_url, expected_response_message", [
    ("/", ResponseMessage(title="Hello FastAPI", description="Successful response.", code=status.HTTP_200_OK)),
    ("/hello", ResponseMessage(title="Hello FastAPI", description="Successful response.", code=status.HTTP_200_OK))
])
def test_hello_fast_api_should_return_200_response(client, monkeypatch,
                                                   endpoint_url: str, expected_response_message: ResponseMessage):
    # Arrange
    # Act
    response = client.get(endpoint_url)

    # Assert
    response_message = ResponseMessage(**response.json())
    assert response_message.title == expected_response_message.title
    assert response_message.description == expected_response_message.description
    assert response_message.code == expected_response_message.code
