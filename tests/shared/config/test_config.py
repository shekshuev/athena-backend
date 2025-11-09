from shared.config.config import Config


def test_config_defaults(monkeypatch):
    """
    Test that Config loads default values when no environment variables are set.
    """
    keys = [
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
        "ACCESS_TOKEN_EXPIRES",
        "REFRESH_TOKEN_EXPIRES",
        "ACCESS_TOKEN_SECRET",
        "REFRESH_TOKEN_SECRET",
        "HASH_ALGORITHM",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)

    config = Config()

    assert config.database_host == "localhost"
    assert config.database_port == "5432"
    assert config.database_name == "athena"
    assert config.database_user == "athena"
    assert config.database_password == "athena"
    assert config.database_min_pool_size == 4
    assert config.database_max_pool_size == 10
    assert config.access_token_expires == 3600
    assert config.refresh_token_expires == 86400
    assert config.access_token_secret == "super_secret_access_token_key"
    assert config.refresh_token_secret == "super_secret_refresh_token_key"
    assert config.hash_algorithm == "HS256"
