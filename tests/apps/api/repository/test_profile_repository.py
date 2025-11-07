import re

import psycopg
import pytest

from apps.api.repository.profile_repository import (
    ProfileConflictError,
    ProfileNotFoundError,
    ProfileRepositoryError,
)
from shared.models.profile import (
    CreateProfileRecordDto,
    FilterProfileRecordsDto,
    ProfileKVInput,
    ReadProfileRecordDto,
    UpdateProfileRecordDto,
    UpsertProfileRecordsDto,
)


@pytest.mark.asyncio
async def test_create_record_success(
    profile_repository, mock_cursor, mock_profile_record
):
    """
    Test that `create_record()` successfully inserts a new profile record.

    Steps:
      1. Mock `fetchone()` to return the created row.
      2. Call `create_record()` with valid DTO.
      3. Assert returned DTO and SQL query details.
    """
    dto = CreateProfileRecordDto(
        account_id=mock_profile_record["account_id"],
        key=mock_profile_record["key"],
        value=mock_profile_record["value"],
        source=mock_profile_record["source"],
    )

    mock_cursor.fetchone.return_value = mock_profile_record

    result = await profile_repository.create_record(dto)

    assert isinstance(result, ReadProfileRecordDto)
    assert result.key == dto.key
    assert result.value == dto.value
    assert result.source == dto.source

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert re.search(r"insert\s+into\s+profiles", sql, re.IGNORECASE)
    assert params == (dto.account_id, dto.key, dto.value, dto.source)


@pytest.mark.asyncio
async def test_create_record_unique_violation(profile_repository, mock_cursor):
    """
    Test that `create_record()` raises `ProfileConflictError` on unique violation.
    """
    dto = CreateProfileRecordDto(
        account_id="00000000-0000-0000-0000-000000000000",
        key="first_name",
        value="John",
        source="user",
    )

    mock_cursor.execute.side_effect = psycopg.errors.UniqueViolation("duplicate key")

    with pytest.raises(ProfileConflictError):
        await profile_repository.create_record(dto)


@pytest.mark.asyncio
async def test_create_record_foreign_key_error(profile_repository, mock_cursor):
    """
    Test that `create_record()` raises `ProfileRepositoryError` when account_id FK fails.
    """
    dto = CreateProfileRecordDto(
        account_id="deadbeef-dead-beef-dead-beefdeadbeef",
        key="first_name",
        value="John",
        source="user",
    )

    mock_cursor.execute.side_effect = psycopg.errors.ForeignKeyViolation("invalid FK")

    with pytest.raises(ProfileRepositoryError):
        await profile_repository.create_record(dto)


@pytest.mark.asyncio
async def test_create_record_unknown_error(profile_repository, mock_cursor):
    """
    Test that `create_record()` raises `ProfileRepositoryError` for generic DB errors.
    """
    dto = CreateProfileRecordDto(
        account_id="00000000-0000-0000-0000-000000000000",
        key="first_name",
        value="John",
        source="user",
    )

    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(ProfileRepositoryError):
        await profile_repository.create_record(dto)


@pytest.mark.asyncio
async def test_get_record_by_id_success(
    profile_repository, mock_cursor, mock_profile_record
):
    """
    Test that `get_record_by_id()` returns a valid record.
    """
    mock_cursor.fetchone.return_value = mock_profile_record

    result = await profile_repository.get_record_by_id(mock_profile_record["id"])

    assert isinstance(result, ReadProfileRecordDto)
    assert result.key == mock_profile_record["key"]
    assert result.value == mock_profile_record["value"]

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert re.search(r"select\s+\*\s+from\s+profiles", sql, re.IGNORECASE)
    assert params == (mock_profile_record["id"],)


