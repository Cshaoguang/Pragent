from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import User
from backend.models.schemas import AuthenticatedUser, ChangePasswordRequest, UserCreateRequest, UserUpdateRequest
from backend.services.common import paginate
from backend.services.ids import new_long_id


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_page(self, current: int, size: int, keyword: str | None):
        stmt = select(User).where(User.deleted == 0)
        if keyword:
            stmt = stmt.where(or_(User.username.like(f"%{keyword}%"), User.role.like(f"%{keyword}%")))
        stmt = stmt.order_by(User.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def create(self, payload: UserCreateRequest) -> str:
        user = User(
            id=new_long_id(),
            username=payload.username,
            password=payload.password,
            role=payload.role,
            avatar=payload.avatar,
        )
        self.session.add(user)
        await self.session.commit()
        return str(user.id)

    async def update(self, user_id: str, payload: UserUpdateRequest) -> None:
        user = await self.session.get(User, int(user_id))
        if user is None or user.deleted != 0:
            raise ValueError("用户不存在")
        if payload.username is not None:
            user.username = payload.username
        if payload.password is not None:
            user.password = payload.password
        if payload.role is not None:
            user.role = payload.role
        if payload.avatar is not None:
            user.avatar = payload.avatar
        await self.session.commit()

    async def delete(self, user_id: str) -> None:
        user = await self.session.get(User, int(user_id))
        if user is None:
            return
        user.deleted = 1
        await self.session.commit()

    async def change_password(self, current_user: AuthenticatedUser, payload: ChangePasswordRequest) -> None:
        user = await self.session.get(User, int(current_user.user_id))
        if user is None or user.deleted != 0:
            raise ValueError("用户不存在")
        if user.password != payload.current_password:
            raise ValueError("原密码错误")
        user.password = payload.new_password
        await self.session.commit()
