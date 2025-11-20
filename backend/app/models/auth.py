from enum import Enum

from pydantic import BaseModel, ConfigDict


class UserRole(str, Enum):
    ADMIN = "admin"
    GUEST = "guest"


class User(BaseModel):
    """User model."""
    username: str
    role: UserRole = UserRole.GUEST
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data embedded in the token."""
    username: str | None = None
    role: UserRole | None = None

