from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db_session
from backend.api.responses import success
from backend.models.schemas import LoginRequest
from backend.services.auth import AuthService

router = APIRouter()


@router.post("/auth/login")
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    data = await AuthService(session).login(payload.username, payload.password)
    return success(data.model_dump(by_alias=True))


@router.post("/auth/logout")
async def logout(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    if authorization:
        await AuthService(session).logout(authorization)
    return success()