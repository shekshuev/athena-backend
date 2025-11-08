from datetime import datetime
from typing import Literal, Optional

from pydantic import EmailStr, Field
from pydantic.dataclasses import dataclass

Status = Literal["created", "active", "blocked"]


@dataclass
class RegisterAccountDto:
    """
    DTO used for user registration.

    This object is received from the frontend and contains the raw password
    along with its confirmation. The service layer (AuthService) is responsible
    for validating that both passwords match and hashing the password before
    persisting the data.
    """

    email: EmailStr
    password: str = Field(
        min_length=6,
        max_length=128,
    )
    confirm_password: str = Field(
        min_length=6,
        max_length=128,
    )


@dataclass
class CreateAccountDto:
    """
    DTO used by the repository to create a new account record.

    Contains only validated data and a pre-hashed password.
    """

    email: EmailStr
    password_hash: str


@dataclass
class ReadAccountDto:
    """
    DTO representing an existing account.

    Returned by repository or service layers. Password hashes are never
    exposed to higher layers.
    """

    id: str
    email: EmailStr
    status: Status
    confirmed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


@dataclass
class UpdateAccountDto:
    """
    DTO used to update an existing account.

    Allows partial updates of selected fields (email, status, password hash).
    """

    email: Optional[EmailStr] = Field(default=None)
    status: Optional[Status] = Field(default=None)
    password_hash: Optional[str] = Field(default=None)
