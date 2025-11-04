from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.repository.account_repository import AccountRepository
from shared.config.config import Config


@pytest.fixture
def mock_pool():
    """
    Mock AsyncConnectionPool chain for async repository testing.

    Structure emulated:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(...)
                await cur.fetchone()
    """
    mock_cursor = MagicMock()
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchone = AsyncMock()
    mock_cursor.fetchall = AsyncMock()
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=None)

    mock_conn = MagicMock()
    mock_conn.cursor = MagicMock(return_value=mock_cursor)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=None)

    mock_pool = MagicMock()
    mock_pool.connection = MagicMock(return_value=mock_conn)

    return mock_pool


@pytest.fixture
def mock_cursor(mock_pool):
    return mock_pool.connection.return_value.cursor.return_value


@pytest.fixture
def mock_config():
    """
    Provide a mock configuration object for testing.

    This fixture supplies a `Config` instance with dummy but valid settings
    for database connection and JWT token generation, allowing services
    and repositories to operate without external dependencies.

    Returns:
        Config: A mock configuration object with test-safe parameters.
    """
    return Config(
        database_host="test",
        database_port=5432,
        database_name="test",
        database_user="test",
        database_password="test",
        access_token_secret="access_secret",
        refresh_token_secret="refresh_secret",
        access_token_expires=60,
        refresh_token_expires=3600,
        hash_algorithm="HS256",
        database_min_pool_size=4,
        database_max_pool_size=10,
    )


@pytest.fixture
def account_repository(mock_pool):
    """
    Provide a AccountRepository instance with a mocked ConnectionPool.

    This fixture allows testing repository methods in isolation
    by injecting a mocked connection pool instead of a real database.

    Args:
        mock_pool (MagicMock): The mocked database connection pool.

    Returns:
        AccountRepository: Repository instance configured with the mock pool.
    """
    return AccountRepository(pool=mock_pool)


@pytest.fixture
def mock_account_repository():
    """
    Provide a fully mocked AccountRepository for service-layer testing.

    This fixture defines a mock repository with its core methods
    pre-initialized as MagicMock objects.

    Returns:
        MagicMock: Mocked account repository.
    """
    mock_repo = MagicMock()
    mock_repo.get_account_by_username = MagicMock()
    mock_repo.get_account_by_email = MagicMock()
    mock_repo.create_account = MagicMock()
    mock_repo.update_account = MagicMock()
    mock_repo.delete_account = MagicMock()
    return mock_repo


@pytest.fixture
def mock_account():
    now = datetime.now()
    return {
        "id": "000000-0000-0000-0000-000000000000",
        "email": "account@example.com",
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "confirmed_at": now,
        "deleted_at": None,
    }


@pytest.fixture
def mock_accounts():
    now = datetime.now()
    return [
        {
            "id": "000000-0000-0000-0000-000000000001",
            "email": "first-account@example.com",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "confirmed_at": now,
            "deleted_at": None,
        },
        {
            "id": "000000-0000-0000-0000-000000000002",
            "email": "second-account@example.com",
            "status": "blocked",
            "created_at": now,
            "updated_at": now,
            "confirmed_at": None,
            "deleted_at": None,
        },
    ]
