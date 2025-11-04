import os
from dataclasses import dataclass


@dataclass
class Config:
    """App config"""

    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: str = os.getenv("DATABASE_PORT", "5432")
    database_name: str = os.getenv("DATABASE_NAME", "athena")
    database_user: str = os.getenv("DATABASE_USER", "athena")
    database_password: str = os.getenv("DATABASE_PASSWORD", "athena")
    database_min_pool_size: int = int(os.getenv("DATABASE_MIN_POOL_SIZE", 4))
    database_max_pool_size: int = int(os.getenv("DATABASE_MAX_POOL_SIZE", 10))
    access_token_expires: int = int(os.getenv("ACCESS_TOKEN_EXPIRES", 3600))
    refresh_token_expires: int = int(os.getenv("REFRESH_TOKEN_EXPIRES", 86400))
    access_token_secret: str = os.getenv(
        "ACCESS_TOKEN_SECRET", "super_secret_access_token_key"
    )
    refresh_token_secret: str = os.getenv(
        "REFRESH_TOKEN_SECRET", "super_secret_refresh_token_key"
    )
    hash_algorithm: str = os.getenv("HASH_ALGORITHM", "HS256")
