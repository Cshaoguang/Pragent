from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from backend.config.settings import Settings, get_settings


@dataclass(slots=True)
class ChatCandidate:
    provider: str
    model: str
    base_url: str | None
    api_key: str | None
    supports_thinking: bool = False


class ModelRouter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get_chat_candidates(self, deep_thinking: bool) -> list[ChatCandidate]:
        candidates = [
            ChatCandidate(
                provider="openai",
                model=self.settings.openai_chat_model or "",
                base_url=self.settings.openai_base_url,
                api_key=self.settings.openai_api_key,
                supports_thinking=False,
            ),
            ChatCandidate(
                provider="deepseek",
                model=self.settings.deepseek_chat_model or "",
                base_url=self.settings.deepseek_base_url,
                api_key=self.settings.deepseek_api_key,
                supports_thinking=True,
            ),
            ChatCandidate(
                provider="anthropic",
                model=self.settings.anthropic_model or "",
                base_url="https://api.anthropic.com",
                api_key=self.settings.anthropic_api_key,
                supports_thinking=True,
            ),
            ChatCandidate(
                provider="siliconflow",
                model=self.settings.siliconflow_chat_model or "",
                base_url=self.settings.siliconflow_base_url,
                api_key=self.settings.siliconflow_api_key,
                supports_thinking=True,
            ),
        ]
        available = [candidate for candidate in candidates if candidate.model and candidate.api_key]
        if deep_thinking:
            thinking = [candidate for candidate in available if candidate.supports_thinking]
            if thinking:
                return thinking
        return available

    async def chat(self, system_prompt: str, messages: list[dict[str, str]], deep_thinking: bool = False) -> str:
        candidates = self.get_chat_candidates(deep_thinking)
        last_error: Exception | None = None
        for candidate in candidates:
            try:
                if candidate.provider == "anthropic":
                    return await self._chat_anthropic(candidate, system_prompt, messages)
                return await self._chat_openai_like(candidate, system_prompt, messages)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        if last_error is not None:
            raise RuntimeError(f"模型调用失败: {last_error}") from last_error
        raise RuntimeError("未配置可用的聊天模型")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        provider = None
        if self.settings.openai_api_key and self.settings.openai_embedding_model:
            provider = (
                "openai",
                self.settings.openai_base_url,
                self.settings.openai_api_key,
                self.settings.openai_embedding_model,
            )
        elif self.settings.siliconflow_api_key and self.settings.siliconflow_embedding_model:
            provider = (
                "siliconflow",
                self.settings.siliconflow_base_url,
                self.settings.siliconflow_api_key,
                self.settings.siliconflow_embedding_model,
            )
        if provider is None:
            raise RuntimeError("未配置可用的向量模型")
        _, base_url, api_key, model = provider
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"model": model, "input": texts}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{base_url.rstrip('/')}/embeddings", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json().get("data", [])
            return [item.get("embedding", []) for item in data]

    async def _chat_openai_like(
        self,
        candidate: ChatCandidate,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> str:
        headers = {"Authorization": f"Bearer {candidate.api_key}"}
        request_messages = [{"role": "system", "content": system_prompt}, *messages]
        payload: dict[str, Any] = {
            "model": candidate.model,
            "messages": request_messages,
            "temperature": 0.2,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{candidate.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        choice = body.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            return "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
        return content

    async def _chat_anthropic(
        self,
        candidate: ChatCandidate,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> str:
        headers = {
            "x-api-key": candidate.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": candidate.model,
            "system": system_prompt,
            "max_tokens": 2048,
            "messages": messages,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        content = body.get("content", [])
        return "\n".join(item.get("text", "") for item in content if item.get("type") == "text")