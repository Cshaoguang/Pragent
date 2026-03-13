from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.workflow import AgentWorkflow
from backend.config.redis import get_redis
from backend.config.settings import get_settings
from backend.memory.service import ConversationMemoryService
from backend.models.schemas import AuthenticatedUser
from backend.rag.model_router import ModelRouter
from backend.services.conversations import ConversationService
from backend.services.traces import TraceService
from backend.services.ids import new_long_id


class RagChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.model_router = ModelRouter(self.settings)

    async def stop_task(self, task_id: str) -> None:
        await get_redis().setex(f"rag:cancel:{task_id}", 600, "1")

    async def stream_chat(
        self,
        question: str,
        conversation_id: str | None,
        deep_thinking: bool,
        current_user: AuthenticatedUser,
    ) -> AsyncIterator[tuple[str, object]]:
        task_id = f"task_{new_long_id()}"
        conversation_service = ConversationService(self.session)
        memory_service = ConversationMemoryService(
            self.session,
            history_keep_turns=self.settings.rag_history_keep_turns,
            summary_start_turns=self.settings.rag_summary_start_turns,
        )
        conversation = await conversation_service.ensure_conversation(
            conversation_id,
            current_user,
            title=question[: self.settings.rag_title_max_length],
        )
        await conversation_service.create_message(conversation.conversation_id, current_user, "user", question)
        trace_service = TraceService(self.session)
        trace = await trace_service.start_run(
            trace_name="rag-chat",
            entry_method="RagChatService.stream_chat",
            conversation_id=conversation.conversation_id,
            task_id=task_id,
            user_id=current_user.user_id,
        )
        yield "meta", {"conversationId": conversation.conversation_id, "taskId": task_id}
        workflow = AgentWorkflow(self.session, self.model_router)
        try:
            await trace_service.create_node(trace.trace_id, "intent", "IntentDetectionNode", "IntentDetectionNode")
            state = await workflow.run(question=question, deep_thinking=deep_thinking)
            await trace_service.finish_node(trace.trace_id, "intent")
            answer = state.get("answer", "")
            thought = "正在综合检索结果生成回答" if deep_thinking else ""
            if thought:
                yield "message", {"type": "think", "delta": thought}
            assembled = []
            chunk_size = max(self.settings.stream_message_chunk_size, 1)
            for index in range(0, len(answer), chunk_size):
                if await self._is_cancelled(task_id):
                    yield "cancel", {"messageId": None, "title": conversation.title}
                    await trace_service.finish_run(trace.trace_id, "ERROR", "任务已取消")
                    return
                delta = answer[index : index + chunk_size]
                assembled.append(delta)
                yield "message", {"type": "response", "delta": delta}
                await asyncio.sleep(0.01)
            assistant = await conversation_service.create_message(
                conversation.conversation_id,
                current_user,
                "assistant",
                "".join(assembled),
            )
            await memory_service.maybe_update_summary(conversation.conversation_id, current_user)
            yield "title", {"title": conversation.title}
            yield "finish", {"messageId": str(assistant.id), "title": conversation.title}
            yield "done", {"status": "ok"}
            await trace_service.finish_run(trace.trace_id, "SUCCESS")
        except Exception as exc:  # noqa: BLE001
            await trace_service.finish_run(trace.trace_id, "ERROR", str(exc))
            yield "error", {"error": str(exc)}

    async def _is_cancelled(self, task_id: str) -> bool:
        value = await get_redis().get(f"rag:cancel:{task_id}")
        return value == "1"