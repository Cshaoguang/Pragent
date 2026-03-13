from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_current_user, get_db_session
from backend.api.responses import page, success
from backend.models.schemas import ChangePasswordRequest, UserCreateRequest, UserUpdateRequest
from backend.services.users import UserService

router = APIRouter()


@router.get("/users")
async def list_users(
    current: int = Query(default=1),
    size: int = Query(default=10),
    keyword: str | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    records, total = await UserService(session).list_page(current, size, keyword)
    data = [
        {
            "id": str(item.id),
            "username": item.username,
            "role": item.role,
            "avatar": item.avatar,
            "createTime": item.create_time,
            "updateTime": item.update_time,
        }
        for item in records
    ]
    return success(page(data, total, current, size).model_dump())


@router.post("/users")
async def create_user(
    payload: UserCreateRequest,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    user_id = await UserService(session).create(payload)
    return success(user_id)


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await UserService(session).update(user_id, payload)
    return success()


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await UserService(session).delete(user_id)
    return success()


@router.get("/user/me")
async def get_current_user_profile(user=Depends(get_current_user)):
    payload = user.model_dump(by_alias=True)
    payload.pop("token", None)
    return success(payload)


@router.put("/user/password")
async def change_password(
    payload: ChangePasswordRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await UserService(session).change_password(user, payload)
    return success()