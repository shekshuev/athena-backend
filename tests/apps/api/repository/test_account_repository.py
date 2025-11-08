import re

import psycopg
import pytest

from apps.api.repository.account_repository import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    AccountRepositoryError,
)
from shared.models.account import CreateAccountDto, ReadAccountDto, UpdateAccountDto


@pytest.mark.asyncio
async def test_create_account_success(account_repository, mock_cursor, mock_account):
    """
    Test that `create_account()` successfully inserts a new account into the database.

    This test verifies:
      - The repository executes the expected SQL INSERT statement.
      - The correct parameter values are passed to the query.
      - The method returns a valid `ReadAccountDto` object with correct data.

    Steps:
      1. Mock the cursor's `fetchone()` to simulate a DB returning a new account row.
      2. Call `create_account()` with a valid DTO.
      3. Assert the returned object and SQL execution details.
    """
    dto = CreateAccountDto(
        email=mock_account["email"], password_hash=mock_account["password_hash"]
    )

    mock_cursor.fetchone.return_value = mock_account

    result = await account_repository.create_account(dto)

    assert isinstance(result, ReadAccountDto)
    assert result.email == dto.email

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert "INSERT INTO accounts" in sql
    assert params == (dto.email,)


@pytest.mark.asyncio
async def test_create_account_unique_violation(account_repository, mock_cursor):
    """
    Test that `create_account()` raises `AccountAlreadyExistsError` when a unique
    constraint violation occurs (duplicate email).

    Steps:
      1. Mock `execute()` to raise `psycopg.errors.UniqueViolation`.
      2. Ensure `AccountAlreadyExistsError` is raised.
    """
    dto = CreateAccountDto(email="john.doe@example.com", password_hash="some_hash")

    mock_cursor.execute.side_effect = psycopg.errors.UniqueViolation("duplicate key")

    with pytest.raises(AccountAlreadyExistsError):
        await account_repository.create_account(dto)


@pytest.mark.asyncio
async def test_create_account_unknown_error(account_repository, mock_cursor):
    """
    Test that `create_account()` raises `AccountRepositoryError` for unknown database errors.

    Steps:
      1. Mock `execute()` to raise a generic `psycopg.errors.Error`.
      2. Ensure `AccountRepositoryError` is raised.
    """
    dto = CreateAccountDto(email="john.doe@example.com", password_hash="some_hash")

    mock_cursor.execute.side_effect = psycopg.errors.Error("connection failure")

    with pytest.raises(AccountRepositoryError):
        await account_repository.create_account(dto)


@pytest.mark.asyncio
async def test_get_all_accounts_success(account_repository, mock_cursor, mock_accounts):
    """
    Test that `get_all_accounts()` successfully retrieves a paginated list of accounts.

    This test verifies:
      - The repository executes the expected SQL SELECT query.
      - The method returns a list of `ReadAccountDto` objects.
      - The SQL query includes correct pagination parameters (OFFSET and LIMIT).

    Steps:
      1. Mock the cursor's `fetchall()` to return a list of account rows.
      2. Call `get_all_accounts()` with `limit` and `offset`.
      3. Assert that the returned list matches the expected data and structure.
      4. Verify the executed SQL and parameters.
    """

    mock_cursor.fetchall.return_value = mock_accounts

    limit = 10
    offset = 5
    result = await account_repository.get_all_accounts(limit=limit, offset=offset)

    assert isinstance(result, list)
    assert all(isinstance(u, ReadAccountDto) for u in result)
    assert result[0].email == mock_accounts[0]["email"]
    assert result[1].email == mock_accounts[1]["email"]

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert re.search(
        r"select\s+.*from\s+accounts.+deleted_at\s+is\s+null",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )

    assert params == (offset, limit)


