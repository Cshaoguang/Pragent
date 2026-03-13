from __future__ import annotations

from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import IngestionPipeline, IngestionPipelineNode, IngestionTask, IngestionTaskNode
from backend.models.schemas import AuthenticatedUser, IngestionPipelinePayload, IngestionTaskCreateRequest
from backend.services.common import paginate
from backend.services.ids import new_long_id
from backend.services.knowledge import KnowledgeService


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.knowledge_service = KnowledgeService(session)

    async def page_pipelines(self, current: int, size: int, keyword: str | None):
        stmt = select(IngestionPipeline).where(IngestionPipeline.deleted == 0)
        if keyword:
            stmt = stmt.where(IngestionPipeline.name.like(f"%{keyword}%"))
        stmt = stmt.order_by(IngestionPipeline.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def get_pipeline(self, pipeline_id: str) -> dict:
        pipeline = await self.session.get(IngestionPipeline, int(pipeline_id))
        if pipeline is None or pipeline.deleted != 0:
            raise ValueError("摄取流水线不存在")
        await self.session.refresh(pipeline, attribute_names=["create_time", "update_time"])
        node_stmt = select(IngestionPipelineNode).where(IngestionPipelineNode.pipeline_id == pipeline.id, IngestionPipelineNode.deleted == 0).order_by(IngestionPipelineNode.id.asc())
        nodes = (await self.session.execute(node_stmt)).scalars().all()
        return self.pipeline_to_dict(pipeline, nodes)

    async def create_pipeline(self, payload: IngestionPipelinePayload, current_user: AuthenticatedUser) -> dict:
        pipeline = IngestionPipeline(
            id=new_long_id(),
            name=payload.name,
            description=payload.description,
            created_by=current_user.username,
            updated_by=current_user.username,
        )
        self.session.add(pipeline)
        await self.session.flush()
        for node_order, node in enumerate(payload.nodes):
            self.session.add(
                IngestionPipelineNode(
                    id=new_long_id(),
                    pipeline_id=pipeline.id,
                    node_id=node.node_id,
                    node_type=node.node_type,
                    next_node_id=node.next_node_id,
                    settings_json=node.settings,
                    condition_json=node.condition,
                    created_by=current_user.username,
                    updated_by=current_user.username,
                )
            )
        await self.session.commit()
        return await self.get_pipeline(str(pipeline.id))

    async def update_pipeline(self, pipeline_id: str, payload: IngestionPipelinePayload, current_user: AuthenticatedUser) -> dict:
        pipeline = await self.session.get(IngestionPipeline, int(pipeline_id))
        if pipeline is None or pipeline.deleted != 0:
            raise ValueError("摄取流水线不存在")
        pipeline.name = payload.name
        pipeline.description = payload.description
        pipeline.updated_by = current_user.username
        node_stmt = select(IngestionPipelineNode).where(IngestionPipelineNode.pipeline_id == pipeline.id, IngestionPipelineNode.deleted == 0)
        old_nodes = (await self.session.execute(node_stmt)).scalars().all()
        for item in old_nodes:
            item.deleted = 1
        await self.session.flush()
        for node in payload.nodes:
            self.session.add(
                IngestionPipelineNode(
                    id=new_long_id(),
                    pipeline_id=pipeline.id,
                    node_id=node.node_id,
                    node_type=node.node_type,
                    next_node_id=node.next_node_id,
                    settings_json=node.settings,
                    condition_json=node.condition,
                    created_by=current_user.username,
                    updated_by=current_user.username,
                )
            )
        await self.session.commit()
        return await self.get_pipeline(str(pipeline.id))

    async def delete_pipeline(self, pipeline_id: str) -> None:
        pipeline = await self.session.get(IngestionPipeline, int(pipeline_id))
        if pipeline is None:
            return
        pipeline.deleted = 1
        await self.session.commit()

    async def page_tasks(self, current: int, size: int, status: str | None):
        stmt = select(IngestionTask).where(IngestionTask.deleted == 0)
        if status:
            stmt = stmt.where(IngestionTask.status == status)
        stmt = stmt.order_by(IngestionTask.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def get_task(self, task_id: str) -> dict:
        task = await self.session.get(IngestionTask, int(task_id))
        if task is None or task.deleted != 0:
            raise ValueError("摄取任务不存在")
        return self.task_to_dict(task)

    async def list_task_nodes(self, task_id: str) -> list[dict]:
        stmt = select(IngestionTaskNode).where(IngestionTaskNode.task_id == int(task_id), IngestionTaskNode.deleted == 0).order_by(IngestionTaskNode.node_order.asc(), IngestionTaskNode.id.asc())
        nodes = (await self.session.execute(stmt)).scalars().all()
        return [self.task_node_to_dict(node) for node in nodes]

    async def create_task(self, payload: IngestionTaskCreateRequest, current_user: AuthenticatedUser) -> dict:
        task = IngestionTask(
            id=new_long_id(),
            pipeline_id=int(payload.pipeline_id),
            source_type=payload.source.type,
            source_location=payload.source.location,
            source_file_name=payload.source.file_name,
            status="PENDING",
            metadata_json=payload.metadata,
            created_by=current_user.username,
            updated_by=current_user.username,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(task)
        await self.session.commit()
        return {
            "taskId": str(task.id),
            "pipelineId": str(task.pipeline_id),
            "status": task.status,
            "chunkCount": task.chunk_count,
            "message": "任务已创建",
        }

    async def upload_task(self, pipeline_id: str, file: UploadFile, current_user: AuthenticatedUser) -> dict:
        task = IngestionTask(
            id=new_long_id(),
            pipeline_id=int(pipeline_id),
            source_type="file",
            source_location=file.filename,
            source_file_name=file.filename,
            status="RUNNING",
            metadata_json=None,
            created_by=current_user.username,
            updated_by=current_user.username,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(task)
        await self.session.flush()
        self.session.add(
            IngestionTaskNode(
                id=new_long_id(),
                task_id=task.id,
                pipeline_id=task.pipeline_id,
                node_id="upload",
                node_type="upload",
                node_order=1,
                status="SUCCESS",
                duration_ms=0,
                message="文件接收成功",
            )
        )
        await self.session.commit()
        return {
            "taskId": str(task.id),
            "pipelineId": str(task.pipeline_id),
            "status": task.status,
            "chunkCount": task.chunk_count,
            "message": "文件已上传，等待处理",
        }

    def pipeline_to_dict(self, pipeline: IngestionPipeline, nodes: list[IngestionPipelineNode]) -> dict:
        return {
            "id": str(pipeline.id),
            "name": pipeline.name,
            "description": pipeline.description,
            "createdBy": pipeline.created_by,
            "createTime": pipeline.create_time,
            "updateTime": pipeline.update_time,
            "nodes": [
                {
                    "id": node.id,
                    "nodeId": node.node_id,
                    "nodeType": node.node_type,
                    "settings": node.settings_json,
                    "condition": node.condition_json,
                    "nextNodeId": node.next_node_id,
                }
                for node in nodes
            ],
        }

    def task_to_dict(self, task: IngestionTask) -> dict:
        return {
            "id": str(task.id),
            "pipelineId": str(task.pipeline_id),
            "sourceType": task.source_type,
            "sourceLocation": task.source_location,
            "sourceFileName": task.source_file_name,
            "status": task.status,
            "chunkCount": task.chunk_count,
            "errorMessage": task.error_message,
            "logs": task.logs_json,
            "metadata": task.metadata_json,
            "startedAt": task.started_at,
            "completedAt": task.completed_at,
            "createdBy": task.created_by,
            "createTime": task.create_time,
            "updateTime": task.update_time,
        }

    def task_node_to_dict(self, node: IngestionTaskNode) -> dict:
        return {
            "id": str(node.id),
            "taskId": str(node.task_id),
            "pipelineId": str(node.pipeline_id),
            "nodeId": node.node_id,
            "nodeType": node.node_type,
            "nodeOrder": node.node_order,
            "status": node.status,
            "durationMs": node.duration_ms,
            "message": node.message,
            "errorMessage": node.error_message,
            "output": node.output_json,
            "createTime": node.create_time,
            "updateTime": node.update_time,
        }