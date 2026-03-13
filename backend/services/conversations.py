from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import Conversation, Message, MessageFeedback
from backend.models.schemas import AuthenticatedUser
from backend.services.ids import new_long_id


class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_conversations(self, current_user: AuthenticatedUser) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == current_user.user_id, Conversation.deleted == 0)
            .order_by(Conversation.last_time.desc(), Conversation.id.desc())
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def rename(self, conversation_id: str, title: str, current_user: AuthenticatedUser) -> None:
        conversation = await self._get_user_conversation(conversation_id, current_user.user_id)
        conversation.title = title
        await self.session.commit()

    async def delete(self, conversation_id: str, current_user: AuthenticatedUser) -> None:
        conversation = await self._get_user_conversation(conversation_id, current_user.user_id)
        conversation.deleted = 1
        await self.session.commit()

    async def list_messages(self, conversation_id: str, current_user: AuthenticatedUser) -> list[dict]:
        await self._get_user_conversation(conversation_id, current_user.user_id)
        msg_stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.user_id == current_user.user_id,
                Message.deleted == 0,
            )
            .order_by(Message.create_time.asc(), Message.id.asc())
        )
        feedback_stmt = select(MessageFeedback).where(
            MessageFeedback.conversation_id == conversation_id,
            MessageFeedback.user_id == current_user.user_id,
            MessageFeedback.deleted == 0,
        )
        messages = (await self.session.execute(msg_stmt)).scalars().all()
        feedback_map = {
            item.message_id: item.vote for item in (await self.session.execute(feedback_stmt)).scalars().all()
        }
        return [
            {
                "id": str(message.id),
                "conversationId": message.conversation_id,
                "role": message.role,
                "content": message.content,
                "vote": feedback_map.get(message.id),
                "createTime": message.create_time,
            }
            for message in messages
        ]

    async def submit_feedback(self, message_id: str, vote: int, current_user: AuthenticatedUser) -> None:
        message = await self.session.get(Message, int(message_id))
        if message is None or message.deleted != 0 or message.user_id != current_user.user_id:
            raise ValueError("消息不存在")
        stmt = select(MessageFeedback).where(
            MessageFeedback.message_id == int(message_id),
            MessageFeedback.user_id == current_user.user_id,
            MessageFeedback.deleted == 0,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            existing = MessageFeedback(
                id=new_long_id(),
                message_id=int(message_id),
                conversation_id=message.conversation_id,
                user_id=current_user.user_id,
                vote=vote,
            )
            self.session.add(existing)
        else:
            existing.vote = vote
            existing.update_time = datetime.utcnow()
        await self.session.commit()

    async def ensure_conversation(self, conversation_id: str | None, current_user: AuthenticatedUser, title: str) -> Conversation:
        if conversation_id:
            return await self._get_user_conversation(conversation_id, current_user.user_id)
        new_conversation_id = f"conv_{new_long_id()}"
        conversation = Conversation(
            id=new_long_id(),
            conversation_id=new_conversation_id,
            user_id=current_user.user_id,
            title=title,
            last_time=datetime.utcnow(),
        )
        self.session.add(conversation)
        await self.session.commit()
        return conversation

    async def create_message(self, conversation_id: str, current_user: AuthenticatedUser, role: str, content: str) -> Message:
        message = Message(
            id=new_long_id(),
            conversation_id=conversation_id,
            user_id=current_user.user_id,
            role=role,
            content=content,
        )
        self.session.add(message)
        stmt = select(Conversation).where(Conversation.conversation_id == conversation_id, Conversation.deleted == 0)
        conversation = (await self.session.execute(stmt)).scalar_one()
        conversation.last_time = datetime.utcnow()
        await self.session.commit()
        return message

    async def _get_user_conversation(self, conversation_id: str, user_id: str) -> Conversation:
        stmt = select(Conversation).where(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.deleted == 0,
        )
        conversation = (await self.session.execute(stmt)).scalar_one_or_none()
        if conversation is None:
            raise ValueError("会话不存在")
        return conversation
