import sqlalchemy
import pymongo
from sqlmodel import SQLModel
from starlette.testclient import TestClient

from app.models import AWFAPIRegisteredUser, Token
from app.services import AWFAPIUserService


def create_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.create_all(bind=engine)


def drop_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.drop_all(bind=engine)


def register_test_user(awfapi_user_service, awfapi_registered_user: AWFAPIRegisteredUser) -> None:
    awfapi_user_service.register_awfapi_user(awfapi_registered_user)


def obtain_access_token(client: TestClient, awfapi_registered_user: AWFAPIRegisteredUser) -> str:
    response = client.post("/token", data={'username': awfapi_registered_user.username,
                                           'password': awfapi_registered_user.password})
    token = Token(**response.json())
    return token.access_token


def drop_collection(engine: pymongo.MongoClient, name: str) -> None:
    engine.awfapi[name].drop()
