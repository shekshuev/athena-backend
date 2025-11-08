import logging
from typing import List
from uuid import UUID

from apps.api.repository.account_repository import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    AccountRepository,
    AccountRepositoryError,
)
from shared.models.account import (
    CreateAccountDto,
    ReadAccountDto,
    RegisterAccountDto,
    UpdateAccountDto,
)
from shared.security.password import hash_password

logger = logging.getLogger(__name__)


class AccountServiceError(Exception):
    """Base class for AccountService errors."""


class PasswordMismatchError(AccountServiceError):
    """Raised when password and confirm_password do not match."""


class AccountService:
    """
    The AccountService acts as a chronicler of user accounts,
    governing their creation, retrieval, modification, and removal.

    Beyond merely storing data, it safeguards the integrity of the
    registration process through password validation and secure hashing.
    """

    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo
        logger.info("📘 AccountService initialized — the chronicles begin.")

    async def create_account(self, dto: RegisterAccountDto) -> ReadAccountDto:
        """
        Register a new account.

        The process unfolds in several deliberate steps:

        1. Passwords are compared to ensure harmony between input fields.
        2. If aligned, the password is sealed with a cryptographic hash.
        3. The data is handed to the repository for inscription into the database.
        4. The newly forged account record is returned to the caller.

        Raises:
            PasswordMismatchError: when password and confirmation do not align.
            AccountServiceError: when persistence errors occur.
        """
        logger.info("Initiating registration for email=%s", dto.email)

        if dto.password != dto.confirm_password:
            logger.warning(
                "Password mismatch detected for email=%s — registration aborted.",
                dto.email,
            )
            raise PasswordMismatchError("Passwords do not match")

        logger.debug("🔒 Passwords verified — proceeding to hash.")
        password_hash = hash_password(dto.password)

        repo_dto = CreateAccountDto(email=dto.email, password_hash=password_hash)
        logger.debug(
            "Account DTO prepared for repository insertion: email=%s", dto.email
        )

        try:
            account = await self.account_repo.create_account(repo_dto)
            logger.info(
                "Account successfully registered: id=%s email=%s",
                account.id,
                account.email,
            )
            return account
        except AccountAlreadyExistsError as e:
            logger.warning("Duplicate email detected: %s", dto.email)
            raise AccountServiceError("Account with this email already exists") from e
        except AccountRepositoryError as e:
            logger.error(
                "Repository error while creating account for email=%s: %s",
                dto.email,
                str(e),
            )
            raise AccountServiceError("Database error while creating account") from e

    async def get_account_by_id(self, account_id: UUID) -> ReadAccountDto:
        logger.debug("Fetching account by id=%s", account_id)

        try:
            account = await self.account_repo.get_account_by_id(account_id)
            logger.info("Account retrieved successfully: id=%s", account_id)
            return account
        except AccountNotFoundError:
            logger.warning("Account not found: id=%s", account_id)
            raise AccountServiceError("Account not found")
        except AccountRepositoryError as e:
            logger.error(
                "Database error while fetching account id=%s: %s", account_id, str(e)
            )
            raise AccountServiceError("Database error while fetching account") from e

    async def get_all_accounts(
        self, limit: int = 20, offset: int = 0
    ) -> List[ReadAccountDto]:
        logger.debug("Retrieving accounts list (limit=%s, offset=%s)", limit, offset)

        try:
            accounts = await self.account_repo.get_all_accounts(
                limit=limit, offset=offset
            )
            logger.info(
                "Retrieved %d account(s) from the archive (offset=%d)",
                len(accounts),
                offset,
            )
            return accounts
        except AccountRepositoryError as e:
            logger.error("Error fetching accounts list: %s", str(e))
            raise AccountServiceError("Database error while fetching accounts") from e

    async def update_account(
        self, account_id: UUID, dto: UpdateAccountDto
    ) -> ReadAccountDto:
        logger.info("✏️ Updating account id=%s with fields=%s", account_id, dto)

        try:
            account = await self.account_repo.update_account(account_id, dto)
            logger.info("Account successfully updated: id=%s", account_id)
            return account
        except AccountNotFoundError:
            logger.warning("Attempted to update non-existent account id=%s", account_id)
            raise AccountServiceError("Account not found")
        except AccountRepositoryError as e:
            logger.error(
                "Database error while updating account id=%s: %s", account_id, str(e)
            )
            raise AccountServiceError("Database error while updating account") from e

    async def delete_account(self, account_id: UUID) -> None:
        logger.info("🗑️ Initiating deletion for account id=%s", account_id)

        try:
            await self.account_repo.delete_account(account_id)
            logger.info("Account successfully deleted: id=%s", account_id)
        except AccountNotFoundError:
            logger.warning(
                "Deletion attempt failed — account not found: id=%s", account_id
            )
            raise AccountServiceError("Account not found")
        except AccountRepositoryError as e:
            logger.error(
                "Database error while deleting account id=%s: %s", account_id, str(e)
            )
            raise AccountServiceError("Database error while deleting account") from e
