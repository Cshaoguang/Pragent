from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db_session
from backend.api.responses import success
from backend.api.sse import sse_stream
from backend.services.rag_chat import RagChatService

router = APIRouter()


@router.get("/rag/v3/chat")
async def chat(
    question: str = Query(...),
    conversationId: str | None = Query(default=None),
    deepThinking: bool = Query(default=False),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    generator = RagChatService(session).stream_chat(question, conversationId, deepThinking, user)
    return StreamingResponse(sse_stream(generator), media_type="text/event-stream")


@router.post("/rag/v3/stop")
async def stop_task(
    taskId: str,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    _ = user
    await RagChatService(session).stop_task(taskId)
    return success()