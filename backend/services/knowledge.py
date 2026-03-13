from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from qdrant_client import models
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ingestion.chunker import Chunker
from backend.ingestion.parsers import DocumentParser
from backend.models.entities import (
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeDocumentChunkLog,
)
from backend.models.schemas import (
    AuthenticatedUser,
    ChunkCreateRequest,
    ChunkUpdateRequest,
    KnowledgeBaseRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeDocumentUpdateRequest,
)
from backend.rag.model_router import ModelRouter
from backend.services.common import paginate
from backend.services.ids import new_long_id
from backend.tools.storage import StorageService
from backend.vectorstore.qdrant_store import get_qdrant


class KnowledgeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.storage = StorageService()
        self.parser = DocumentParser()
        self.chunker = Chunker()
        self.model_router = ModelRouter()

    async def page_bases(self, current: int, size: int, name: str | None):
        stmt = select(KnowledgeBase).where(KnowledgeBase.deleted == 0)
        if name:
            stmt = stmt.where(KnowledgeBase.name.like(f"%{name}%"))
        stmt = stmt.order_by(KnowledgeBase.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def get_base(self, kb_id: str) -> KnowledgeBase:
        kb = await self.session.get(KnowledgeBase, int(kb_id))
        if kb is None or kb.deleted != 0:
            raise ValueError("知识库不存在")
        return kb

    async def create_base(self, payload: KnowledgeBaseRequest, current_user: AuthenticatedUser) -> str:
        kb = KnowledgeBase(
            id=new_long_id(),
            name=payload.name,
            embedding_model=payload.embedding_model or "default",
            collection_name=f"kb_{new_long_id()}",
            created_by=current_user.username,
            updated_by=current_user.username,
        )
        self.session.add(kb)
        await self.session.commit()
        await self._ensure_collection(kb.collection_name)
        return str(kb.id)

    async def update_base(self, kb_id: str, payload: KnowledgeBaseUpdateRequest, current_user: AuthenticatedUser) -> None:
        kb = await self.get_base(kb_id)
        if payload.name is not None:
            kb.name = payload.name
        if payload.embedding_model is not None:
            kb.embedding_model = payload.embedding_model
        kb.updated_by = current_user.username
        await self.session.commit()

    async def delete_base(self, kb_id: str) -> None:
        kb = await self.get_base(kb_id)
        kb.deleted = 1
        await self.session.commit()

    async def page_documents(self, kb_id: str, current: int, size: int, status: str | None, keyword: str | None):
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.kb_id == int(kb_id), KnowledgeDocument.deleted == 0)
        if status:
            stmt = stmt.where(KnowledgeDocument.status == status)
        if keyword:
            stmt = stmt.where(KnowledgeDocument.doc_name.like(f"%{keyword}%"))
        stmt = stmt.order_by(KnowledgeDocument.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def search_documents(self, keyword: str, limit: int) -> list[dict]:
        stmt = (
            select(KnowledgeDocument, KnowledgeBase)
            .join(KnowledgeBase, KnowledgeBase.id == KnowledgeDocument.kb_id)
            .where(
                KnowledgeDocument.deleted == 0,
                KnowledgeBase.deleted == 0,
                or_(KnowledgeDocument.doc_name.like(f"%{keyword}%"), KnowledgeBase.name.like(f"%{keyword}%")),
            )
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "id": str(doc.id),
                "kbId": doc.kb_id,
                "docName": doc.doc_name,
                "kbName": kb.name,
            }
            for doc, kb in rows
        ]

    async def upload_document(
        self,
        kb_id: str,
        upload: UploadFile | None,
        source_type: str,
        source_location: str | None,
        schedule_enabled: bool,
        schedule_cron: str | None,
        process_mode: str | None,
        chunk_strategy: str | None,
        current_user: AuthenticatedUser,
    ) -> dict:
        kb = await self.get_base(kb_id)
        if source_type == "file":
            if upload is None:
                raise ValueError("缺少上传文件")
            content = await upload.read()
            file_name = upload.filename or f"upload-{new_long_id()}.txt"
            relative_path = f"knowledge/{kb.id}/{new_long_id()}-{file_name}"
            stored = await self.storage.save_bytes(relative_path, content)
            text = await self.parser.parse(file_name, content)
        else:
            raise ValueError("当前仅实现文件上传模式")
        document = KnowledgeDocument(
            id=new_long_id(),
            kb_id=kb.id,
            doc_name=file_name,
            enabled=1,
            file_url=stored.storage_path,
            file_type=Path(file_name).suffix.lower().lstrip("."),
            file_size=stored.size,
            process_mode=process_mode or "chunk",
            status="processing",
            source_type=source_type,
            source_location=source_location,
            schedule_enabled=1 if schedule_enabled else 0,
            schedule_cron=schedule_cron,
            chunk_strategy=chunk_strategy or "fixed_size",
            created_by=current_user.username,
            updated_by=current_user.username,
        )
        self.session.add(document)
        await self.session.commit()
        try:
            chunks = self.chunker.split_text(text)
            await self._replace_document_chunks(document, kb, chunks, current_user.username)
            document.status = "completed"
            document.chunk_count = len(chunks)
            await self._create_chunk_log(document.id, process_mode or "chunk", chunk_strategy or "fixed_size", len(chunks), None)
        except Exception as exc:  # noqa: BLE001
            document.status = "failed"
            await self._create_chunk_log(document.id, process_mode or "chunk", chunk_strategy or "fixed_size", 0, str(exc))
            raise
        finally:
            await self.session.commit()
        await self.session.refresh(document, attribute_names=["create_time", "update_time"])
        return self.document_to_dict(document)

    async def get_document(self, doc_id: str) -> dict:
        doc = await self.session.get(KnowledgeDocument, int(doc_id))
        if doc is None or doc.deleted != 0:
            raise ValueError("文档不存在")
        return self.document_to_dict(doc)

    async def update_document(self, doc_id: str, payload: KnowledgeDocumentUpdateRequest, current_user: AuthenticatedUser) -> None:
        doc = await self._get_document_entity(doc_id)
        if payload.doc_name is not None:
            doc.doc_name = payload.doc_name
        doc.updated_by = current_user.username
        await self.session.commit()

    async def start_chunking(self, doc_id: str, current_user: AuthenticatedUser) -> None:
        doc = await self._get_document_entity(doc_id)
        content = await self.storage.load_bytes(doc.file_url)
        text = await self.parser.parse(doc.doc_name, content)
        chunks = self.chunker.split_text(text)
        kb = await self.get_base(str(doc.kb_id))
        await self._replace_document_chunks(doc, kb, chunks, current_user.username)
        doc.status = "completed"
        doc.chunk_count = len(chunks)
        await self._create_chunk_log(doc.id, doc.process_mode or "chunk", doc.chunk_strategy or "fixed_size", len(chunks), None)
        await self.session.commit()

    async def enable_document(self, doc_id: str, enabled: bool) -> None:
        doc = await self._get_document_entity(doc_id)
        doc.enabled = 1 if enabled else 0
        await self.session.commit()

    async def delete_document(self, doc_id: str) -> None:
        doc = await self._get_document_entity(doc_id)
        doc.deleted = 1
        await self.session.commit()

    async def page_chunks(self, doc_id: str, current: int, size: int, enabled: int | None):
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.doc_id == int(doc_id), KnowledgeChunk.deleted == 0)
        if enabled is not None:
            stmt = stmt.where(KnowledgeChunk.enabled == enabled)
        stmt = stmt.order_by(KnowledgeChunk.chunk_index.asc(), KnowledgeChunk.id.asc())
        return await paginate(self.session, stmt, current, size)

    async def create_chunk(self, doc_id: str, payload: ChunkCreateRequest, current_user: AuthenticatedUser) -> dict:
        doc = await self._get_document_entity(doc_id)
        chunk = KnowledgeChunk(
            id=int(payload.chunk_id) if payload.chunk_id else new_long_id(),
            kb_id=doc.kb_id,
            doc_id=doc.id,
            chunk_index=payload.index or 0,
            content=payload.content,
            char_count=len(payload.content),
            token_count=len(payload.content) // 4,
            enabled=1,
            created_by=current_user.username,
            updated_by=current_user.username,
        )
        self.session.add(chunk)
        await self.session.commit()
        await self._upsert_chunk_vector(doc.kb_id, chunk)
        return self.chunk_to_dict(chunk)

    async def update_chunk(self, doc_id: str, chunk_id: str, payload: ChunkUpdateRequest, current_user: AuthenticatedUser) -> None:
        chunk = await self._get_chunk_entity(doc_id, chunk_id)
        chunk.content = payload.content
        chunk.char_count = len(payload.content)
        chunk.token_count = len(payload.content) // 4
        chunk.updated_by = current_user.username
        await self.session.commit()
        await self._upsert_chunk_vector(chunk.kb_id, chunk)

    async def delete_chunk(self, doc_id: str, chunk_id: str) -> None:
        chunk = await self._get_chunk_entity(doc_id, chunk_id)
        chunk.deleted = 1
        await self.session.commit()

    async def set_chunk_enabled(self, doc_id: str, chunk_id: str, enabled: bool) -> None:
        chunk = await self._get_chunk_entity(doc_id, chunk_id)
        chunk.enabled = 1 if enabled else 0
        await self.session.commit()
        await self._upsert_chunk_vector(chunk.kb_id, chunk)

    async def batch_set_chunk_enabled(self, doc_id: str, chunk_ids: list[int] | None, enabled: bool) -> None:
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.doc_id == int(doc_id), KnowledgeChunk.deleted == 0)
        if chunk_ids:
            stmt = stmt.where(KnowledgeChunk.id.in_(chunk_ids))
        items = (await self.session.execute(stmt)).scalars().all()
        for item in items:
            item.enabled = 1 if enabled else 0
        await self.session.commit()
        for item in items:
            await self._upsert_chunk_vector(item.kb_id, item)

    async def rebuild_chunks(self, doc_id: str, current_user: AuthenticatedUser) -> None:
        await self.start_chunking(doc_id, current_user)

    async def page_chunk_logs(self, doc_id: str, current: int, size: int):
        stmt = select(KnowledgeDocumentChunkLog).where(KnowledgeDocumentChunkLog.doc_id == int(doc_id)).order_by(KnowledgeDocumentChunkLog.create_time.desc(), KnowledgeDocumentChunkLog.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def _replace_document_chunks(self, doc: KnowledgeDocument, kb: KnowledgeBase, chunks: list[str], operator: str) -> None:
        old_stmt = select(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc.id, KnowledgeChunk.deleted == 0)
        old_chunks = (await self.session.execute(old_stmt)).scalars().all()
        for item in old_chunks:
            item.deleted = 1
        for index, content in enumerate(chunks):
            chunk = KnowledgeChunk(
                id=new_long_id(),
                kb_id=doc.kb_id,
                doc_id=doc.id,
                chunk_index=index,
                content=content,
                char_count=len(content),
                token_count=len(content) // 4,
                enabled=1,
                created_by=operator,
                updated_by=operator,
            )
            self.session.add(chunk)
            await self.session.flush()
            await self._upsert_chunk_vector(kb.id, chunk)

    async def _upsert_chunk_vector(self, kb_id: int, chunk: KnowledgeChunk) -> None:
        kb = await self.session.get(KnowledgeBase, kb_id)
        if kb is None or kb.deleted != 0:
            return
        await self._ensure_collection(kb.collection_name)
        embeddings = await self.model_router.embed_texts([chunk.content])
        point = models.PointStruct(
            id=chunk.id,
            vector=embeddings[0],
            payload={
                "kb_id": chunk.kb_id,
                "doc_id": chunk.doc_id,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "enabled": chunk.enabled,
            },
        )
        await get_qdrant().upsert(collection_name=kb.collection_name, wait=True, points=[point])

    async def _ensure_collection(self, collection_name: str) -> None:
        client = get_qdrant()
        collections = await client.get_collections()
        existing = {item.name for item in collections.collections}
        if collection_name in existing:
            return
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=self.model_router.settings.rag_embedding_dimension, distance=models.Distance.COSINE),
        )

    async def _create_chunk_log(self, doc_id: int, process_mode: str, chunk_strategy: str, chunk_count: int, error_message: str | None) -> None:
        item = KnowledgeDocumentChunkLog(
            id=new_long_id(),
            doc_id=doc_id,
            status="FAILED" if error_message else "SUCCESS",
            process_mode=process_mode,
            chunk_strategy=chunk_strategy,
            chunk_count=chunk_count,
            error_message=error_message,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            total_duration=0,
        )
        self.session.add(item)

    async def _get_document_entity(self, doc_id: str) -> KnowledgeDocument:
        doc = await self.session.get(KnowledgeDocument, int(doc_id))
        if doc is None or doc.deleted != 0:
            raise ValueError("文档不存在")
        return doc

    async def _get_chunk_entity(self, doc_id: str, chunk_id: str) -> KnowledgeChunk:
        chunk = await self.session.get(KnowledgeChunk, int(chunk_id))
        if chunk is None or chunk.deleted != 0 or chunk.doc_id != int(doc_id):
            raise ValueError("分块不存在")
        return chunk

    def base_to_dict(self, item: KnowledgeBase, document_count: int | None = None) -> dict:
        return {
            "id": str(item.id),
            "name": item.name,
            "embeddingModel": item.embedding_model,
            "collectionName": item.collection_name,
            "createdBy": item.created_by,
            "documentCount": document_count,
            "createTime": item.create_time,
            "updateTime": item.update_time,
        }

    def document_to_dict(self, item: KnowledgeDocument) -> dict:
        return {
            "id": str(item.id),
            "kbId": str(item.kb_id),
            "docName": item.doc_name,
            "sourceType": item.source_type,
            "sourceLocation": item.source_location,
            "scheduleEnabled": item.schedule_enabled,
            "scheduleCron": item.schedule_cron,
            "enabled": bool(item.enabled),
            "chunkCount": item.chunk_count,
            "fileUrl": item.file_url,
            "fileType": item.file_type,
            "fileSize": item.file_size,
            "processMode": item.process_mode,
            "chunkStrategy": item.chunk_strategy,
            "chunkConfig": item.chunk_config,
            "pipelineId": str(item.pipeline_id) if item.pipeline_id else None,
            "status": item.status,
            "createdBy": item.created_by,
            "updatedBy": item.updated_by,
            "createTime": item.create_time,
            "updateTime": item.update_time,
        }

    def chunk_to_dict(self, item: KnowledgeChunk) -> dict:
        return {
            "id": str(item.id),
            "kbId": str(item.kb_id),
            "docId": str(item.doc_id),
            "chunkIndex": item.chunk_index,
            "content": item.content,
            "contentHash": item.content_hash,
            "charCount": item.char_count,
            "tokenCount": item.token_count,
            "enabled": item.enabled,
            "createTime": item.create_time,
            "updateTime": item.update_time,
        }

    def chunk_log_to_dict(self, item: KnowledgeDocumentChunkLog) -> dict:
        return {
            "id": str(item.id),
            "docId": str(item.doc_id),
            "status": item.status,
            "processMode": item.process_mode,
            "chunkStrategy": item.chunk_strategy,
            "pipelineId": str(item.pipeline_id) if item.pipeline_id else None,
            "extractDuration": item.extract_duration,
            "chunkDuration": item.chunk_duration,
            "embeddingDuration": item.embedding_duration,
            "totalDuration": item.total_duration,
            "chunkCount": item.chunk_count,
            "errorMessage": item.error_message,
            "startTime": item.start_time,
            "endTime": item.end_time,
            "createTime": item.create_time,
        }