@pytest.mark.asyncio
async def test_get_all_accounts_database_error(account_repository, mock_cursor):
    """
    Test that `get_all_account()` raises `AccountRepositoryError`
    when a database error occurs during query execution.

    Steps:
      1. Mock `execute()` to raise `psycopg.errors.Error`.
      2. Assert that `AccountRepositoryError` is raised.
    """

    mock_cursor.execute.side_effect = psycopg.errors.Error("database error")

    with pytest.raises(AccountRepositoryError):
        await account_repository.get_all_accounts(limit=10, offset=0)


@pytest.mark.asyncio
async def test_get_account_by_id_success(account_repository, mock_cursor, mock_account):
    """
    Test that `get_account_by_id()` successfully retrieves an account by ID.

    This test verifies:
      - The repository executes the expected SELECT query.
      - The returned result is an instance of `ReadAccountDto`.
      - The correct SQL parameters are passed.

    Steps:
      1. Mock the cursor's `fetchone()` to return a valid account row.
      2. Call `get_account_by_id()` with a test account ID.
      3. Assert that the returned DTO contains correct data.
      4. Verify that the SQL query structure and parameters are correct.
    """
    mock_cursor.fetchone.return_value = mock_account
    result = await account_repository.get_account_by_id(mock_account["id"])

    assert isinstance(result, ReadAccountDto)
    assert result.email == mock_account["email"]

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"select\s+.*from\s+accounts.*id\s*=\s*%s.*",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert re.search(
        r"select\s+.*from\s+accounts.*deleted_at\s+is\s+null.*",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )

    assert params == (mock_account["id"],)


@pytest.mark.asyncio
async def test_get_account_by_id_not_found(account_repository, mock_cursor):
    """
    Test that `get_account_by_id()` raises `AccountNotFoundError` when no account is found.
    """

    mock_cursor.fetchone.return_value = None

    with pytest.raises(AccountNotFoundError):
        await account_repository.get_account_by_id("000000-0000-0000-0000-000000000000")

    mock_cursor.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_account_by_id_unknown_error(account_repository, mock_cursor):
    """
    Test that `get_account_by_id()` raises `AccountRepositoryError` on unexpected DB exceptions.
    """
    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(AccountRepositoryError):
        await account_repository.get_account_by_id("000000-0000-0000-0000-000000000000")


