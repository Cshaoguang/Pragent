from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_db_session
from backend.api.responses import page, success
from backend.models.entities import KnowledgeBase, KnowledgeDocument
from backend.models.schemas import (
    BatchIdsRequest,
    ChunkCreateRequest,
    ChunkUpdateRequest,
    KnowledgeBaseRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeDocumentUpdateRequest,
)
from backend.services.knowledge import KnowledgeService

router = APIRouter()


@router.get("/knowledge-base")
async def page_bases(
    current: int = Query(default=1),
    size: int = Query(default=10),
    name: str | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = KnowledgeService(session)
    records, total = await service.page_bases(current, size, name)
    counts_stmt = (
        select(KnowledgeDocument.kb_id, func.count())
        .where(KnowledgeDocument.deleted == 0)
        .group_by(KnowledgeDocument.kb_id)
    )
    counts = {row[0]: row[1] for row in (await session.execute(counts_stmt)).all()}
    data = [service.base_to_dict(item, counts.get(item.id, 0)) for item in records]
    return success(page(data, total, current, size).model_dump())


@router.get("/knowledge-base/{kb_id}")
async def get_base(
    kb_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = KnowledgeService(session)
    kb = await service.get_base(kb_id)
    count = await session.scalar(select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.kb_id == kb.id, KnowledgeDocument.deleted == 0)) or 0
    return success(service.base_to_dict(kb, int(count)))


@router.post("/knowledge-base")
async def create_base(
    payload: KnowledgeBaseRequest,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await KnowledgeService(session).create_base(payload, user))


@router.put("/knowledge-base/{kb_id}")
async def update_base(
    kb_id: str,
    payload: KnowledgeBaseUpdateRequest,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).update_base(kb_id, payload, user)
    return success()


@router.delete("/knowledge-base/{kb_id}")
async def delete_base(
    kb_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).delete_base(kb_id)
    return success()


@router.get("/knowledge-base/{kb_id}/docs")
async def page_docs(
    kb_id: str,
    pageNo: int = Query(default=1),
    pageSize: int = Query(default=10),
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = KnowledgeService(session)
    records, total = await service.page_documents(kb_id, pageNo, pageSize, status, keyword)
    data = [service.document_to_dict(item) for item in records]
    return success(page(data, total, pageNo, pageSize).model_dump())


@router.get("/knowledge-base/docs/search")
async def search_docs(
    keyword: str,
    limit: int = Query(default=8),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await KnowledgeService(session).search_documents(keyword, limit))


@router.post("/knowledge-base/{kb_id}/docs/upload")
async def upload_doc(
    kb_id: str,
    sourceType: str = Form(...),
    file: UploadFile | None = File(default=None),
    sourceLocation: str | None = Form(default=None),
    scheduleEnabled: bool = Form(default=False),
    scheduleCron: str | None = Form(default=None),
    processMode: str | None = Form(default=None),
    chunkStrategy: str | None = Form(default=None),
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    data = await KnowledgeService(session).upload_document(
        kb_id,
        file,
        sourceType,
        sourceLocation,
        scheduleEnabled,
        scheduleCron,
        processMode,
        chunkStrategy,
        user,
    )
    return success(data)


@router.get("/knowledge-base/docs/{doc_id}")
async def get_doc(
    doc_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await KnowledgeService(session).get_document(doc_id))


@router.put("/knowledge-base/docs/{doc_id}")
async def update_doc(
    doc_id: str,
    payload: KnowledgeDocumentUpdateRequest,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).update_document(doc_id, payload, user)
    return success()


@router.post("/knowledge-base/docs/{doc_id}/chunk")
async def start_chunk(
    doc_id: str,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).start_chunking(doc_id, user)
    return success()


@router.patch("/knowledge-base/docs/{doc_id}/enable")
async def enable_doc(
    doc_id: str,
    value: bool,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).enable_document(doc_id, value)
    return success()


@router.delete("/knowledge-base/docs/{doc_id}")
async def delete_doc(
    doc_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).delete_document(doc_id)
    return success()


@router.get("/knowledge-base/docs/{doc_id}/chunks")
async def page_chunks(
    doc_id: str,
    current: int = Query(default=1),
    size: int = Query(default=10),
    enabled: int | None = Query(default=None),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = KnowledgeService(session)
    records, total = await service.page_chunks(doc_id, current, size, enabled)
    data = [service.chunk_to_dict(item) for item in records]
    return success(page(data, total, current, size).model_dump())


@router.post("/knowledge-base/docs/{doc_id}/chunks")
async def create_chunk(
    doc_id: str,
    payload: ChunkCreateRequest,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    return success(await KnowledgeService(session).create_chunk(doc_id, payload, user))


@router.put("/knowledge-base/docs/{doc_id}/chunks/{chunk_id}")
async def update_chunk(
    doc_id: str,
    chunk_id: str,
    payload: ChunkUpdateRequest,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).update_chunk(doc_id, chunk_id, payload, user)
    return success()


@router.delete("/knowledge-base/docs/{doc_id}/chunks/{chunk_id}")
async def delete_chunk(
    doc_id: str,
    chunk_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).delete_chunk(doc_id, chunk_id)
    return success()


@router.post("/knowledge-base/docs/{doc_id}/chunks/{chunk_id}/enable")
async def enable_chunk(
    doc_id: str,
    chunk_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).set_chunk_enabled(doc_id, chunk_id, True)
    return success()


@router.post("/knowledge-base/docs/{doc_id}/chunks/{chunk_id}/disable")
async def disable_chunk(
    doc_id: str,
    chunk_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).set_chunk_enabled(doc_id, chunk_id, False)
    return success()


@router.post("/knowledge-base/docs/{doc_id}/chunks/batch-enable")
async def batch_enable_chunks(
    doc_id: str,
    payload: dict,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).batch_set_chunk_enabled(doc_id, payload.get("chunkIds"), True)
    return success()


@router.post("/knowledge-base/docs/{doc_id}/chunks/batch-disable")
async def batch_disable_chunks(
    doc_id: str,
    payload: dict,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).batch_set_chunk_enabled(doc_id, payload.get("chunkIds"), False)
    return success()


@router.post("/knowledge-base/docs/{doc_id}/chunks/rebuild")
async def rebuild_chunks(
    doc_id: str,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await KnowledgeService(session).rebuild_chunks(doc_id, user)
    return success()


@router.get("/knowledge-base/docs/{doc_id}/chunk-logs")
async def page_chunk_logs(
    doc_id: str,
    pageNo: int = Query(default=1),
    pageSize: int = Query(default=10),
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = KnowledgeService(session)
    records, total = await service.page_chunk_logs(doc_id, pageNo, pageSize)
    data = [service.chunk_log_to_dict(item) for item in records]
    return success(page(data, total, pageNo, pageSize).model_dump())