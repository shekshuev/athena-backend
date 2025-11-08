import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from apps.api.repository.account_repository import AccountRepository
from shared.config.config import Config
from shared.models.account import ReadAccountDto
from shared.security.password import verify_password

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    """Raised when invalid email or password is provided."""


class TokenError(Exception):
    """Raised when token is invalid or expired."""


class AuthService:
    """
    Authentication service for Athena LMS.

    Responsibilities:
      - Verify user credentials (email/password).
      - Issue and refresh JWT access/refresh tokens.
      - Decode and validate token payloads.
    """

    def __init__(self, config: Config, account_repo: AccountRepository):
        self.config = config
        self.account_repo = account_repo
        logger.debug(
            "AuthService initialized with token expirations: access=%s, refresh=%s",
            config.access_token_expires,
            config.refresh_token_expires,
        )

    def _create_token(
        self, data: dict[str, Any], expires_delta: int, secret: str
    ) -> str:
        """
        Generate a JWT token with expiration time.

        Logs:
          - Token creation intent.
          - Payload claims before encoding.
        """
        logger.debug(
            "Creating token for subject=%s with expiry=%s seconds",
            data.get("sub"),
            expires_delta,
        )
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, secret, algorithm=self.config.hash_algorithm
        )
        logger.debug(
            "Token successfully generated for subject=%s exp=%s",
            data.get("sub"),
            expire,
        )
        return encoded_jwt

    def _decode_token(self, token: str, secret: str) -> dict[str, Any]:
        """
        Decode and verify a JWT token.

        Logs:
          - Decoding attempt.
          - Failure reason if token is invalid or expired.
        """
        logger.debug("Attempting to decode token...")
        try:
            payload = jwt.decode(token, secret, algorithms=[self.config.hash_algorithm])
            logger.debug(
                "Token decoded successfully for subject=%s", payload.get("sub")
            )
            return payload
        except JWTError as e:
            logger.warning("Token decoding failed: %s", str(e))
            raise TokenError("Invalid or expired token") from e

    async def login(self, email: str, password: str) -> dict[str, str]:
        """
        Authenticate user by email/password and return access and refresh JWT tokens.

        Logs:
          - Authentication attempt with email.
          - Failure reasons (account not found, no password hash, invalid password).
          - Successful authentication and token issuance.
        """
        logger.info("Login attempt for email=%s", email)
        try:
            account = await self.account_repo.get_account_by_email(email)
            logger.debug("Account lookup successful for email=%s", email)
        except Exception as e:
            logger.warning(
                "Login failed: account lookup error for email=%s (%s)", email, e
            )
            raise InvalidCredentialsError("Invalid credentials") from e

        if not account or not getattr(account, "password_hash", None):
            logger.warning(
                "Login failed: no account or missing password hash for email=%s", email
            )
            raise InvalidCredentialsError("Invalid credentials")

        if not verify_password(password, account.password_hash):
            logger.warning("Login failed: incorrect password for email=%s", email)
            raise InvalidCredentialsError("Invalid credentials")

        logger.info(
            "Authentication succeeded for account_id=%s email=%s",
            account.id,
            account.email,
        )

        payload = {
            "sub": account.id,
            "email": account.email,
            "status": account.status,
            "type": "access",
        }

        access_token = self._create_token(
            data=payload,
            expires_delta=self.config.access_token_expires,
            secret=self.config.access_token_secret,
        )

        refresh_payload = payload.copy()
        refresh_payload["type"] = "refresh"

        refresh_token = self._create_token(
            data=refresh_payload,
            expires_delta=self.config.refresh_token_expires,
            secret=self.config.refresh_token_secret,
        )

        logger.info(
            "Issued new tokens for account_id=%s (access=%ss refresh=%ss)",
            account.id,
            self.config.access_token_expires,
            self.config.refresh_token_expires,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.config.access_token_expires,
        }

    def refresh_tokens(self, refresh_token: str) -> dict[str, str]:
        """
        Validate refresh token and issue new tokens.

        Logs:
          - Refresh attempt.
          - Validation errors (type mismatch, decode failure).
          - Successful re-issuance.
        """
        logger.info("Attempting token refresh...")
        decoded = self._decode_token(refresh_token, self.config.refresh_token_secret)

        if decoded.get("type") != "refresh":
            logger.warning(
                "Invalid token type for refresh (expected 'refresh', got '%s')",
                decoded.get("type"),
            )
            raise TokenError("Invalid token type")

        logger.debug("Refresh token valid for subject=%s", decoded.get("sub"))

        account = ReadAccountDto(
            id=decoded["sub"],
            email=decoded["email"],
            status=decoded.get("status", "active"),
            confirmed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )

        payload = {
            "sub": account.id,
            "email": account.email,
            "status": account.status,
            "type": "access",
        }

        access_token = self._create_token(
            data=payload,
            expires_delta=self.config.access_token_expires,
            secret=self.config.access_token_secret,
        )

        refresh_payload = payload.copy()
        refresh_payload["type"] = "refresh"

        refresh_token = self._create_token(
            data=refresh_payload,
            expires_delta=self.config.refresh_token_expires,
            secret=self.config.refresh_token_secret,
        )

        logger.info("Refreshed tokens for account_id=%s", account.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.config.access_token_expires,
        }
