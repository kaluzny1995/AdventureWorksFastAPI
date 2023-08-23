import pytest
import sqlalchemy
from sqlmodel import create_engine
from typing import List

from app.config import PostgresdbConnectionConfig
from app.providers import BusinessEntityProvider
from app import errors

from app.tests.fixtures.fixtures_tests import create_tables, drop_tables


connection_string: str = PostgresdbConnectionConfig.get_db_connection_string(test_suffix="_test")
db_engine: sqlalchemy.engine.Engine = create_engine(connection_string)
business_entity_provider: BusinessEntityProvider = BusinessEntityProvider(connection_string, db_engine)


@pytest.mark.parametrize("business_entities", [
    ["BusinessEntity0", "BusinessEntity1", "BusinessEntity2"],
    ["BusinessEntity0"]
])
def test_get_business_entities_should_return_valid_objects(business_entities: List[object]) -> None:
    create_tables(db_engine)

    # Arrange
    for _ in business_entities:
        business_entity_provider.insert_business_entity()

    # Act
    expected_business_entities = business_entity_provider.get_business_entities()

    # Assert
    assert len(business_entities) == len(expected_business_entities)
    for _, ebe in zip(business_entities, expected_business_entities):
        assert ebe.business_entity_id is not None
        assert ebe.rowguid is not None
        assert ebe.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("business_entity", [
    "BusinessEntity0", "BusinessEntity1"
])
def test_get_business_entity_should_return_valid_object(business_entity: object) -> None:
    create_tables(db_engine)

    # Arrange
    business_entity_id = business_entity_provider.insert_business_entity()

    # Act
    expected_business_entity = business_entity_provider.get_business_entity(business_entity_id)

    # Assert
    assert expected_business_entity.business_entity_id is not None
    assert expected_business_entity.rowguid is not None
    assert expected_business_entity.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("business_entity", [
    "BusinessEntity0", "BusinessEntity1"
])
def test_insert_business_entity_should_insert_object(business_entity: object) -> None:
    create_tables(db_engine)

    # Arrange
    # Act
    business_entity_id = business_entity_provider.insert_business_entity()

    # Assert
    expected_business_entity = business_entity_provider.get_business_entity(business_entity_id)
    assert expected_business_entity.business_entity_id is not None
    assert expected_business_entity.rowguid is not None
    assert expected_business_entity.modified_date is not None

    drop_tables(db_engine)


@pytest.mark.parametrize("business_entity", [
    "BusinessEntity0", "BusinessEntity1"
])
def test_delete_person_should_delete_object(business_entity: object) -> None:
    create_tables(db_engine)

    # Arrange
    business_entity_id = business_entity_provider.insert_business_entity()

    # Act
    business_entity_provider.delete_business_entity(business_entity_id)

    # Assert
    with pytest.raises(errors.NotFoundError):
        business_entity_provider.get_business_entity(business_entity_id)

    drop_tables(db_engine)
