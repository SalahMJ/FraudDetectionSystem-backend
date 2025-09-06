from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    settings = get_settings()
    if body.username == settings.ADMIN_USER and body.password == settings.ADMIN_PASSWORD:
        token = create_access_token(body.username)
        return LoginResponse(access_token=token)
    raise HTTPException(status_code=401, detail="Invalid credentials")