@pytest.mark.asyncio
async def test_get_account_by_email_success(
    account_repository, mock_cursor, mock_account
):
    """
    Test that `get_account_by_email()` successfully retrieves a account by email.

    This test verifies:
      - The repository executes the expected SELECT query.
      - The returned result is a valid `ReadAccountDto`.
      - SQL query includes correct WHERE conditions for email and deleted_at.

    Steps:
      1. Mock the cursor's `fetchone()` to return a fake account row.
      2. Call `get_account_by_email()` with a test email.
      3. Assert that the returned object matches expected fields.
      4. Verify SQL text and parameters passed to the cursor.
    """

    mock_cursor.fetchone.return_value = mock_account

    result = await account_repository.get_account_by_email(mock_account["email"])

    assert isinstance(result, ReadAccountDto)
    assert result.email == mock_account["email"]
    assert result.id == "000000-0000-0000-0000-000000000000"

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"select\s+.*from\s+accounts",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert re.search(
        r"email\s*=\s*%s",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert re.search(
        r"deleted_at\s+is\s+null",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )

    assert params == (mock_account["email"],)


@pytest.mark.asyncio
async def test_get_account_by_email_not_found(account_repository, mock_cursor):
    """
    Test that `get_account_by_email()` raises `AccountNotFoundError`
    when the account does not exist or is soft-deleted.
    """

    mock_cursor.fetchone.return_value = None
    with pytest.raises(AccountNotFoundError):
        await account_repository.get_account_by_email("account@example.ru")


@pytest.mark.asyncio
async def test_get_account_by_email_db_error(account_repository, mock_cursor):
    """
    Test that `get_account_by_email()` raises `AccountRepositoryError`
    when a generic database error occurs.
    """
    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(AccountRepositoryError):
        await account_repository.get_account_by_email("account@example.ru")


@pytest.mark.asyncio
async def test_update_account_success(account_repository, mock_cursor, mock_account):
    """
        Test that `update_account()` successfully updates account data.

        Verifies:
          - Model validation passes for correct input.
          - SQL query is dynamically constructed with correct fields.
          - Result is a valid `ReadAccountDto`.
    s
        Steps:
          1. Create a valid `UpdateAccountDto`.
          2. Mock the cursor's return value with updated account data.
          3. Call `update_account()` and verify result + SQL structure.
    """

    mock_cursor.fetchone.return_value = mock_account

    dto = UpdateAccountDto(
        email="changed@example.com",
        status="blocked",
    )

    result = await account_repository.update_account(
        account_id=mock_account["id"], dto=dto
    )

    assert isinstance(result, ReadAccountDto)
    assert result.email == mock_account["email"]

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(r"update\s+accounts\s+set", sql, re.IGNORECASE)
    assert re.search(r"email\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"status\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"where\s+id\s*=\s*%s", sql, re.IGNORECASE)
    assert re.search(r"deleted_at\s+is\s+null", sql, re.IGNORECASE)

    assert params[-1] == mock_account["id"]


@pytest.mark.asyncio
async def test_update_account_db_error(account_repository, mock_cursor):
    """
    Test that `update_account()` raises `accountRepositoryError`
    when a database exception occurs.
    """

    mock_cursor.execute.side_effect = psycopg.errors.Error("syntax error in SQL")

    dto = UpdateAccountDto(
        email="changed@example.com",
        status="blocked",
    )

    with pytest.raises(AccountRepositoryError):
        await account_repository.update_account(
            account_id="000000-0000-0000-0000-000000000000", dto=dto
        )


@pytest.mark.asyncio
async def test_delete_account_success(account_repository, mock_cursor):
    """
    Test that `delete_account()` performs a soft delete successfully.

    This test verifies:
      - The repository executes the correct UPDATE query.
      - The query includes the correct `WHERE` and `SET` clauses.
      - No exceptions are raised for a valid deletion.

    Steps:
      1. Mock the cursor's `rowcount` to simulate one updated row.
      2. Call `delete_account()` with a valid account ID.
      3. Assert that the correct SQL query and parameters were used.
    """

    mock_cursor.rowcount = 1
    account_id = "000000-0000-0000-0000-000000000000"

    await account_repository.delete_account(account_id)

    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]

    assert re.search(
        r"update\s+accounts.*set\s+deleted_at\s*=\s*now",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    ), f"SQL missing SET deleted_at clause:\n{sql}"

    assert re.search(
        r"where\s+id\s*=\s*%s.*deleted_at\s+is\s+null",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    ), f"SQL missing WHERE id and deleted_at filter:\n{sql}"

    assert params == (account_id,)


@pytest.mark.asyncio
async def test_delete_account_not_found(account_repository, mock_cursor):
    """
    Test that `delete_account()` raises AccountNotFoundError when no rows are affected.

    Steps:
      1. Mock cursor to return `rowcount = 0`.
      2. Call `delete_account()` with a non-existent account ID.
      3. Expect `AccountNotFoundError` to be raised.
    """
    mock_cursor.rowcount = 0
    account_id = "000000-0000-0000-0000-000000000000"

    with pytest.raises(AccountNotFoundError):
        await account_repository.delete_account(account_id)


@pytest.mark.asyncio
async def test_delete_account_unknown_error(account_repository, mock_cursor):
    """
    Test that `delete_account()` raises AccountRepositoryError for generic DB failures.

    Steps:
      1. Mock cursor.execute() to raise a psycopg generic error.
      2. Call `delete_account()`.
      3. Expect `AccountRepositoryError` to be raised.
    """

    mock_cursor.execute.side_effect = psycopg.errors.Error("connection lost")

    with pytest.raises(AccountRepositoryError):
        await account_repository.delete_account("000000-0000-0000-0000-000000000000")
