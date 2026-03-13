from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import IntentNode
from backend.models.schemas import BatchIdsRequest, IntentNodePayload, IntentNodeUpdatePayload


class IntentTreeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tree(self) -> list[dict]:
        stmt = select(IntentNode).where(IntentNode.deleted == 0).order_by(IntentNode.level.asc(), IntentNode.sort_order.asc(), IntentNode.id.asc())
        nodes = (await self.session.execute(stmt)).scalars().all()
        by_parent: dict[str | None, list[IntentNode]] = defaultdict(list)
        for node in nodes:
            by_parent[node.parent_code].append(node)
        return [self._to_tree(node, by_parent) for node in by_parent.get(None, [])]

    async def create(self, payload: IntentNodePayload, created_by: str) -> str:
        node = IntentNode(
            kb_id=int(payload.kb_id) if payload.kb_id else None,
            intent_code=payload.intent_code,
            name=payload.name,
            level=payload.level,
            parent_code=payload.parent_code,
            description=payload.description,
            examples="\n".join(payload.examples or []),
            collection_name=payload.collection_name,
            mcp_tool_id=payload.mcp_tool_id,
            top_k=payload.top_k,
            kind=payload.kind or 0,
            sort_order=payload.sort_order or 0,
            enabled=1 if payload.enabled is None else payload.enabled,
            prompt_snippet=payload.prompt_snippet,
            prompt_template=payload.prompt_template,
            param_prompt_template=payload.param_prompt_template,
            create_by=created_by,
            update_by=created_by,
        )
        self.session.add(node)
        await self.session.commit()
        return str(node.id)

    async def update(self, node_id: str, payload: IntentNodeUpdatePayload, updated_by: str) -> None:
        node = await self.session.get(IntentNode, int(node_id))
        if node is None or node.deleted != 0:
            raise ValueError("意图节点不存在")
        for field, value in {
            "kb_id": int(payload.kb_id) if payload.kb_id else None,
            "intent_code": payload.intent_code,
            "name": payload.name,
            "level": payload.level,
            "parent_code": payload.parent_code,
            "description": payload.description,
            "examples": "\n".join(payload.examples or []) if payload.examples is not None else None,
            "collection_name": payload.collection_name,
            "mcp_tool_id": payload.mcp_tool_id,
            "top_k": payload.top_k,
            "kind": payload.kind,
            "sort_order": payload.sort_order,
            "enabled": payload.enabled,
            "prompt_snippet": payload.prompt_snippet,
            "prompt_template": payload.prompt_template,
            "param_prompt_template": payload.param_prompt_template,
        }.items():
            if value is not None:
                setattr(node, field, value)
        node.update_by = updated_by
        await self.session.commit()

    async def delete(self, node_id: str) -> None:
        node = await self.session.get(IntentNode, int(node_id))
        if node is None:
            return
        node.deleted = 1
        await self.session.commit()

    async def batch_update_enabled(self, payload: BatchIdsRequest, enabled: int) -> None:
        for item_id in payload.ids:
            node = await self.session.get(IntentNode, item_id)
            if node is not None and node.deleted == 0:
                node.enabled = enabled
        await self.session.commit()

    async def batch_delete(self, payload: BatchIdsRequest) -> None:
        for item_id in payload.ids:
            node = await self.session.get(IntentNode, item_id)
            if node is not None:
                node.deleted = 1
        await self.session.commit()

    def _to_tree(self, node: IntentNode, by_parent: dict[str | None, list[IntentNode]]) -> dict:
        return {
            "id": node.id,
            "intentCode": node.intent_code,
            "name": node.name,
            "level": node.level,
            "parentCode": node.parent_code,
            "description": node.description,
            "examples": node.examples,
            "collectionName": node.collection_name,
            "mcpToolId": node.mcp_tool_id,
            "topK": node.top_k,
            "kind": node.kind,
            "sortOrder": node.sort_order,
            "enabled": node.enabled,
            "promptSnippet": node.prompt_snippet,
            "promptTemplate": node.prompt_template,
            "paramPromptTemplate": node.param_prompt_template,
            "children": [self._to_tree(child, by_parent) for child in by_parent.get(node.intent_code, [])],
        }