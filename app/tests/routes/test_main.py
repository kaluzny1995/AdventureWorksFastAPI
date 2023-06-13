import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("address", [
    "/",
    "/hello"
])
def test_hello_fast_api_should_return_200_response(client, monkeypatch, address):
    # Arrange
    # Act
    response = client.get(address)

    # Assert
    assert response.status_code == 200
    response_dict = response.json()
    assert response_dict['message'] == "Hello FastAPI!"
