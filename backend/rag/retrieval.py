from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import IntentNode, KnowledgeChunk, KnowledgeDocument
from backend.rag.model_router import ModelRouter
from backend.vectorstore.qdrant_store import get_qdrant


@dataclass(slots=True)
class RetrievedChunk:
    doc_id: int
    kb_id: int
    chunk_id: int
    score: float
    content: str
    chunk_index: int | None = None


class RetrievalEngine:
    def __init__(self, session: AsyncSession, model_router: ModelRouter) -> None:
        self.session = session
        self.model_router = model_router

    async def detect_intent(self, question: str) -> dict:
        stmt = select(IntentNode).where(IntentNode.deleted == 0, IntentNode.enabled == 1)
        nodes = (await self.session.execute(stmt)).scalars().all()
        lowered = question.lower()
        ranked: list[tuple[float, IntentNode]] = []
        for node in nodes:
            score = 0.0
            if node.name.lower() in lowered:
                score += 0.8
            if node.intent_code.lower() in lowered:
                score += 0.9
            if node.description and any(term in lowered for term in node.description.lower().split()[:6]):
                score += 0.3
            if node.examples and any(example.strip().lower() in lowered for example in node.examples.split("\n")[:3]):
                score += 0.2
            if score > 0:
                ranked.append((score, node))
        ranked.sort(key=lambda item: item[0], reverse=True)
        best = ranked[0][1] if ranked else None
        confidence = ranked[0][0] if ranked else 0.0
        return {
            "intent": best,
            "confidence": confidence,
            "use_global": confidence < 0.6,
        }

    async def rewrite_question(self, question: str) -> str:
        return " ".join(question.split())

    async def retrieve(self, question: str, intent: dict, top_k: int = 5) -> list[RetrievedChunk]:
        vectors = await self.model_router.embed_texts([question])
        vector = vectors[0]
        chunks: list[RetrievedChunk] = []
        target_collections: list[str] = []
        intent_node = intent.get("intent")
        if intent_node and getattr(intent_node, "collection_name", None):
            target_collections.append(intent_node.collection_name)
        if intent.get("use_global"):
            docs_stmt = select(KnowledgeDocument.kb_id).where(KnowledgeDocument.deleted == 0, KnowledgeDocument.enabled == 1)
            kb_ids = {row[0] for row in (await self.session.execute(docs_stmt)).all()}
            if intent_node and getattr(intent_node, "kb_id", None):
                kb_ids.add(intent_node.kb_id)
            if kb_ids:
                kb_stmt = select(IntentNode.collection_name).where(IntentNode.kb_id.in_(kb_ids), IntentNode.deleted == 0)
                target_collections.extend([row[0] for row in (await self.session.execute(kb_stmt)).all() if row[0]])
        target_collections = list(dict.fromkeys(target_collections))
        client = get_qdrant()
        for collection in target_collections:
            try:
                result = await client.query_points(
                    collection_name=collection,
                    query=vector,
                    with_payload=True,
                    limit=top_k,
                    query_filter=models.Filter(
                        must=[models.FieldCondition(key="enabled", match=models.MatchValue(value=1))]
                    ),
                )
            except Exception:  # noqa: BLE001
                continue
            points = getattr(result, "points", result)
            for point in points:
                payload = point.payload or {}
                chunks.append(
                    RetrievedChunk(
                        doc_id=int(payload.get("doc_id", 0)),
                        kb_id=int(payload.get("kb_id", 0)),
                        chunk_id=int(payload.get("chunk_id", point.id)),
                        score=float(getattr(point, "score", 0.0) or 0.0),
                        content=str(payload.get("content", "")),
                        chunk_index=payload.get("chunk_index"),
                    )
                )
        if chunks:
            return self._deduplicate(chunks)[:top_k]
        return await self._fallback_retrieve(question, top_k)

    async def _fallback_retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        stmt = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.deleted == 0, KnowledgeChunk.enabled == 1)
            .order_by(KnowledgeChunk.update_time.desc(), KnowledgeChunk.id.desc())
            .limit(max(top_k * 4, 20))
        )
        candidates = (await self.session.execute(stmt)).scalars().all()
        scored: list[RetrievedChunk] = []
        tokens = {token.lower() for token in question.split() if token.strip()}
        for chunk in candidates:
            content_tokens = chunk.content.lower()
            score = sum(1 for token in tokens if token in content_tokens)
            if score == 0:
                continue
            scored.append(
                RetrievedChunk(
                    doc_id=chunk.doc_id,
                    kb_id=chunk.kb_id,
                    chunk_id=chunk.id,
                    score=float(score),
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def _deduplicate(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        deduped: dict[int, RetrievedChunk] = {}
        for chunk in sorted(chunks, key=lambda item: item.score, reverse=True):
            deduped.setdefault(chunk.chunk_id, chunk)
        return list(deduped.values())