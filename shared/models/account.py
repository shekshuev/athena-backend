from datetime import datetime
from typing import Literal, Optional

from pydantic import EmailStr, Field
from pydantic.dataclasses import dataclass


@dataclass
class CreateAccountDto:
    email: EmailStr


@dataclass
class ReadAccountDto:
    id: str
    email: EmailStr
    status: Literal["created", "active", "blocked"]
    confirmed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


@dataclass
class UpdateAccountDto:
    email: Optional[EmailStr] = Field(default=None)
    status: Optional[Literal["active", "blocked"]] = Field(default=None)
