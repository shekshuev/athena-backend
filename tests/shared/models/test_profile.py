from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from shared.models.profile import (
    CreateProfileRecordDto,
    FilterProfileRecordsDto,
    PatchProfileDto,
    ProfileKVInput,
    ReadProfileRecordDto,
    UpdateProfileRecordDto,
    UpsertProfileRecordsDto,
)


def test_profile_kv_input_valid():
    """
    Test that ProfileKVInput accepts valid key/value/source.
    """
    dto = ProfileKVInput(key="first_name", value="John", source="user")
    assert dto.key == "first_name"
    assert dto.value == "John"
    assert dto.source == "user"


def test_profile_kv_input_invalid_key():
    """
    Test that ProfileKVInput raises ValidationError for invalid key.
    """
    with pytest.raises(ValidationError):
        ProfileKVInput(key="nickname", value="John", source="user")


def test_profile_kv_input_invalid_source():
    """
    Test that ProfileKVInput raises ValidationError for invalid source.
    """
    with pytest.raises(ValidationError):
        ProfileKVInput(key="first_name", value="John", source="external")


def test_create_profile_record_dto_valid():
    """
    Test that CreateProfileRecordDto accepts valid data.
    """
    dto = CreateProfileRecordDto(
        account_id="uuid-1",
        key="last_name",
        value="Doe",
        source="admin",
    )
    assert dto.account_id == "uuid-1"
    assert dto.key == "last_name"
    assert dto.value == "Doe"
    assert dto.source == "admin"


def test_create_profile_record_dto_default_source():
    """
    Test that CreateProfileRecordDto defaults `source` to 'user'.
    """
    dto = CreateProfileRecordDto(account_id="uuid-1", key="last_name", value="Doe")
    assert dto.source == "user"


def test_create_profile_record_dto_invalid_key():
    """
    Test that CreateProfileRecordDto enforces valid key.
    """
    with pytest.raises(ValidationError):
        CreateProfileRecordDto(account_id="uuid-1", key="nickname", value="Doe")


def test_read_profile_record_dto_valid():
    """
    Test that ReadProfileRecordDto accepts valid fields.
    """
    now = datetime.now(timezone.utc)
    dto = ReadProfileRecordDto(
        id="uuid-123",
        account_id="uuid-acc",
        key="date_of_birth",
        value="1990-01-01",
        source="system",
        created_at=now,
        updated_at=now,
    )
    assert dto.key == "date_of_birth"
    assert dto.source == "system"
    assert isinstance(dto.created_at, datetime)
    assert dto.updated_at == now


def test_read_profile_record_dto_invalid_source():
    """
    Test that ReadProfileRecordDto rejects invalid source.
    """
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ReadProfileRecordDto(
            id="uuid-123",
            account_id="uuid-acc",
            key="first_name",
            value="John",
            source="unknown",
            created_at=now,
            updated_at=now,
        )


def test_update_profile_record_dto_valid():
    """
    Test that UpdateProfileRecordDto accepts valid values.
    """
    dto = UpdateProfileRecordDto(value="Updated", source="system")
    assert dto.value == "Updated"
    assert dto.source == "system"


def test_update_profile_record_dto_invalid_source():
    """
    Test that UpdateProfileRecordDto raises ValidationError for invalid source.
    """
    with pytest.raises(ValidationError):
        UpdateProfileRecordDto(value="Updated", source="invalid")


def test_upsert_profile_records_dto_valid():
    """
    Test that UpsertProfileRecordsDto accepts a list of ProfileKVInput.
    """
    records = [
        ProfileKVInput(key="first_name", value="John", source="user"),
        ProfileKVInput(key="last_name", value="Doe", source="user"),
    ]
    dto = UpsertProfileRecordsDto(account_id="uuid-1", records=records)
    assert dto.account_id == "uuid-1"
    assert len(dto.records) == 2
    assert dto.records[0].key == "first_name"


def test_upsert_profile_records_dto_invalid_record_type():
    """
    Test that UpsertProfileRecordsDto raises ValidationError for wrong record type.
    """
    with pytest.raises(ValidationError):
        UpsertProfileRecordsDto(account_id="uuid-1", records=["value"])


def test_patch_profile_dto_valid():
    """
    Test that PatchProfileDto accepts valid changes list.
    """
    changes = [
        ProfileKVInput(key="first_name", value="Jane", source="user"),
        ProfileKVInput(key="last_name", value="Smith", source="system"),
    ]
    dto = PatchProfileDto(account_id="uuid-2", changes=changes)
    assert dto.account_id == "uuid-2"
    assert len(dto.changes) == 2
    assert dto.changes[1].source == "system"


def test_patch_profile_dto_invalid_key():
    """
    Test that PatchProfileDto raises ValidationError for invalid key in changes.
    """
    with pytest.raises(ValidationError):
        PatchProfileDto(
            account_id="uuid-2",
            changes=[ProfileKVInput(key="nickname", value="Bob", source="user")],
        )


def test_filter_profile_records_dto_defaults():
    """
    Test that FilterProfileRecordsDto applies default pagination.
    """
    dto = FilterProfileRecordsDto()
    assert dto.limit == 10
    assert dto.offset == 0
    assert dto.account_id is None
    assert dto.source is None


@pytest.mark.parametrize("limit", [0, 600])
def test_filter_profile_records_dto_invalid_limit(limit):
    """
    Test that FilterProfileRecordsDto enforces limit boundaries (1–500).
    """
    with pytest.raises(ValidationError):
        FilterProfileRecordsDto(limit=limit)


def test_filter_profile_records_dto_invalid_source():
    """
    Test that FilterProfileRecordsDto rejects invalid source.
    """
    with pytest.raises(ValidationError):
        FilterProfileRecordsDto(source="botnet")
