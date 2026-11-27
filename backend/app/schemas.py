"""Pydantic request and response schemas for auth, profiles, account settings, and admin."""
import re
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, EmailStr, Field, field_validator

from .roles import ALL_ROLES, SIGNUP_ROLES


def _as_utc(d: datetime) -> datetime:
    """Attach UTC timezone to naive datetimes so JSON responses include timezone info."""
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


UTCDatetime = Annotated[datetime, AfterValidator(_as_utc)]


def _check_password(v: str) -> str:
    """Validate password complexity and bcrypt's 72-byte length limit."""
    if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
        raise ValueError("Password must contain at least one letter and one number")
    if len(v.encode("utf-8")) > 72:  # bcrypt only uses the first 72 bytes
        raise ValueError("Password is too long (72 bytes maximum)")
    return v


# ---------- auth ----------
class RegisterRequest(BaseModel):
    """Payload for new user registration."""

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Literal[SIGNUP_ROLES]  # only creator / agency can be chosen at signup

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Trim whitespace and ensure the display name has at least 2 characters."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        """Enforce password strength rules on registration."""
        return _check_password(v)


class UserOut(BaseModel):
    """Public user representation returned by auth and admin endpoints."""

    user_id: int
    name: str
    email: EmailStr
    role: str
    role_label: str
    is_active: bool
    created_at: UTCDatetime


class TokenOut(BaseModel):
    """JWT login response containing the bearer token and user details."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- profiles ----------
class _Profile(BaseModel):
    """Base schema that normalizes blank profile strings to None."""

    @field_validator("*", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        """Convert empty or whitespace-only strings to None."""
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


def _url(v: str | None) -> str | None:
    """Ensure optional URL fields use http:// or https://."""
    if v is not None and not re.match(r"^https?://\S+$", v):
        raise ValueError("Must be a valid http:// or https:// URL")
    return v


class CreatorUpdate(_Profile):
    """Fields a creator can update on their profile."""

    creator_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)
    profile_image: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=100)

    _urls = field_validator("profile_image", "website")(_url)


class CreatorOut(BaseModel):
    """Creator profile response schema."""

    creator_id: int
    user_id: int
    creator_name: str | None
    bio: str | None
    profile_image: str | None
    website: str | None
    location: str | None
    updated_at: UTCDatetime


class AgencyUpdate(_Profile):
    """Fields an agency can update on its profile."""

    agency_name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    logo: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=100)

    _urls = field_validator("logo", "website")(_url)


class AgencyOut(BaseModel):
    """Agency profile response schema."""

    agency_id: int
    user_id: int
    agency_name: str | None
    description: str | None
    logo: str | None
    website: str | None
    location: str | None
    updated_at: UTCDatetime


class AgencyCreatorAdd(BaseModel):
    """Request body to link an existing creator to an agency."""

    creator_id: int


# ---------- account settings ----------
class AccountUpdate(BaseModel):
    """Payload for updating the current user's account name."""

    name: str = Field(min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Trim whitespace and enforce minimum name length."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v


class PasswordChange(BaseModel):
    """Payload for changing the current user's password."""

    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        """Enforce password strength rules on the new password."""
        return _check_password(v)


class DeactivateRequest(BaseModel):
    """Password confirmation payload required to deactivate an account."""

    password: str = Field(min_length=1, max_length=72)


# ---------- admin ----------
class AdminUserUpdate(BaseModel):
    """Admin payload for updating a user's role or active status."""

    role: Literal[ALL_ROLES] | None = None
    is_active: bool | None = None
