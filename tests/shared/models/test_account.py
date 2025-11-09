from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from shared.models.account import (
    CreateAccountDto,
    ReadAccountDto,
    RegisterAccountDto,
    UpdateAccountDto,
)


def test_register_account_dto_valid():
    """
    Test that RegisterAccountDto accepts valid data.
    """
    dto = RegisterAccountDto(
        email="user@example.com",
        password="strongpass",
        confirm_password="strongpass",
    )
    assert dto.email == "user@example.com"
    assert dto.password == "strongpass"
    assert dto.confirm_password == "strongpass"


def test_register_account_dto_invalid_email():
    """
    Test that RegisterAccountDto raises ValidationError for invalid email.
    """
    with pytest.raises(ValidationError):
        RegisterAccountDto(
            email="invalid_email",
            password="secret123",
            confirm_password="secret123",
        )


@pytest.mark.parametrize("field", ["password", "confirm_password"])
def test_register_account_dto_password_too_short(field):
    """
    Test that RegisterAccountDto enforces minimum password length.
    """
    data = {
        "email": "test@example.com",
        "password": "123",
        "confirm_password": "123",
    }
    with pytest.raises(ValidationError):
        RegisterAccountDto(**data)


def test_create_account_dto_valid():
    """
    Test that CreateAccountDto accepts valid input.
    """
    dto = CreateAccountDto(email="new@example.com", password_hash="hashed123")
    assert dto.email == "new@example.com"
    assert dto.password_hash == "hashed123"


def test_create_account_dto_invalid_email():
    """
    Test that CreateAccountDto validates email format.
    """
    with pytest.raises(ValidationError):
        CreateAccountDto(email="bademail", password_hash="hashed")


def test_read_account_dto_valid():
    """
    Test that ReadAccountDto accepts all required fields and types.
    """
    now = datetime.now(timezone.utc)
    dto = ReadAccountDto(
        id="uuid-123",
        email="reader@example.com",
        status="active",
        confirmed_at=now,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )

    assert dto.id == "uuid-123"
    assert dto.status == "active"
    assert isinstance(dto.created_at, datetime)
    assert dto.deleted_at is None


@pytest.mark.parametrize("status", ["created", "active", "blocked"])
def test_read_account_dto_status_enum(status):
    """
    Test that ReadAccountDto accepts only valid status values.
    """
    now = datetime.now(timezone.utc)
    dto = ReadAccountDto(
        id="uuid-1",
        email="ok@example.com",
        status=status,
        confirmed_at=None,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )
    assert dto.status == status


def test_read_account_dto_invalid_status():
    """
    Test that ReadAccountDto rejects invalid status.
    """
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        ReadAccountDto(
            id="uuid-2",
            email="ok@example.com",
            status="unknown",  # invalid literal
            confirmed_at=None,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )


def test_update_account_dto_all_fields():
    """
    Test that UpdateAccountDto correctly stores optional fields.
    """
    dto = UpdateAccountDto(
        email="updated@example.com",
        status="blocked",
        password_hash="hashed_pw",
    )
    assert dto.email == "updated@example.com"
    assert dto.status == "blocked"
    assert dto.password_hash == "hashed_pw"


def test_update_account_dto_defaults():
    """
    Test that UpdateAccountDto allows omitted optional fields.
    """
    dto = UpdateAccountDto()
    assert dto.email is None
    assert dto.status is None
    assert dto.password_hash is None