@pytest.mark.asyncio
async def test_get_record_by_id_not_found(profile_repository, mock_cursor):
    """
    Test that `get_record_by_id()` raises `ProfileNotFoundError` when no record found.
    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ProfileNotFoundError):
        await profile_repository.get_record_by_id(
            "11111111-1111-1111-1111-111111111111"
        )

    mock_cursor.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_record_by_id_db_error(profile_repository, mock_cursor):
    """
    Test that `get_record_by_id()` raises `ProfileRepositoryError` for DB failures.
    """
    mock_cursor.execute.side_effect = psycopg.errors.Error("timeout")

    with pytest.raises(ProfileRepositoryError):
        await profile_repository.get_record_by_id(
            "11111111-1111-1111-1111-111111111111"
        )


@pytest.mark.asyncio
async def test_update_record_success(
    profile_repository, mock_cursor, mock_profile_record
):
    """
    Test that `update_record()` updates value and source correctly.
    """
    mock_cursor.fetchone.return_value = mock_profile_record

    dto = UpdateProfileRecordDto(value="Jane", source="system")

    result = await profile_repository.update_record(mock_profile_record["id"], dto)

    assert isinstance(result, ReadProfileRecordDto)
    assert result.value == mock_profile_record["value"]

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert re.search(r"update\s+profiles\s+set", sql, re.IGNORECASE)
    assert re.search(r"value\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"source\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"where\s+id\s*=\s*%s", sql, re.IGNORECASE)
    assert params[-1] == mock_profile_record["id"]


@pytest.mark.asyncio
async def test_update_record_not_found(profile_repository, mock_cursor):
    """
    Test that `update_record()` raises ProfileNotFoundError if record not found.
    """
    mock_cursor.fetchone.return_value = None

    dto = UpdateProfileRecordDto(value="Jane")
    with pytest.raises(ProfileNotFoundError):
        await profile_repository.update_record(
            "11111111-1111-1111-1111-111111111111", dto
        )


@pytest.mark.asyncio
async def test_update_record_db_error(profile_repository, mock_cursor):
    """
    Test that `update_record()` raises ProfileRepositoryError on DB failure.
    """
    dto = UpdateProfileRecordDto(value="Jane")
    mock_cursor.execute.side_effect = psycopg.errors.Error("syntax error")

    with pytest.raises(ProfileRepositoryError):
        await profile_repository.update_record(
            "11111111-1111-1111-1111-111111111111", dto
        )


@pytest.mark.asyncio
async def test_delete_record_success(profile_repository, mock_cursor):
    """
    Test that `delete_record()` deletes record successfully.
    """
    mock_cursor.rowcount = 1
    record_id = "11111111-1111-1111-1111-111111111111"

    await profile_repository.delete_record(record_id)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert re.search(r"delete\s+from\s+profiles", sql, re.IGNORECASE)
    assert params == (record_id,)


@pytest.mark.asyncio
async def test_delete_record_not_found(profile_repository, mock_cursor):
    """
    Test that `delete_record()` raises ProfileNotFoundError if no row affected.
    """
    mock_cursor.rowcount = 0
    record_id = "11111111-1111-1111-1111-111111111111"

    with pytest.raises(ProfileNotFoundError):
        await profile_repository.delete_record(record_id)


@pytest.mark.asyncio
async def test_delete_record_db_error(profile_repository, mock_cursor):
    """
    Test that `delete_record()` raises ProfileRepositoryError on DB exception.
    """
    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(ProfileRepositoryError):
        await profile_repository.delete_record("11111111-1111-1111-1111-111111111111")


@pytest.mark.asyncio
async def test_get_records_success(
    profile_repository, mock_cursor, mock_profile_records
):
    """
    Test that `get_records()` retrieves records filtered by account and source.
    """
    mock_cursor.fetchall.return_value = mock_profile_records

    dto = FilterProfileRecordsDto(
        account_id="00000000-0000-0000-0000-000000000000",
        source="user",
        limit=5,
        offset=0,
    )

    result = await profile_repository.get_records(dto)

    assert isinstance(result, list)
    assert all(isinstance(r, ReadProfileRecordDto) for r in result)
    assert result[0].key == mock_profile_records[0]["key"]

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert re.search(r"select\s+\*\s+from\s+profiles", sql, re.IGNORECASE)
    assert "where" in sql.lower()
    assert "limit" in sql.lower()
    assert "offset" in sql.lower()
    assert params[-2:] == [dto.limit, dto.offset]


@pytest.mark.asyncio
async def test_get_records_db_error(profile_repository, mock_cursor):
    """
    Test that `get_records()` raises ProfileRepositoryError on DB exception.
    """
    dto = FilterProfileRecordsDto(account_id="0000", source="user")
    mock_cursor.execute.side_effect = psycopg.errors.Error("bad query")

    with pytest.raises(ProfileRepositoryError):
        await profile_repository.get_records(dto)


@pytest.mark.asyncio
async def test_upsert_records_success(
    profile_repository, mock_cursor, mock_profile_records
):
    """
    Test that `upsert_records()` performs batch insert/update successfully.
    """
    dto = UpsertProfileRecordsDto(
        account_id=mock_profile_records[0]["account_id"],
        records=[
            ProfileKVInput(key="first_name", value="John", source="user"),
            ProfileKVInput(key="last_name", value="Doe", source="system"),
        ],
    )

    async def fake_iter():
        for row in mock_profile_records:
            yield row

    mock_cursor.__aiter__.return_value = fake_iter()
    mock_cursor.__aiter__.side_effect = None

    result = await profile_repository.upsert_records(dto)

    assert isinstance(result, list)
    assert all(isinstance(r, ReadProfileRecordDto) for r in result)

    mock_cursor.executemany.assert_called_once()
    sql, values = mock_cursor.executemany.call_args[0]
    assert re.search(r"insert\s+into\s+profiles", sql, re.IGNORECASE)
    assert re.search(r"on\s+conflict", sql, re.IGNORECASE)
    assert len(values) == len(dto.records)


@pytest.mark.asyncio
async def test_upsert_records_db_error(profile_repository, mock_cursor):
    """
    Test that `upsert_records()` raises ProfileRepositoryError on DB failure.
    """
    dto = UpsertProfileRecordsDto(
        account_id="00000000-0000-0000-0000-000000000000",
        records=[ProfileKVInput(key="first_name", value="John", source="user")],
    )

    mock_cursor.executemany.side_effect = psycopg.errors.Error("insert error")

    with pytest.raises(ProfileRepositoryError):
        await profile_repository.upsert_records(dto)
