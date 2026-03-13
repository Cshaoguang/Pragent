from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_db_session
from backend.api.responses import page, success
from backend.services.traces import TraceService

router = APIRouter()


@router.get("/rag/traces/runs")
async def page_runs(
    current: int = Query(default=1),
    size: int = Query(default=10),
    traceId: str | None = Query(default=None),
    conversationId: str | None = Query(default=None),
    taskId: str | None = Query(default=None),
    status: str | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    records, total = await TraceService(session).page_runs(current, size, traceId, conversationId, taskId, status)
    data = [TraceService(session)._run_to_dict(item) for item in records]
    return success(page(data, total, current, size).model_dump())


@router.get("/rag/traces/runs/{trace_id}")
async def get_detail(
    trace_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await TraceService(session).get_detail(trace_id))


@router.get("/rag/traces/runs/{trace_id}/nodes")
async def get_nodes(
    trace_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await TraceService(session).list_nodes(trace_id))