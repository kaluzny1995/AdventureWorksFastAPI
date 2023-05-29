import sqlalchemy
from sqlmodel import SQLModel


def create_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.create_all(bind=engine)


def drop_tables(engine: sqlalchemy.engine.Engine) -> None:
    SQLModel.metadata.drop_all(bind=engine)
