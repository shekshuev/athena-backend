from typing import List
from uuid import UUID

import psycopg.errors
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from shared.models.profile import (
    CreateProfileRecordDto,
    FilterProfileRecordsDto,
    ReadProfileRecordDto,
    UpdateProfileRecordDto,
    UpsertProfileRecordsDto,
)


class ProfileConflictError(Exception):
    """
    Raised when attempting to insert a duplicate (account_id, key, source)
    combination, violating the unique constraint.
    """

    ...


class ProfileNotFoundError(Exception):
    """
    Raised when a profile record cannot be found in the database.

    This can occur when:
      - The given record ID does not exist.
      - The record was deleted.
    """

    ...


class ProfileRepositoryError(Exception):
    """
    General fallback exception for unexpected or unclassified database errors
    occurring in profile-related queries.

    This ensures that upper layers (services, controllers) can handle all
    repository-level failures through a unified interface.
    """

    ...


class ProfileRepository:
    """
    Repository responsible for managing `profiles` (key-value user data).

    Each record represents a single key-value pair linked to an account,
    identified uniquely by (account_id, key, source).
    """

    def __init__(self, pool: AsyncConnectionPool):
        """
        Initialize the repository with a database connection pool.

        Args:
            pool (ConnectionPool): A psycopg connection pool.
        """
        self.pool = pool

    async def create_record(self, dto: CreateProfileRecordDto) -> ReadProfileRecordDto:
        """
        Insert a new profile record into the database.

        Args:
            dto (CreateProfileRecordDto): Data for the new profile record.

        Returns:
            ReadProfileRecordDto: The created record.

        Raises:
            ProfileConflictError: If the record already exists (unique violation).
            ProfileRepositoryError: For any other database error.
        """
        query = """
            INSERT INTO profiles (account_id, key, value, source)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
        """
        values = (dto.account_id, dto.key, dto.value, dto.source)

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    return ReadProfileRecordDto(**row)
        except psycopg.errors.UniqueViolation as e:
            raise ProfileConflictError(
                f"Profile record already exists for key={dto.key}, source={dto.source}"
            ) from e
        except psycopg.errors.ForeignKeyViolation as e:
            raise ProfileRepositoryError(
                "Invalid account_id (foreign key violation)"
            ) from e
        except psycopg.errors.Error as e:
            raise ProfileRepositoryError("Unknown database error") from e

    async def get_record_by_id(self, record_id: UUID) -> ReadProfileRecordDto:
        """
        Retrieve a single profile record by its ID.

        Args:
            record_id (UUID): The record's unique ID.

        Returns:
            ReadProfileRecordDto: The record.

        Raises:
            ProfileNotFoundError: If not found.
            ProfileRepositoryError: On DB errors.
        """
        query = "SELECT * FROM profiles WHERE id = %s;"
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (record_id,))
                    row = await cur.fetchone()
                    if row is None:
                        raise ProfileNotFoundError("Profile record not found")
                    return ReadProfileRecordDto(**row)
        except psycopg.errors.Error as e:
            raise ProfileRepositoryError("Unknown database error") from e

    async def update_record(
        self, record_id: UUID, dto: UpdateProfileRecordDto
    ) -> ReadProfileRecordDto:
        """
        Update an existing profile record's value or source.

        Args:
            record_id (UUID): The record ID.
            dto (UpdateProfileRecordDto): Fields to update.

        Returns:
            ReadProfileRecordDto: Updated record.

        Raises:
            ProfileNotFoundError: If the record does not exist.
            ProfileRepositoryError: On DB errors.
        """
        fields = []
        values = []

        if dto.value is not None:
            fields.append("value = %s")
            values.append(dto.value)
        if dto.source is not None:
            fields.append("source = %s")
            values.append(dto.source)

        if not fields:
            raise ValueError("No fields to update in UpdateProfileRecordDto")

        fields.append("updated_at = NOW()")
        values.append(record_id)

        query = f"""
            UPDATE profiles
            SET {", ".join(fields)}
            WHERE id = %s
            RETURNING *;
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row is None:
                        raise ProfileNotFoundError("Profile record not found")
                    return ReadProfileRecordDto(**row)
        except psycopg.errors.Error as e:
            raise ProfileRepositoryError("Unknown database error") from e

    async def delete_record(self, record_id: UUID) -> None:
        """
        Delete a profile record by its ID.

        Args:
            record_id (UUID): The record's ID.

        Raises:
            ProfileNotFoundError: If the record does not exist.
            ProfileRepositoryError: On DB errors.
        """
        query = "DELETE FROM profiles WHERE id = %s;"
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, (record_id,))
                    if cur.rowcount == 0:
                        raise ProfileNotFoundError("Profile record not found")
        except psycopg.errors.Error as e:
            raise ProfileRepositoryError("Unknown database error") from e

    async def get_records(
        self, dto: FilterProfileRecordsDto
    ) -> List[ReadProfileRecordDto]:
        """
        Retrieve a list of profile records filtered by account/source and paginated.

        Args:
            dto (FilterProfileRecordsDto): Filter + pagination parameters.

        Returns:
            List[ReadProfileRecordDto]: Matching records.
        """
        clauses = []
        params = []

        if dto.account_id:
            clauses.append("account_id = %s")
            params.append(dto.account_id)
        if dto.source:
            clauses.append("source = %s")
            params.append(dto.source)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([dto.limit, dto.offset])

        query = f"""
            SELECT *
            FROM profiles
            {where_clause}
            ORDER BY created_at ASC
            LIMIT %s OFFSET %s;
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, params)
                    rows = await cur.fetchall()
                    return [ReadProfileRecordDto(**r) for r in rows]
        except psycopg.errors.Error as e:
            raise ProfileRepositoryError("Unknown database error") from e

    async def upsert_records(
        self, dto: UpsertProfileRecordsDto
    ) -> List[ReadProfileRecordDto]:
        """
        Upsert multiple profile records at once (insert or update if exists).

        Args:
            dto (UpsertProfileRecordsDto): Account ID + records list.

        Returns:
            List[ReadProfileRecordDto]: Newly inserted or updated rows.

        Raises:
            ProfileRepositoryError: On DB errors.
        """
        if not dto.records:
            return []

        values = [(dto.account_id, r.key, r.value, r.source) for r in dto.records]

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.executemany(
                        "INSERT INTO profiles (account_id, key, value, source) "
                        "VALUES (%s, %s, %s, %s) "
                        "ON CONFLICT (account_id, key, source) "
                        "DO UPDATE SET value = EXCLUDED.value, updated_at = NOW() "
                        "RETURNING *;",
                        values,
                    )
                    rows = []
                    async for row in cur:
                        rows.append(ReadProfileRecordDto(**row))
                    return rows
        except psycopg.errors.Error as e:
            raise ProfileRepositoryError("Unknown database error") from e
