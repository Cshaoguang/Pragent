from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, SoftDeleteMixin, TimestampMixin


class Conversation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_conversation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(128))
    last_time: Mapped[datetime | None] = mapped_column(DateTime)


class ConversationSummary(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_conversation_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64))
    last_message_id: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text)


class IngestionPipeline(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_ingestion_pipeline"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    updated_by: Mapped[str] = mapped_column(String(64), default="")


class IngestionPipelineNode(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_ingestion_pipeline_node"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(BigInteger, index=True)
    node_id: Mapped[str] = mapped_column(String(64))
    node_type: Mapped[str] = mapped_column(String(30))
    next_node_id: Mapped[str | None] = mapped_column(String(64))
    settings_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    condition_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    updated_by: Mapped[str] = mapped_column(String(64), default="")


class IngestionTask(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_ingestion_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(BigInteger, index=True)
    source_type: Mapped[str] = mapped_column(String(20))
    source_location: Mapped[str | None] = mapped_column(Text)
    source_file_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), index=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    logs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    updated_by: Mapped[str] = mapped_column(String(64), default="")


class IngestionTaskNode(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_ingestion_task_node"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_id: Mapped[int] = mapped_column(BigInteger, index=True)
    pipeline_id: Mapped[int] = mapped_column(BigInteger, index=True)
    node_id: Mapped[str] = mapped_column(String(64))
    node_type: Mapped[str] = mapped_column(String(30))
    node_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), index=True)
    duration_ms: Mapped[int] = mapped_column(BigInteger, default=0)
    message: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class IntentNode(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_intent_node"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kb_id: Mapped[int | None] = mapped_column(BigInteger)
    intent_code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    level: Mapped[int] = mapped_column(Integer)
    parent_code: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(512))
    examples: Mapped[str | None] = mapped_column(Text)
    collection_name: Mapped[str | None] = mapped_column(String(128))
    top_k: Mapped[int | None] = mapped_column(Integer)
    mcp_tool_id: Mapped[str | None] = mapped_column(String(128))
    kind: Mapped[int] = mapped_column(Integer, default=0)
    prompt_snippet: Mapped[str | None] = mapped_column(Text)
    prompt_template: Mapped[str | None] = mapped_column(Text)
    param_prompt_template: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    create_by: Mapped[str | None] = mapped_column(String(64))
    update_by: Mapped[str | None] = mapped_column(String(64))


class KnowledgeBase(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_knowledge_base"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128))
    embedding_model: Mapped[str] = mapped_column(String(128))
    collection_name: Mapped[str] = mapped_column(String(128), unique=True)
    created_by: Mapped[str] = mapped_column(String(64))
    updated_by: Mapped[str | None] = mapped_column(String(64))


class KnowledgeChunk(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_knowledge_chunk"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(BigInteger, index=True)
    doc_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    char_count: Mapped[int | None] = mapped_column(Integer)
    token_count: Mapped[int | None] = mapped_column(Integer)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str] = mapped_column(String(64))
    updated_by: Mapped[str | None] = mapped_column(String(64))


class KnowledgeDocument(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_knowledge_document"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(BigInteger, index=True)
    doc_name: Mapped[str] = mapped_column(String(256))
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    file_url: Mapped[str] = mapped_column(String(1024))
    file_type: Mapped[str] = mapped_column(String(32))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    process_mode: Mapped[str | None] = mapped_column(String(32), default="chunk")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    source_type: Mapped[str | None] = mapped_column(String(32))
    source_location: Mapped[str | None] = mapped_column(String(1024))
    schedule_enabled: Mapped[int | None] = mapped_column(Integer)
    schedule_cron: Mapped[str | None] = mapped_column(String(128))
    chunk_strategy: Mapped[str | None] = mapped_column(String(32))
    chunk_config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    pipeline_id: Mapped[int | None] = mapped_column(BigInteger)
    created_by: Mapped[str] = mapped_column(String(64))
    updated_by: Mapped[str | None] = mapped_column(String(64))


class KnowledgeDocumentChunkLog(Base):
    __tablename__ = "t_knowledge_document_chunk_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    doc_id: Mapped[int] = mapped_column(BigInteger, index=True)
    status: Mapped[str] = mapped_column(String(20))
    process_mode: Mapped[str | None] = mapped_column(String(20))
    chunk_strategy: Mapped[str | None] = mapped_column(String(50))
    pipeline_id: Mapped[int | None] = mapped_column(BigInteger)
    extract_duration: Mapped[int | None] = mapped_column(BigInteger)
    chunk_duration: Mapped[int | None] = mapped_column(BigInteger)
    embedding_duration: Mapped[int | None] = mapped_column(BigInteger)
    total_duration: Mapped[int | None] = mapped_column(BigInteger)
    chunk_count: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    create_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)


class KnowledgeDocumentSchedule(Base, TimestampMixin):
    __tablename__ = "t_knowledge_document_schedule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    doc_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    kb_id: Mapped[int] = mapped_column(BigInteger)
    cron_expr: Mapped[str | None] = mapped_column(String(128))
    enabled: Mapped[int] = mapped_column(Integer, default=0)
    next_run_time: Mapped[datetime | None] = mapped_column(DateTime)
    last_run_time: Mapped[datetime | None] = mapped_column(DateTime)
    last_success_time: Mapped[datetime | None] = mapped_column(DateTime)
    last_status: Mapped[str | None] = mapped_column(String(32))
    last_error: Mapped[str | None] = mapped_column(String(512))
    last_etag: Mapped[str | None] = mapped_column(String(256))
    last_modified: Mapped[str | None] = mapped_column(String(256))
    last_content_hash: Mapped[str | None] = mapped_column(String(128))
    lock_owner: Mapped[str | None] = mapped_column(String(128))
    lock_until: Mapped[datetime | None] = mapped_column(DateTime)


class KnowledgeDocumentScheduleExec(Base, TimestampMixin):
    __tablename__ = "t_knowledge_document_schedule_exec"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    schedule_id: Mapped[int] = mapped_column(BigInteger, index=True)
    doc_id: Mapped[int] = mapped_column(BigInteger, index=True)
    kb_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(String(512))
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    file_name: Mapped[str | None] = mapped_column(String(512))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    etag: Mapped[str | None] = mapped_column(String(256))
    last_modified: Mapped[str | None] = mapped_column(String(256))


class Message(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)


class MessageFeedback(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_message_feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInteger, index=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    vote: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(String(255))
    comment: Mapped[str | None] = mapped_column(String(1024))


class QueryTermMapping(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_query_term_mapping"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    domain: Mapped[str | None] = mapped_column(String(64))
    source_term: Mapped[str] = mapped_column(String(128), index=True)
    target_term: Mapped[str] = mapped_column(String(128))
    match_type: Mapped[int] = mapped_column(Integer, default=1)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    remark: Mapped[str | None] = mapped_column(String(255))
    create_by: Mapped[str | None] = mapped_column(String(64))
    update_by: Mapped[str | None] = mapped_column(String(64))


class RagTraceNode(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_rag_trace_node"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    node_id: Mapped[str] = mapped_column(String(64))
    parent_node_id: Mapped[str | None] = mapped_column(String(64))
    depth: Mapped[int] = mapped_column(Integer, default=0)
    node_type: Mapped[str | None] = mapped_column(String(64))
    node_name: Mapped[str | None] = mapped_column(String(128))
    class_name: Mapped[str | None] = mapped_column(String(256))
    method_name: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="RUNNING")
    error_message: Mapped[str | None] = mapped_column(String(1000))
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    extra_data: Mapped[str | None] = mapped_column(Text)


class RagTraceRun(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_rag_trace_run"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(64), unique=True)
    trace_name: Mapped[str | None] = mapped_column(String(128))
    entry_method: Mapped[str | None] = mapped_column(String(256))
    conversation_id: Mapped[str | None] = mapped_column(String(64))
    task_id: Mapped[str | None] = mapped_column(String(64), index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="RUNNING")
    error_message: Mapped[str | None] = mapped_column(String(1000))
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    extra_data: Mapped[str | None] = mapped_column(Text)


class SampleQuestion(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_sample_question"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(String(1024))


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(32), default="user")
    avatar: Mapped[str | None] = mapped_column(String(128))
