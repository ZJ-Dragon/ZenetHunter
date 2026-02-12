from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.exceptions import AppError, ErrorCode
from app.models.auth import Token
from app.services.setup import SetupService

router = APIRouter(tags=["auth"])
setup_service = SetupService()


@router.post("/auth/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    Login to get access token.
    Validates against stored admin credentials.
    """
    token = await setup_service.authenticate(form_data.username, form_data.password)
    if token:
        return {"access_token": token, "token_type": "bearer"}

    raise AppError(
        ErrorCode.AUTH_INVALID_TOKEN,
        "Incorrect username or password",
        http_status=status.HTTP_401_UNAUTHORIZED,
        extra={"headers": {"WWW-Authenticate": "Bearer"}},
    )
