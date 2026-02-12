from pydantic import BaseModel, Field

from app.models.auth import Token


class SetupStatus(BaseModel):
    """Current OOBE/setup state."""

    admin_exists: bool
    first_run_completed: bool


class RegisterAdminRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class RegisterAdminResponse(Token):
    """Token response after bootstrap registration."""

    pass


class AcknowledgeRequest(BaseModel):
    """Empty body reserved for future fields."""

    acknowledged: bool = True
