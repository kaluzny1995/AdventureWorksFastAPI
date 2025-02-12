import pytest
from typing import Optional, List
from starlette.testclient import TestClient
from fastapi import status
from pytest import MonkeyPatch

from app.models import (ResponseMessage, PersonInput, Person,
                        E400BadRequest, E404NotFound)
from app.factories import (MongoDBFactory, PostgresDBFactory, AWFAPIUserFactory, JWTAuthenticationFactory,
                           PersonFactory)

from app.routes import person as person_routes

from app.tests.fixtures.fixtures_entry_lists import persons_db
from app.tests.fixtures.fixtures_tests import insert_test_persons, create_tables, drop_tables


mongodb_connection_string, mongodb_collection_name, mongodb_engine = MongoDBFactory.get_db_connection_details(test_suffix="_test")
awfapi_user_provider, awfapi_user_service = AWFAPIUserFactory.get_provider_and_service(mongodb_connection_string, mongodb_collection_name, mongodb_engine)
jwt_authentication_service = JWTAuthenticationFactory.get_service(awfapi_user_provider, awfapi_user_service)

postgresdb_connection_string, postgresdb_engine = PostgresDBFactory.get_db_connection_details(test_suffix="_test")
person_provider, person_service = PersonFactory.get_provider_and_service(postgresdb_connection_string, postgresdb_engine)


@pytest.fixture()
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def fixtures_before_test(monkeypatch: MonkeyPatch) -> None:
    create_tables(postgresdb_engine)

    monkeypatch.setattr(person_routes, 'person_provider', person_provider)
    monkeypatch.setattr(person_routes, 'person_service', person_service)

    insert_test_persons(postgresdb_engine, postgresdb_connection_string)


def fixtures_after_test() -> None:
    drop_tables(postgresdb_engine)


@pytest.mark.parametrize("first_name_phrase, last_name_phrase, is_alternative, expected_persons", [
    ("ria", "", False, [persons_db[5]]),
    ("ron", "", False, [persons_db[6], persons_db[7], persons_db[8]]),
    ("", "smi", False, [persons_db[1], persons_db[6], persons_db[8], persons_db[9]]),
    ("ron", "smi", False, [persons_db[6], persons_db[8]]),
    ("rian", "shing", True, [persons_db[5], persons_db[7]])
])
def test_search_by_phrases_should_return_200_response(client, monkeypatch,
                                                      first_name_phrase: Optional[str],
                                                      last_name_phrase: Optional[str],
                                                      is_alternative: Optional[bool],
                                                      expected_persons: List[PersonInput]) -> None:
    try:
        # Arrange
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get("/search_by_phrases",
                              params={'first_name_phrase': first_name_phrase,
                                      'last_name_phrase': last_name_phrase,
                                      'is_ordered': False,
                                      'is_alternative': is_alternative})

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
        fixtures_after_test()
        raise e
    else:
        fixtures_after_test()


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
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get("/search_by_phrases",
                              params={'first_name_phrase': first_name_phrase, 'last_name_phrase': last_name_phrase})

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
        fixtures_before_test(monkeypatch)

        # Act
        response = client.get(f"/search_by_phrases",
                              params={'first_name_phrase': first_name_phrase, 'last_name_phrase': last_name_phrase})

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
