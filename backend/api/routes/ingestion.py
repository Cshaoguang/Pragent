from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_db_session
from backend.api.responses import page, success
from backend.models.schemas import IngestionPipelinePayload, IngestionTaskCreateRequest
from backend.services.ingestion import IngestionService

router = APIRouter()


@router.get("/ingestion/pipelines")
async def page_pipelines(
    pageNo: int = Query(default=1),
    pageSize: int = Query(default=10),
    keyword: str | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IngestionService(session)
    records, total = await service.page_pipelines(pageNo, pageSize, keyword)
    data = [service.pipeline_to_dict(item, []) for item in records]
    return success(page(data, total, pageNo, pageSize).model_dump())


@router.get("/ingestion/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await IngestionService(session).get_pipeline(pipeline_id))


@router.post("/ingestion/pipelines")
async def create_pipeline(
    payload: IngestionPipelinePayload,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await IngestionService(session).create_pipeline(payload, user))


@router.put("/ingestion/pipelines/{pipeline_id}")
async def update_pipeline(
    pipeline_id: str,
    payload: IngestionPipelinePayload,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await IngestionService(session).update_pipeline(pipeline_id, payload, user))


@router.delete("/ingestion/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await IngestionService(session).delete_pipeline(pipeline_id)
    return success()


@router.get("/ingestion/tasks")
async def page_tasks(
    pageNo: int = Query(default=1),
    pageSize: int = Query(default=10),
    status: str | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IngestionService(session)
    records, total = await service.page_tasks(pageNo, pageSize, status)
    data = [service.task_to_dict(item) for item in records]
    return success(page(data, total, pageNo, pageSize).model_dump())


@router.get("/ingestion/tasks/{task_id}")
async def get_task(
    task_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await IngestionService(session).get_task(task_id))


@router.get("/ingestion/tasks/{task_id}/nodes")
async def get_task_nodes(
    task_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await IngestionService(session).list_task_nodes(task_id))


@router.post("/ingestion/tasks")
async def create_task(
    payload: IngestionTaskCreateRequest,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await IngestionService(session).create_task(payload, user))


@router.post("/ingestion/tasks/upload")
async def upload_task(
    pipelineId: str,
    file: UploadFile = File(...),
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await IngestionService(session).upload_task(pipelineId, file, user))