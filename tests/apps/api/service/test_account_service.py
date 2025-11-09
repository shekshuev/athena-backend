import pytest

from apps.api.repository.account_repository import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    AccountRepositoryError,
)
from apps.api.service.account_service import (
    AccountService,
    AccountServiceError,
    PasswordMismatchError,
)
from shared.models.account import ReadAccountDto, RegisterAccountDto, UpdateAccountDto


@pytest.mark.asyncio
async def test_create_account_success(
    mock_account_repository, mock_account_dto, monkeypatch
):
    """
    Test that `create_account()` successfully registers a new account.

    Steps:
      1. Prepare a valid RegisterAccountDto.
      2. Mock repository's `create_account()` to return a ReadAccountDto.
      3. Call the service method.
      4. Verify the returned object and repository call.

    Expected:
      - Repository called once with correct parameters.
      - Returned object is a valid ReadAccountDto.
    """
    service = AccountService(mock_account_repository)
    dto = RegisterAccountDto(
        email=mock_account_dto.email, password="123456", confirm_password="123456"
    )

    hashed_pw = "hashed_pw"

    monkeypatch.setattr(
        "apps.api.service.account_service.hash_password", lambda _: hashed_pw
    )

    mock_account_repository.create_account.return_value = mock_account_dto

    result = await service.create_account(dto)

    call_args = mock_account_repository.create_account.call_args[0][0]
    assert call_args.password_hash == hashed_pw
    assert call_args.email == dto.email

    mock_account_repository.create_account.assert_called_once()
    assert isinstance(result, ReadAccountDto)
    assert result.email == dto.email


@pytest.mark.asyncio
async def test_create_account_password_mismatch(mock_account_repository):
    """
    Test that `create_account()` raises PasswordMismatchError
    when password and confirm_password do not match.

    Steps:
      1. Prepare a DTO with mismatching passwords.
      2. Call `create_account()`.
      3. Expect PasswordMismatchError.
    """
    service = AccountService(mock_account_repository)
    dto = RegisterAccountDto(
        email="user@example.com", password="123456", confirm_password="456789"
    )

    with pytest.raises(PasswordMismatchError):
        await service.create_account(dto)

    mock_account_repository.create_account.assert_not_called()


@pytest.mark.asyncio
async def test_create_account_duplicate_email(mock_account_repository):
    """
    Test that `create_account()` raises AccountServiceError
    when AccountAlreadyExistsError is raised by repository.

    Steps:
      1. Mock repository to raise AccountAlreadyExistsError.
      2. Call `create_account()`.
      3. Expect AccountServiceError with 'already exists' message.
    """
    service = AccountService(mock_account_repository)
    dto = RegisterAccountDto(
        email="dup@example.com", password="123456", confirm_password="123456"
    )

    mock_account_repository.create_account.side_effect = AccountAlreadyExistsError()

    with pytest.raises(AccountServiceError, match="already exists"):
        await service.create_account(dto)


@pytest.mark.asyncio
async def test_create_account_database_error(mock_account_repository):
    """
    Test that `create_account()` raises AccountServiceError
    when repository raises AccountRepositoryError.

    Steps:
      1. Mock repository to raise AccountRepositoryError.
      2. Call `create_account()`.
      3. Expect AccountServiceError with 'Database error' message.
    """
    service = AccountService(mock_account_repository)
    dto = RegisterAccountDto(
        email="db@example.com", password="123456", confirm_password="123456"
    )

    mock_account_repository.create_account.side_effect = AccountRepositoryError(
        "DB failed"
    )

    with pytest.raises(AccountServiceError, match="Database error"):
        await service.create_account(dto)


@pytest.mark.asyncio
async def test_get_account_by_id_success(mock_account_repository, mock_account_dto):
    """
    Test that `get_account_by_id()` successfully retrieves an account.

    Steps:
      1. Mock repository to return a valid ReadAccountDto.
      2. Call `get_account_by_id()` with UUID.
      3. Verify the returned object and repository call.
    """
    service = AccountService(mock_account_repository)

    mock_account_repository.get_account_by_id.return_value = mock_account_dto

    result = await service.get_account_by_id(mock_account_dto.id)

    mock_account_repository.get_account_by_id.assert_called_once_with(
        mock_account_dto.id
    )
    assert isinstance(result, ReadAccountDto)
    assert result.id == str(mock_account_dto.id)


@pytest.mark.asyncio
async def test_get_account_by_id_not_found(mock_account_repository):
    """
    Test that `get_account_by_id()` raises AccountServiceError
    when repository raises AccountNotFoundError.

    Steps:
      1. Mock repository to raise AccountNotFoundError.
      2. Call `get_account_by_id()`.
      3. Expect AccountServiceError with 'not found' message.
    """
    service = AccountService(mock_account_repository)
    account_id = "00000000-0000-0000-0000-000000000002"

    mock_account_repository.get_account_by_id.side_effect = AccountNotFoundError()

    with pytest.raises(AccountServiceError, match="not found"):
        await service.get_account_by_id(account_id)


