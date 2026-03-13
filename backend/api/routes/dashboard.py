from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_db_session
from backend.api.responses import success
from backend.services.dashboard import DashboardService

router = APIRouter()


@router.get("/admin/dashboard/overview")
async def get_overview(
    window: str = Query(default="24h"),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await DashboardService(session).get_overview(window))


@router.get("/admin/dashboard/performance")
async def get_performance(
    window: str = Query(default="24h"),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await DashboardService(session).get_performance(window))


@router.get("/admin/dashboard/trends")
async def get_trends(
    metric: str = Query(default="messages"),
    window: str = Query(default="7d"),
    granularity: str = Query(default="day"),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await DashboardService(session).get_trends(metric, window, granularity))