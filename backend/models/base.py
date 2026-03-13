from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


class TimestampMixin:
    create_time: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    update_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    deleted: Mapped[int] = mapped_column(default=0)
