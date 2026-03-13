from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    session: AsyncSession,
    stmt: Select,
    current: int,
    size: int,
) -> tuple[Sequence, int]:
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = int((await session.scalar(count_stmt)) or 0)
    result = await session.execute(stmt.offset((current - 1) * size).limit(size))
    return result.scalars().all(), total
