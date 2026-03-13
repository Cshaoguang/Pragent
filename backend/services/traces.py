from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import RagTraceNode, RagTraceRun
from backend.services.common import paginate
from backend.services.ids import new_long_id


class TraceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def start_run(self, trace_name: str, entry_method: str, conversation_id: str | None, task_id: str | None, user_id: str | None) -> RagTraceRun:
        trace = RagTraceRun(
            id=new_long_id(),
            trace_id=f"trace_{new_long_id()}",
            trace_name=trace_name,
            entry_method=entry_method,
            conversation_id=conversation_id,
            task_id=task_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            status="RUNNING",
        )
        self.session.add(trace)
        await self.session.commit()
        return trace

    async def finish_run(self, trace_id: str, status: str, error_message: str | None = None) -> None:
        stmt = select(RagTraceRun).where(RagTraceRun.trace_id == trace_id, RagTraceRun.deleted == 0)
        trace = (await self.session.execute(stmt)).scalar_one_or_none()
        if trace is None:
            return
        now = datetime.utcnow()
        trace.status = status
        trace.error_message = error_message
        trace.end_time = now
        if trace.start_time:
            trace.duration_ms = int((now - trace.start_time).total_seconds() * 1000)
        await self.session.commit()

    async def create_node(self, trace_id: str, node_id: str, node_name: str, node_type: str, depth: int = 0, parent_node_id: str | None = None) -> RagTraceNode:
        node = RagTraceNode(
            id=new_long_id(),
            trace_id=trace_id,
            node_id=node_id,
            parent_node_id=parent_node_id,
            depth=depth,
            node_type=node_type,
            node_name=node_name,
            class_name=node_type,
            method_name=node_name,
            start_time=datetime.utcnow(),
            status="RUNNING",
        )
        self.session.add(node)
        await self.session.commit()
        return node

    async def finish_node(self, trace_id: str, node_id: str, status: str = "SUCCESS", error_message: str | None = None) -> None:
        stmt = select(RagTraceNode).where(
            RagTraceNode.trace_id == trace_id,
            RagTraceNode.node_id == node_id,
            RagTraceNode.deleted == 0,
        )
        node = (await self.session.execute(stmt)).scalar_one_or_none()
        if node is None:
            return
        now = datetime.utcnow()
        node.status = status
        node.error_message = error_message
        node.end_time = now
        if node.start_time:
            node.duration_ms = int((now - node.start_time).total_seconds() * 1000)
        await self.session.commit()

    async def page_runs(
        self,
        current: int,
        size: int,
        trace_id: str | None,
        conversation_id: str | None,
        task_id: str | None,
        status: str | None,
    ):
        stmt: Select = select(RagTraceRun).where(RagTraceRun.deleted == 0)
        if trace_id:
            stmt = stmt.where(RagTraceRun.trace_id == trace_id)
        if conversation_id:
            stmt = stmt.where(RagTraceRun.conversation_id == conversation_id)
        if task_id:
            stmt = stmt.where(RagTraceRun.task_id == task_id)
        if status:
            stmt = stmt.where(RagTraceRun.status == status)
        stmt = stmt.order_by(RagTraceRun.start_time.desc(), RagTraceRun.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def get_detail(self, trace_id: str) -> dict:
        run_stmt = select(RagTraceRun).where(RagTraceRun.trace_id == trace_id, RagTraceRun.deleted == 0)
        node_stmt = select(RagTraceNode).where(RagTraceNode.trace_id == trace_id, RagTraceNode.deleted == 0).order_by(RagTraceNode.depth.asc(), RagTraceNode.start_time.asc())
        run = (await self.session.execute(run_stmt)).scalar_one_or_none()
        if run is None:
            raise ValueError("Trace 不存在")
        nodes = (await self.session.execute(node_stmt)).scalars().all()
        return {
            "run": self._run_to_dict(run),
            "nodes": [self._node_to_dict(node) for node in nodes],
        }

    async def list_nodes(self, trace_id: str) -> list[dict]:
        stmt = select(RagTraceNode).where(RagTraceNode.trace_id == trace_id, RagTraceNode.deleted == 0).order_by(RagTraceNode.depth.asc(), RagTraceNode.start_time.asc())
        nodes = (await self.session.execute(stmt)).scalars().all()
        return [self._node_to_dict(node) for node in nodes]

    def _run_to_dict(self, run: RagTraceRun) -> dict:
        return {
            "traceId": run.trace_id,
            "traceName": run.trace_name,
            "entryMethod": run.entry_method,
            "conversationId": run.conversation_id,
            "taskId": run.task_id,
            "userId": run.user_id,
            "status": run.status,
            "errorMessage": run.error_message,
            "durationMs": run.duration_ms,
            "startTime": run.start_time,
            "endTime": run.end_time,
        }

    def _node_to_dict(self, node: RagTraceNode) -> dict:
        return {
            "traceId": node.trace_id,
            "nodeId": node.node_id,
            "parentNodeId": node.parent_node_id,
            "depth": node.depth,
            "nodeType": node.node_type,
            "nodeName": node.node_name,
            "className": node.class_name,
            "methodName": node.method_name,
            "status": node.status,
            "errorMessage": node.error_message,
            "durationMs": node.duration_ms,
            "startTime": node.start_time,
            "endTime": node.end_time,
        }