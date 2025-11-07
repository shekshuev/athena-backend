from uuid import UUID

import psycopg.errors
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from shared.models.account import (
    CreateAccountDto,
    ReadAccountDto,
    UpdateAccountDto,
)


class AccountAlreadyExistsError(Exception):
    """
    Raised when attempting to create a new account whose email already exists.

    Typically corresponds to a `UniqueViolation` error on the `email` column
    in the `accounts` table.
    """

    ...


class AccountNotFoundError(Exception):
    """
    Raised when a account cannot be found in the database.

    This can occur when:
      - The account ID or email does not exist.
      - The account has been soft-deleted (`deleted_at IS NOT NULL`).
    """

    ...


class AccountRepositoryError(Exception):
    """
    General fallback exception for unexpected or unclassified database errors
    occurring in account-related queries.

    This ensures that upper layers (services, controllers) can handle all
    repository-level failures through a unified interface.
    """

    ...


class AccountRepository:
    """
    Repository responsible for managing `accounts` and authentication-related data.

    This repository provides low-level CRUD operations for account records,
    using psycopg connection pooling and explicit SQL queries instead of an ORM.

    """

    def __init__(self, pool: AsyncConnectionPool):
        """
        Initialize the repository with a database connection pool.

        Args:
            pool (ConnectionPool): A psycopg connection pool.
        """
        self.pool = pool

    async def create_account(self, dto: CreateAccountDto) -> ReadAccountDto:
        """
        Insert a new account into the database.

        Args:
            dto (CreateAccountDto): Data for the new account.

        Returns:
            ReadAccountDto: The created account data.

        Raises:
            AccountAlreadyExistsError: If email already exists.
            AccountRepositoryError: For any other database error.
        """
        query = """
            INSERT INTO accounts (email)
            VALUES (%s)
            RETURNING *;
        """
        values = (dto.email,)

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    return ReadAccountDto(**row)
        except psycopg.errors.UniqueViolation as e:
            raise AccountAlreadyExistsError("Account already exists") from e
        except psycopg.errors.Error as e:
            raise AccountRepositoryError("Unknown error") from e

    async def get_all_accounts(self, limit: int, offset: int) -> list[ReadAccountDto]:
        """
        Retrieve a paginated list of active accounts (not soft-deleted).

        Args:
            limit (int): Max number of accounts to return.
            offset (int): Number of accounts to skip.

        Returns:
            list[ReadAccountDto]: List of account objects.

        Raises:
            AccountRepositoryError: For any database error.
        """
        query = """
            SELECT *
            FROM accounts
            WHERE deleted_at IS NULL
            OFFSET %s LIMIT %s;
        """
        params = (offset, limit)

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, params)
                    rows = await cur.fetchall()
                    return [ReadAccountDto(**row) for row in rows]
        except psycopg.errors.Error as e:
            raise AccountRepositoryError("Unknown error") from e

    async def get_account_by_id(self, account_id: UUID) -> ReadAccountDto:
        """
        Retrieve an account by ID.

        Args:
            account_id (int): The account's ID.

        Returns:
            ReadAccountDto: Account data.

        Raises:
            AccountNotFoundError: If the account does not exist or is deleted.
            AccountRepositoryError: For any database error.
        """
        query = """
            SELECT *
            FROM accounts
            WHERE id = %s AND deleted_at IS NULL;
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (account_id,))
                    result = await cur.fetchone()

                    if result is None:
                        raise AccountNotFoundError("Account not found")
                    return ReadAccountDto(**result)
        except psycopg.errors.Error as e:
            raise AccountRepositoryError("Unknown error") from e

    async def get_account_by_email(self, email: str) -> ReadAccountDto:
        """
        Retrieve a account by email.

        Args:
            email (str): The email to look up.

        Returns:
            ReadAccountDto: Account data.

        Raises:
            AccountNotFoundError: If the account does not exist or is deleted.
            AccountRepositoryError: For any database error.
        """
        query = """
            SELECT *
            FROM accounts
            WHERE email = %s AND deleted_at IS NULL;
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (email,))
                    result = await cur.fetchone()

                    if result is None:
                        raise AccountNotFoundError("Account not found")
                    return ReadAccountDto(**result)
        except psycopg.errors.Error as e:
            raise AccountRepositoryError("Unknown error") from e

    async def update_account(
        self, account_id: UUID, dto: UpdateAccountDto
    ) -> ReadAccountDto:
        """
        Update fields of an existing account.

        Args:
            account_id (int): The account's ID.
            dto (UpdateAccountDto): Data with fields to update.

        Returns:
            ReadAccountDto: Updated account data.

        Raises:
            AccountNotFoundError: If the account does not exist or is deleted.
            AccountRepositoryError: For any database error.
        """
        fields = []
        values = []

        if dto.email is not None:
            fields.append("email = %s")
            values.append(dto.email)
        if dto.status is not None:
            fields.append("status = %s")
            values.append(dto.status)

        fields.append("updated_at = NOW()")
        values.append(account_id)

        query = f"""
            UPDATE accounts
            SET {", ".join(fields)}
            WHERE id = %s AND deleted_at IS NULL
            RETURNING *;
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, values)
                    result = await cur.fetchone()

                    if result is None:
                        raise AccountNotFoundError("Account not found")

                    return ReadAccountDto(**result)

        except psycopg.errors.Error as e:
            raise AccountRepositoryError("Unknown error") from e

    async def delete_account(self, account_id: UUID) -> None:
        """
        Soft-delete an account by setting deleted_at timestamp.

        Args:
            account_id (int): The account's ID.

        Raises:
            AccountNotFoundError: If the account does not exist or is already deleted.
            AccountRepositoryError: For any database error.
        """
        query = """
            UPDATE accounts
            SET deleted_at = NOW()
            WHERE id = %s AND deleted_at IS NULL;
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, (account_id,))
                    if cur.rowcount == 0:
                        raise AccountNotFoundError("Account not found")

        except psycopg.errors.Error as e:
            raise AccountRepositoryError("Unknown error") from e
