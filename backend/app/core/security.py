from typing import Annotated

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AppError, ErrorCode
from app.models.auth import User, UserRole
from app.services.auth import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    Validate token and return current user.
    Guests (no token) are allowed but identified as GUEST role.
    """
    if not token:
        return User(username="guest", role=UserRole.GUEST)

    token_data = verify_token(token)
    if token_data is None:
        # Invalid token provided -> 401
        raise AppError(
            ErrorCode.AUTH_INVALID_TOKEN,
            "Could not validate credentials",
            http_status=status.HTTP_401_UNAUTHORIZED,
            extra={"headers": {"WWW-Authenticate": "Bearer"}},
        )

    return User(username=token_data.username, role=token_data.role or UserRole.GUEST)


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency to require Admin role."""
    if current_user.role != UserRole.ADMIN:
        raise AppError(ErrorCode.AUTH_FORBIDDEN, "Admin privileges required")
    return current_user
