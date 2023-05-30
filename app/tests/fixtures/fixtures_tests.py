import sqlalchemy
import pymongo
from sqlmodel import SQLModel


def create_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.create_all(bind=engine)


def drop_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.drop_all(bind=engine)


def drop_collection(engine: pymongo.MongoClient, name: str) -> None:
    engine.awfapi[name].drop()
