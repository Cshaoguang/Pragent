from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="userId")
    username: str
    role: str
    avatar: str | None = None
    token: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(AuthenticatedUser):
    pass


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    avatar: str | None = None


class UserUpdateRequest(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None
    avatar: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(alias="newPassword")


class ConversationRenameRequest(BaseModel):
    title: str


class FeedbackRequest(BaseModel):
    vote: int


class KnowledgeBaseRequest(BaseModel):
    name: str
    embedding_model: str | None = Field(default=None, alias="embeddingModel")


class KnowledgeBaseUpdateRequest(BaseModel):
    name: str | None = None
    embedding_model: str | None = Field(default=None, alias="embeddingModel")


class KnowledgeDocumentUpdateRequest(BaseModel):
    doc_name: str | None = Field(default=None, alias="docName")


class ChunkCreateRequest(BaseModel):
    content: str
    index: int | None = None
    chunk_id: str | None = Field(default=None, alias="chunkId")


class ChunkUpdateRequest(BaseModel):
    content: str


class IngestionPipelineNodePayload(BaseModel):
    node_id: str = Field(alias="nodeId")
    node_type: str = Field(alias="nodeType")
    settings: dict[str, Any] | None = None
    condition: dict[str, Any] | None = None
    next_node_id: str | None = Field(default=None, alias="nextNodeId")


class IngestionPipelinePayload(BaseModel):
    name: str
    description: str | None = None
    nodes: list[IngestionPipelineNodePayload] = Field(default_factory=list)


class IngestionTaskSourcePayload(BaseModel):
    type: str
    location: str
    file_name: str | None = Field(default=None, alias="fileName")
    credentials: dict[str, str] | None = None


class IngestionTaskCreateRequest(BaseModel):
    pipeline_id: str = Field(alias="pipelineId")
    source: IngestionTaskSourcePayload
    metadata: dict[str, Any] | None = None


class IntentNodePayload(BaseModel):
    kb_id: str | None = Field(default=None, alias="kbId")
    intent_code: str = Field(alias="intentCode")
    name: str
    level: int
    parent_code: str | None = Field(default=None, alias="parentCode")
    description: str | None = None
    examples: list[str] | None = None
    collection_name: str | None = Field(default=None, alias="collectionName")
    mcp_tool_id: str | None = Field(default=None, alias="mcpToolId")
    top_k: int | None = Field(default=None, alias="topK")
    kind: int | None = None
    sort_order: int | None = Field(default=None, alias="sortOrder")
    enabled: int | None = None
    prompt_snippet: str | None = Field(default=None, alias="promptSnippet")
    prompt_template: str | None = Field(default=None, alias="promptTemplate")
    param_prompt_template: str | None = Field(default=None, alias="paramPromptTemplate")


class IntentNodeUpdatePayload(BaseModel):
    kb_id: str | None = Field(default=None, alias="kbId")
    intent_code: str | None = Field(default=None, alias="intentCode")
    name: str | None = None
    level: int | None = None
    parent_code: str | None = Field(default=None, alias="parentCode")
    description: str | None = None
    examples: list[str] | None = None
    collection_name: str | None = Field(default=None, alias="collectionName")
    mcp_tool_id: str | None = Field(default=None, alias="mcpToolId")
    top_k: int | None = Field(default=None, alias="topK")
    kind: int | None = None
    sort_order: int | None = Field(default=None, alias="sortOrder")
    enabled: int | None = None
    prompt_snippet: str | None = Field(default=None, alias="promptSnippet")
    prompt_template: str | None = Field(default=None, alias="promptTemplate")
    param_prompt_template: str | None = Field(default=None, alias="paramPromptTemplate")


class BatchIdsRequest(BaseModel):
    ids: list[int]


class SampleQuestionPayload(BaseModel):
    title: str | None = None
    description: str | None = None
    question: str | None = None


class ChatQuery(BaseModel):
    question: str
    conversation_id: str | None = Field(default=None, alias="conversationId")
    deep_thinking: bool = Field(default=False, alias="deepThinking")


class MessageResponse(BaseModel):
    id: str
    conversation_id: str = Field(alias="conversationId")
    role: str
    content: str
    vote: int | None = None
    create_time: datetime | None = Field(default=None, alias="createTime")
