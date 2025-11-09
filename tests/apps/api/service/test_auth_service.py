import pytest
from jose import JWTError

from apps.api.service.auth_service import (
    AuthService,
    InvalidCredentialsError,
    TokenError,
)


@pytest.mark.asyncio
async def test_login_success(
    monkeypatch, mock_account_repository, mock_config, mock_account_dto
):
    """
    Test that `login()` authenticates user and issues valid tokens.

    Steps:
      1. Mock password verification to return True.
      2. Mock token creation to return predictable strings.
      3. Call `login()` with valid credentials.
      4. Verify returned structure and repository calls.
    """
    mock_account_dto.password_hash = "hashed_pw"
    mock_account_repository.get_account_by_email.return_value = mock_account_dto

    monkeypatch.setattr(
        "apps.api.service.auth_service.verify_password", lambda p, h: True
    )
    monkeypatch.setattr(
        "apps.api.service.auth_service.jwt.encode",
        lambda d, s, algorithm: f"TOKEN_{d['type']}",
    )

    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    result = await service.login(email=mock_account_dto.email, password="123456")

    mock_account_repository.get_account_by_email.assert_called_once_with(
        mock_account_dto.email
    )
    assert result["access_token"] == "TOKEN_access"
    assert result["refresh_token"] == "TOKEN_refresh"
    assert result["token_type"] == "bearer"
    assert result["expires_in"] == mock_config.access_token_expires


@pytest.mark.asyncio
async def test_login_invalid_password(
    monkeypatch, mock_account_repository, mock_config, mock_account_dto
):
    """
    Test that `login()` raises InvalidCredentialsError when password is incorrect.
    """
    mock_account_repository.get_account_by_email.return_value = mock_account_dto
    mock_account_dto.password_hash = "some_hash"
    monkeypatch.setattr(
        "apps.api.service.auth_service.verify_password", lambda p, h: False
    )

    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    with pytest.raises(InvalidCredentialsError):
        await service.login(email=mock_account_dto.email, password="wrong_pw")


@pytest.mark.asyncio
async def test_login_missing_account(monkeypatch, mock_account_repository, mock_config):
    """
    Test that `login()` raises InvalidCredentialsError when account is missing.
    """
    mock_account_repository.get_account_by_email.return_value = None
    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    with pytest.raises(InvalidCredentialsError):
        await service.login(email="ghost@example.com", password="123456")


@pytest.mark.asyncio
async def test_login_repository_error(mock_account_repository, mock_config):
    """
    Test that `login()` raises InvalidCredentialsError when repository fails.
    """
    mock_account_repository.get_account_by_email.side_effect = Exception("DB down")
    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    with pytest.raises(InvalidCredentialsError):
        await service.login(email="user@example.com", password="123456")


@pytest.mark.asyncio
async def test_login_missing_password_hash(
    mock_account_repository, mock_config, mock_account_dto
):
    """
    Test that `login()` raises InvalidCredentialsError when password hash is missing.
    """
    mock_account_repository.get_account_by_email.return_value = mock_account_dto
    mock_account_dto.password_hash = None
    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    with pytest.raises(InvalidCredentialsError):
        await service.login(email=mock_account_dto.email, password="123456")


def test_create_token_success(monkeypatch, mock_config, mock_account_repository):
    """
    Test that `_create_token()` generates a JWT with proper claims.
    """
    dummy_payload = {"sub": "123", "type": "access"}
    monkeypatch.setattr(
        "apps.api.service.auth_service.jwt.encode",
        lambda d, s, algorithm: f"encoded:{d['sub']}",
    )

    service = AuthService(config=mock_config, account_repo=mock_account_repository)
    token = service._create_token(
        data=dummy_payload,
        expires_delta=mock_config.access_token_expires,
        secret="secret",
    )

    assert token.startswith("encoded:")
    assert "123" in token


def test_decode_token_success(monkeypatch, mock_config, mock_account_repository):
    """
    Test that `_decode_token()` successfully decodes a valid JWT.
    """
    expected_payload = {"sub": "user123", "type": "access"}
    monkeypatch.setattr(
        "apps.api.service.auth_service.jwt.decode",
        lambda t, s, algorithms: expected_payload,
    )

    service = AuthService(config=mock_config, account_repo=mock_account_repository)
    decoded = service._decode_token("fake_token", "secret")

    assert decoded == expected_payload


def test_decode_token_invalid(monkeypatch, mock_config, mock_account_repository):
    """
    Test that `_decode_token()` raises TokenError on invalid JWT.
    """

    def raise_jwt_error(*args, **kwargs):
        raise JWTError("Invalid signature")

    monkeypatch.setattr("apps.api.service.auth_service.jwt.decode", raise_jwt_error)
    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    with pytest.raises(TokenError):
        service._decode_token("bad_token", "secret")


def test_refresh_tokens_success(monkeypatch, mock_config, mock_account_repository):
    """
    Test that `refresh_tokens()` validates a refresh token and issues new tokens.

    Steps:
      1. Patch `_decode_token` to return a valid refresh payload.
      2. Patch `_create_token` to return dummy tokens.
      3. Call `refresh_tokens()` and verify structure.
    """
    decoded_payload = {
        "sub": "uuid",
        "email": "user@example.com",
        "status": "active",
        "type": "refresh",
    }

    monkeypatch.setattr(
        "apps.api.service.auth_service.AuthService._decode_token",
        lambda self, token, secret: decoded_payload,
    )
    monkeypatch.setattr(
        "apps.api.service.auth_service.AuthService._create_token",
        lambda self, data, expires_delta, secret: f"TOKEN_{data['type']}",
    )

    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    result = service.refresh_tokens("dummy_refresh_token")

    assert result["access_token"] == "TOKEN_access"
    assert result["refresh_token"] == "TOKEN_refresh"
    assert result["token_type"] == "bearer"
    assert result["expires_in"] == mock_config.access_token_expires


def test_refresh_tokens_invalid_type(monkeypatch, mock_config, mock_account_repository):
    """
    Test that `refresh_tokens()` raises TokenError when decoded token type is invalid.
    """
    decoded_payload = {"sub": "uuid", "email": "user@example.com", "type": "access"}
    monkeypatch.setattr(
        "apps.api.service.auth_service.AuthService._decode_token",
        lambda self, token, secret: decoded_payload,
    )

    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    with pytest.raises(TokenError):
        service.refresh_tokens("bad_refresh_token")


def test_refresh_tokens_invalid_jwt(monkeypatch, mock_config, mock_account_repository):
    """
    Test that `refresh_tokens()` raises TokenError when JWT decoding fails.
    """

    def raise_token_error(*args, **kwargs):
        raise TokenError("Invalid or expired token")

    monkeypatch.setattr(
        "apps.api.service.auth_service.AuthService._decode_token",
        raise_token_error,
    )

    service = AuthService(config=mock_config, account_repo=mock_account_repository)

    with pytest.raises(TokenError):
        service.refresh_tokens("expired_token")
