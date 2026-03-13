from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.model_router import ModelRouter
from backend.rag.retrieval import RetrievalEngine, RetrievedChunk


class AgentState(TypedDict, total=False):
    question: str
    deep_thinking: bool
    rewritten_question: str
    intent: dict[str, Any]
    retrieved_chunks: list[RetrievedChunk]
    context: str
    answer: str


class AgentWorkflow:
    def __init__(self, session: AsyncSession, model_router: ModelRouter) -> None:
        self.session = session
        self.model_router = model_router
        self.retrieval_engine = RetrievalEngine(session, model_router)
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("intent_detection", self.intent_detection_node)
        graph.add_node("rewrite", self.rewrite_node)
        graph.add_node("retriever", self.retriever_node)
        graph.add_node("rerank", self.rerank_node)
        graph.add_node("context_builder", self.context_builder_node)
        graph.add_node("llm", self.llm_node)
        graph.add_node("memory_update", self.memory_update_node)
        graph.set_entry_point("intent_detection")
        graph.add_edge("intent_detection", "rewrite")
        graph.add_conditional_edges(
            "rewrite",
            self._route_after_rewrite,
            {
                "retriever": "retriever",
                "llm": "llm",
            },
        )
        graph.add_edge("retriever", "rerank")
        graph.add_edge("rerank", "context_builder")
        graph.add_edge("context_builder", "llm")
        graph.add_edge("llm", "memory_update")
        graph.add_edge("memory_update", END)
        return graph.compile()

    async def run(self, question: str, deep_thinking: bool = False) -> AgentState:
        return await self.graph.ainvoke({"question": question, "deep_thinking": deep_thinking})

    async def intent_detection_node(self, state: AgentState) -> AgentState:
        return {**state, "intent": await self.retrieval_engine.detect_intent(state["question"])}

    async def rewrite_node(self, state: AgentState) -> AgentState:
        rewritten = await self.retrieval_engine.rewrite_question(state["question"])
        return {**state, "rewritten_question": rewritten}

    async def retriever_node(self, state: AgentState) -> AgentState:
        chunks = await self.retrieval_engine.retrieve(state["rewritten_question"], state["intent"], top_k=6)
        return {**state, "retrieved_chunks": chunks}

    async def rerank_node(self, state: AgentState) -> AgentState:
        chunks = sorted(state.get("retrieved_chunks", []), key=lambda item: item.score, reverse=True)
        return {**state, "retrieved_chunks": chunks[:5]}

    async def context_builder_node(self, state: AgentState) -> AgentState:
        chunks = state.get("retrieved_chunks", [])
        context = "\n\n".join(
            f"[Chunk {index + 1}] {chunk.content}" for index, chunk in enumerate(chunks)
        )
        return {**state, "context": context}

    async def llm_node(self, state: AgentState) -> AgentState:
        system_prompt = (
            "你是企业知识助手。优先基于上下文回答；如果上下文不足，要明确说明不确定，不要编造。"
        )
        user_prompt = state["rewritten_question"]
        context = state.get("context", "")
        if context:
            user_prompt = f"已检索到的知识上下文：\n{context}\n\n用户问题：{state['rewritten_question']}"
        answer = await self.model_router.chat(
            system_prompt,
            [{"role": "user", "content": user_prompt}],
            deep_thinking=state.get("deep_thinking", False),
        )
        return {**state, "answer": answer}

    async def memory_update_node(self, state: AgentState) -> AgentState:
        return state

    def _route_after_rewrite(self, state: AgentState) -> str:
        if not state.get("rewritten_question"):
            return "llm"
        return "retriever"