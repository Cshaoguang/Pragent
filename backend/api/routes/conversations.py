from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db_session
from backend.api.responses import success
from backend.models.schemas import ConversationRenameRequest, FeedbackRequest
from backend.services.conversations import ConversationService

router = APIRouter()


@router.get("/conversations")
async def list_conversations(user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    items = await ConversationService(session).list_conversations(user)
    data = [
        {
            "conversationId": item.conversation_id,
            "title": item.title,
            "lastTime": item.last_time,
        }
        for item in items
    ]
    return success(data)


@router.put("/conversations/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    payload: ConversationRenameRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await ConversationService(session).rename(conversation_id, payload.title, user)
    return success()


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await ConversationService(session).delete(conversation_id, user)
    return success()


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    data = await ConversationService(session).list_messages(conversation_id, user)
    return success(data)


@router.post("/conversations/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: str,
    payload: FeedbackRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await ConversationService(session).submit_feedback(message_id, payload.vote, user)
    return success()