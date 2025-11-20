from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.exceptions import AppError, ErrorCode
from app.models.auth import Token, UserRole
from app.services.auth import create_access_token

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    Login to get access token.
    Simple hardcoded admin check for MVP.
    User: admin / Pass: zenethunter
    """
    # In a real app, verify against DB hash
    if form_data.username == "admin" and form_data.password == "zenethunter":
        access_token = create_access_token(
            data={"sub": form_data.username, "role": UserRole.ADMIN}
        )
        return {"access_token": access_token, "token_type": "bearer"}

    raise AppError(
        ErrorCode.AUTH_INVALID_TOKEN,
        "Incorrect username or password",
        http_status=status.HTTP_401_UNAUTHORIZED,
        extra={"headers": {"WWW-Authenticate": "Bearer"}},
    )
