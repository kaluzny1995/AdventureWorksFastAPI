import pytest
import sqlalchemy
from sqlmodel import create_engine
from typing import Optional, List
from starlette.testclient import TestClient
from fastapi import status

from app.config import PostgresdbConnectionConfig
from app.models import ResponseMessage, EPersonType, PersonInput, Person, \
    E400BadRequest, E404NotFound
from app.providers import BusinessEntityProvider, PersonProvider
from app.services import PersonService

from app.routes import person as person_routes

from app.tests.fixtures.fixtures_tests import create_tables, drop_tables


postgresdb_connection_string: str = PostgresdbConnectionConfig.get_db_connection_string(test_suffix="_test")
postgresdb_engine: sqlalchemy.engine.Engine = create_engine(postgresdb_connection_string)
business_entity_provider: BusinessEntityProvider = BusinessEntityProvider(
    connection_string=postgresdb_connection_string,
    db_engine=postgresdb_engine
)
person_provider: PersonProvider = PersonProvider(
    connection_string=postgresdb_connection_string,
    business_entity_provider=business_entity_provider,
    db_engine=postgresdb_engine
)
person_service: PersonService = PersonService(
    person_provider=person_provider
)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


persons_db: List[PersonInput] = [
    PersonInput(person_type=EPersonType.GC, first_name="John", last_name="Doe"),
    PersonInput(person_type=EPersonType.EM, first_name="John", last_name="Smith"),
    PersonInput(person_type=EPersonType.IN, first_name="John", last_name="Adams"),
    PersonInput(person_type=EPersonType.VC, first_name="John", middle_name="K", last_name="Adams"),
    PersonInput(person_type=EPersonType.SP, first_name="John", middle_name="J", last_name="Adams"),
    PersonInput(person_type=EPersonType.GC, first_name="Brian", last_name="Washer"),
    PersonInput(person_type=EPersonType.SC, first_name="Aaron", last_name="Dasmi"),
    PersonInput(person_type=EPersonType.SC, first_name="Aaron", last_name="Washington"),
    PersonInput(person_type=EPersonType.SC, first_name="Sharon", last_name="Smith"),
    PersonInput(person_type=EPersonType.SC, first_name="Claire", last_name="Smith"),
]


@pytest.mark.parametrize("first_name_phrase, last_name_phrase, expected_persons", [
    ("ria", "", [persons_db[5]]),
    ("ron", "", [persons_db[6], persons_db[7], persons_db[8]]),
    ("", "smi", [persons_db[1], persons_db[6], persons_db[8], persons_db[9]]),
    ("ron", "smi", [persons_db[6], persons_db[8]])
])
def test_search_by_phrases_should_return_200_response(client, monkeypatch,
                                                      first_name_phrase: Optional[str],
                                                      last_name_phrase: Optional[str],
                                                      expected_persons: List[PersonInput]) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(person_routes, 'person_provider', person_provider)
        monkeypatch.setattr(person_routes, 'person_service', person_service)

        for pdb in persons_db:
            person_provider.insert_person(pdb)

        # Act
        response = client.get("/search_by_phrases",
                              params={'first_name_phrase': first_name_phrase,
                                      'last_name_phrase': last_name_phrase,
                                      'is_ordered': False})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_dict = response.json()
        persons = list(map(lambda rd: Person(**rd), response_dict))
        assert len(persons) == len(expected_persons)
        for p, ep in zip(persons, expected_persons):
            assert p.business_entity_id is not None
            assert p.person_type == ep.person_type
            assert p.name_style == ep.name_style
            assert p.title == ep.title
            assert p.first_name == ep.first_name
            assert p.middle_name == ep.middle_name
            assert p.last_name == ep.last_name
            assert p.suffix == ep.suffix
            assert p.email_promotion == ep.email_promotion
            assert p.additional_contact_info == ep.additional_contact_info
            assert p.demographics == ep.demographics
            assert p.rowguid is not None
            assert p.modified_date is not None

    except Exception as e:
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("first_name_phrase, last_name_phrase, expected_message", [
    ("", "", ResponseMessage(title="Missing values.",
                             description=f"{E400BadRequest.VALUES_NOT_PROVIDED}: "
                                         f"Either first or last name phrase must be provided.",
                             code=status.HTTP_400_BAD_REQUEST)),
    (None, None, ResponseMessage(title="Missing values.",
                                 description=f"{E400BadRequest.VALUES_NOT_PROVIDED}: "
                                             f"Either first or last name phrase must be provided.",
                                 code=status.HTTP_400_BAD_REQUEST))
])
def test_search_by_phrases_should_return_400_response(client, monkeypatch,
                                                      first_name_phrase: Optional[str],
                                                      last_name_phrase: Optional[str],
                                                      expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(person_routes, 'person_provider', person_provider)
        monkeypatch.setattr(person_routes, 'person_service', person_service)

        for pdb in persons_db:
            person_provider.insert_person(pdb)

        # Act
        response = client.get("/search_by_phrases",
                              params={'first_name_phrase': first_name_phrase, 'last_name_phrase': last_name_phrase})

        # Assert
        message = ResponseMessage(**response.json()['detail'])
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_tables(postgresdb_engine)


@pytest.mark.parametrize("first_name_phrase, last_name_phrase, expected_message", [
    ("ahn", "",
     ResponseMessage(title="Persons not found | "
                           "No persons found for given phrases(first_name_phrase: ahn | last_name_phrase: None).",
                     description=f"{E404NotFound.PERSON_NOT_FOUND}: Persons of given phrases not found.",
                     code=status.HTTP_404_NOT_FOUND)),
    ("", "oth",
     ResponseMessage(title="Persons not found | "
                           "No persons found for given phrases(first_name_phrase: None | last_name_phrase: oth).",
                     description=f"{E404NotFound.PERSON_NOT_FOUND}: Persons of given phrases not found.",
                     code=status.HTTP_404_NOT_FOUND)),
    ("ohn", "ems",
     ResponseMessage(title="Persons not found | "
                           "No persons found for given phrases(first_name_phrase: ohn | last_name_phrase: ems).",
                     description=f"{E404NotFound.PERSON_NOT_FOUND}: Persons of given phrases not found.",
                     code=status.HTTP_404_NOT_FOUND)),
    ("oron", "smi",
     ResponseMessage(title="Persons not found | "
                           "No persons found for given phrases(first_name_phrase: oron | last_name_phrase: smi).",
                     description=f"{E404NotFound.PERSON_NOT_FOUND}: Persons of given phrases not found.",
                     code=status.HTTP_404_NOT_FOUND))
])
def test_search_by_phrases_should_return_404_response(client, monkeypatch,
                                                      first_name_phrase: Optional[str],
                                                      last_name_phrase: Optional[str],
                                                      expected_message: ResponseMessage) -> None:
    try:
        # Arrange
        create_tables(postgresdb_engine)

        monkeypatch.setattr(person_routes, 'person_provider', person_provider)
        monkeypatch.setattr(person_routes, 'person_service', person_service)

        for pdb in persons_db:
            person_provider.insert_person(pdb)

        # Act
        response = client.get(f"/search_by_phrases",
                              params={'first_name_phrase': first_name_phrase, 'last_name_phrase': last_name_phrase})

        # Assert
        message = ResponseMessage(**response.json()['detail'])
        assert message.title == expected_message.title
        assert message.description == expected_message.description
        assert message.code == expected_message.code

    except Exception as e:
        drop_tables(postgresdb_engine)
        raise e
    else:
        drop_tables(postgresdb_engine)
