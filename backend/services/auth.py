import hashlib
import hmac
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.redis import get_redis
from backend.models.entities import User
from backend.models.schemas import AuthenticatedUser, LoginResponse


class AuthService:
    token_ttl_seconds = 60 * 60 * 24 * 30

    def __init__(self, session: AsyncSession):
        self.session = session

    async def login(self, username: str, password: str) -> LoginResponse:
        stmt = select(User).where(User.username == username, User.deleted == 0)
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if user is None or not self._verify_password(password, user.password):
            raise ValueError("用户名或密码错误")
        token = str(uuid.uuid4())
        redis = get_redis()
        await redis.setex(f"auth:token:{token}", self.token_ttl_seconds, str(user.id))
        return LoginResponse(
            user_id=str(user.id),
            username=user.username,
            role=user.role,
            avatar=user.avatar,
            token=token,
        )

    async def logout(self, token: str) -> None:
        await get_redis().delete(f"auth:token:{token}")

    async def get_current_user(self, token: str) -> AuthenticatedUser | None:
        user_id = await get_redis().get(f"auth:token:{token}")
        if not user_id:
            return None
        user = await self.session.get(User, int(user_id))
        if user is None or user.deleted != 0:
            return None
        return AuthenticatedUser(
            user_id=str(user.id),
            username=user.username,
            role=user.role,
            avatar=user.avatar,
            token=token,
        )

    @staticmethod
    def _verify_password(raw_password: str, stored_password: str) -> bool:
        plain_match = hmac.compare_digest(raw_password, stored_password)
        sha256_match = hmac.compare_digest(hashlib.sha256(raw_password.encode()).hexdigest(), stored_password)
        return plain_match or sha256_match
