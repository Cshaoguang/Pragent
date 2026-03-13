from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import ConversationSummary, Message
from backend.models.schemas import AuthenticatedUser
from backend.services.ids import new_long_id


class ConversationMemoryService:
    def __init__(self, session: AsyncSession, history_keep_turns: int, summary_start_turns: int) -> None:
        self.session = session
        self.history_keep_turns = history_keep_turns
        self.summary_start_turns = summary_start_turns

    async def get_recent_messages(self, conversation_id: str, current_user: AuthenticatedUser) -> list[Message]:
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.user_id == current_user.user_id,
                Message.deleted == 0,
            )
            .order_by(Message.create_time.desc(), Message.id.desc())
            .limit(self.history_keep_turns * 2)
        )
        items = (await self.session.execute(stmt)).scalars().all()
        return list(reversed(items))

    async def maybe_update_summary(self, conversation_id: str, current_user: AuthenticatedUser) -> None:
        stmt = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.user_id == current_user.user_id,
            Message.deleted == 0,
        )
        messages = (await self.session.execute(stmt)).scalars().all()
        if len(messages) < self.summary_start_turns * 2:
            return
        content = "\n".join(f"{message.role}: {message.content[:200]}" for message in messages[-8:])
        summary_stmt = select(ConversationSummary).where(
            ConversationSummary.conversation_id == conversation_id,
            ConversationSummary.user_id == current_user.user_id,
            ConversationSummary.deleted == 0,
        )
        summary = (await self.session.execute(summary_stmt)).scalar_one_or_none()
        last_message_id = str(messages[-1].id)
        if summary is None:
            summary = ConversationSummary(
                id=new_long_id(),
                conversation_id=conversation_id,
                user_id=current_user.user_id,
                last_message_id=last_message_id,
                content=content,
            )
            self.session.add(summary)
        else:
            summary.last_message_id = last_message_id
            summary.content = content
        await self.session.commit()