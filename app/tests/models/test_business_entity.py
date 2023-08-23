import pytest
import datetime as dt
import uuid

from app.models import BusinessEntity


@pytest.mark.parametrize("business_entity_id, rowguid, modified_date, expected_business_entity", [
    (101, uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"), dt.datetime(2020, 1, 1, 0, 0, 0),
     BusinessEntity(business_entity_id=101,
                    rowguid=uuid.UUID("92c4279f-1207-48a3-8448-4636514eb7e2"),
                    modified_date=dt.datetime(2020, 1, 1, 0, 0, 0))),
    (0, uuid.UUID("00000000-0000-0000-0000-000000000000"), dt.datetime(2000, 1, 1, 0, 0, 0),
     BusinessEntity(business_entity_id=0,
                    rowguid=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                    modified_date=dt.datetime(2000, 1, 1, 0, 0, 0)))
])
def test_business_entity_constructor_should_create_valid_object(business_entity_id: int,
                                                                rowguid: uuid.UUID, modified_date: dt.datetime,
                                                                expected_business_entity: BusinessEntity) -> None:
    # Act
    business_entity = BusinessEntity(business_entity_id=business_entity_id,
                                     rowguid=rowguid, modified_date=modified_date)

    # Assert
    assert business_entity.business_entity_id == expected_business_entity.business_entity_id
    assert business_entity.rowguid == expected_business_entity.rowguid
    assert business_entity.modified_date == expected_business_entity.modified_date
