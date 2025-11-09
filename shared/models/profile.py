from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field
from pydantic.dataclasses import dataclass

ProfileSource = Literal["user", "system", "admin", "import", "sync"]
ProfileKey = Literal["first_name", "last_name", "date_of_birth"]


@dataclass
class ProfileKVInput:
    """
    Single profile key-value pair to be created/updated.

    Constraints are intentionally soft here: the DB enforces uniqueness
    (account_id, key, source), while the repo may normalize keys (e.g., lower, snake_case).
    """

    key: ProfileKey = Field()
    value: Optional[str] = Field(default=None, max_length=10_000)
    source: Optional[ProfileSource] = Field(default=None)


# ------------------------------------------------------------
# CRUD DTO для записи профиля (одной KV-строки)
# ------------------------------------------------------------
@dataclass
class CreateProfileRecordDto:
    """
    Create a new profile record (key-value) for a given account.
    """

    account_id: str
    key: ProfileKey = Field()
    value: Optional[str] = Field(default=None, max_length=10_000)
    source: ProfileSource = Field(default="user")


@dataclass
class ReadProfileRecordDto:
    """
    Read a single persisted profile record (row from `profiles`).
    """

    id: str
    account_id: str
    key: ProfileKey
    value: Optional[str]
    source: Optional[ProfileSource]
    created_at: datetime
    updated_at: datetime


@dataclass
class UpdateProfileRecordDto:
    """
    Update fields of an existing profile record.
    Only value/source are mutable; key is immutable by design.
    """

    value: Optional[str] = Field(default=None, max_length=10_000)
    source: Optional[ProfileSource] = Field(default=None)


@dataclass
class UpsertProfileRecordsDto:
    """
    Upsert multiple key-value records for an account.
    If a (account_id, key, source) exists -> update, else -> insert.
    """

    account_id: str
    records: List[ProfileKVInput] = Field(default_factory=list)


@dataclass
class PatchProfileDto:
    """
    Partial update for multiple keys at once (no deletions).
    Semantics: update existing keys, upsert missing ones.
    """

    account_id: str
    changes: List[ProfileKVInput] = Field(default_factory=list)


@dataclass
class FilterProfileRecordsDto:
    """
    Query parameters for listing raw profile records (rows) with pagination
    and simple filtering.
    """

    account_id: Optional[str] = None
    source: Optional[ProfileSource] = None
    limit: int = Field(default=10, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