@pytest.mark.asyncio
async def test_get_account_by_id_database_error(mock_account_repository):
    """
    Test that `get_account_by_id()` raises AccountServiceError
    when repository raises AccountRepositoryError.
    """
    service = AccountService(mock_account_repository)
    account_id = "00000000-0000-0000-0000-000000000003"

    mock_account_repository.get_account_by_id.side_effect = AccountRepositoryError(
        "DB issue"
    )

    with pytest.raises(AccountServiceError, match="Database error"):
        await service.get_account_by_id(account_id)


@pytest.mark.asyncio
async def test_get_all_accounts_success(mock_account_repository, mock_account_dtos):
    """
    Test that `get_all_accounts()` retrieves a list of accounts successfully.

    Steps:
      1. Mock repository to return multiple ReadAccountDto objects.
      2. Call `get_all_accounts()` with pagination params.
      3. Verify returned list and repository call.
    """
    service = AccountService(mock_account_repository)

    mock_account_repository.get_all_accounts.return_value = mock_account_dtos

    result = await service.get_all_accounts(limit=10, offset=0)

    mock_account_repository.get_all_accounts.assert_called_once_with(limit=10, offset=0)
    assert len(result) == 2
    assert all(isinstance(acc, ReadAccountDto) for acc in result)


@pytest.mark.asyncio
async def test_get_all_accounts_database_error(mock_account_repository):
    """
    Test that `get_all_accounts()` raises AccountServiceError
    when repository raises AccountRepositoryError.
    """
    service = AccountService(mock_account_repository)
    mock_account_repository.get_all_accounts.side_effect = AccountRepositoryError("DB")

    with pytest.raises(AccountServiceError, match="Database error"):
        await service.get_all_accounts()


@pytest.mark.asyncio
async def test_update_account_success(mock_account_repository, mock_account_dto):
    """
    Test that `update_account()` successfully updates account data.

    Steps:
      1. Mock repository to return updated ReadAccountDto.
      2. Call `update_account()` with valid data.
      3. Verify result and repository call.
    """
    service = AccountService(mock_account_repository)
    dto = UpdateAccountDto(email="updated@example.com")

    mock_account_dto.email = dto.email

    mock_account_repository.update_account.return_value = mock_account_dto

    result = await service.update_account(mock_account_dto.id, dto)

    mock_account_repository.update_account.assert_called_once_with(
        mock_account_dto.id, dto
    )
    assert isinstance(result, ReadAccountDto)
    assert result.email == dto.email


@pytest.mark.asyncio
async def test_update_account_not_found(mock_account_repository):
    """
    Test that `update_account()` raises AccountServiceError
    when repository raises AccountNotFoundError.
    """
    service = AccountService(mock_account_repository)
    account_id = "00000000-0000-0000-0000-000000000011"
    dto = UpdateAccountDto(email="missing@example.com")

    mock_account_repository.update_account.side_effect = AccountNotFoundError()

    with pytest.raises(AccountServiceError, match="not found"):
        await service.update_account(account_id, dto)


@pytest.mark.asyncio
async def test_update_account_database_error(mock_account_repository):
    """
    Test that `update_account()` raises AccountServiceError
    when repository raises AccountRepositoryError.
    """
    service = AccountService(mock_account_repository)
    account_id = "00000000-0000-0000-0000-000000000012"
    dto = UpdateAccountDto(email="broken@example.com")

    mock_account_repository.update_account.side_effect = AccountRepositoryError("DB")

    with pytest.raises(AccountServiceError, match="Database error"):
        await service.update_account(account_id, dto)


@pytest.mark.asyncio
async def test_delete_account_success(mock_account_repository):
    """
    Test that `delete_account()` performs deletion successfully.

    Steps:
      1. Call `delete_account()` with valid ID.
      2. Verify repository called once.
      3. Expect no exceptions raised.
    """
    service = AccountService(mock_account_repository)
    account_id = "00000000-0000-0000-0000-000000000013"

    await service.delete_account(account_id)

    mock_account_repository.delete_account.assert_called_once_with(account_id)


@pytest.mark.asyncio
async def test_delete_account_not_found(mock_account_repository):
    """
    Test that `delete_account()` raises AccountServiceError
    when repository raises AccountNotFoundError.
    """
    service = AccountService(mock_account_repository)
    account_id = "00000000-0000-0000-0000-000000000014"

    mock_account_repository.delete_account.side_effect = AccountNotFoundError()

    with pytest.raises(AccountServiceError, match="not found"):
        await service.delete_account(account_id)


@pytest.mark.asyncio
async def test_delete_account_database_error(mock_account_repository):
    """
    Test that `delete_account()` raises AccountServiceError
    when repository raises AccountRepositoryError.
    """
    service = AccountService(mock_account_repository)
    account_id = "00000000-0000-0000-0000-000000000015"

    mock_account_repository.delete_account.side_effect = AccountRepositoryError("DB")

    with pytest.raises(AccountServiceError, match="Database error"):
        await service.delete_account(account_id)
