from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_db_session
from backend.api.responses import page, success
from backend.models.schemas import SampleQuestionPayload
from backend.services.sample_questions import SampleQuestionService

router = APIRouter()


@router.get("/rag/sample-questions")
async def list_public_questions(session: AsyncSession = Depends(get_db_session)):
    items = await SampleQuestionService(session).list_public()
    data = [
        {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "question": item.question,
            "createTime": item.create_time,
            "updateTime": item.update_time,
        }
        for item in items
    ]
    return success(data)


@router.get("/sample-questions")
async def page_questions(
    current: int = Query(default=1),
    size: int = Query(default=10),
    keyword: str | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    records, total = await SampleQuestionService(session).list_page(current, size, keyword)
    data = [
        {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "question": item.question,
            "createTime": item.create_time,
            "updateTime": item.update_time,
        }
        for item in records
    ]
    return success(page(data, total, current, size).model_dump())


@router.post("/sample-questions")
async def create_question(
    payload: SampleQuestionPayload,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    item_id = await SampleQuestionService(session).create(payload)
    return success(item_id)


@router.put("/sample-questions/{item_id}")
async def update_question(
    item_id: str,
    payload: SampleQuestionPayload,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await SampleQuestionService(session).update(item_id, payload)
    return success()


@router.delete("/sample-questions/{item_id}")
async def delete_question(
    item_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await SampleQuestionService(session).delete(item_id)
    return success()