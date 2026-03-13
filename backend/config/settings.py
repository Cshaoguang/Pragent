from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderSettings(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    chat_model: str | None = None
    embedding_model: str | None = None
    rerank_model: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "pragent-service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 9090
    api_prefix: str = "/api/pragent"
    app_demo_mode: bool = False

    database_url: str
    redis_url: str
    qdrant_url: str
    qdrant_api_key: str | None = None

    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: str = "/tmp/pragent-storage"
    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket: str = "pragent"
    s3_use_ssl: bool = False

    mcp_server_url: str = "http://localhost:9099"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_chat_model: str | None = None
    openai_embedding_model: str | None = None

    deepseek_api_key: str | None = None
    deepseek_base_url: str | None = None
    deepseek_chat_model: str | None = None

    anthropic_api_key: str | None = None
    anthropic_model: str | None = None

    siliconflow_api_key: str | None = None
    siliconflow_base_url: str | None = None
    siliconflow_chat_model: str | None = None
    siliconflow_embedding_model: str | None = None
    siliconflow_rerank_model: str | None = None

    rag_default_collection: str = "rag_default_store"
    rag_embedding_dimension: int = 3072
    rag_metric_type: str = "Cosine"
    rag_history_keep_turns: int = 4
    rag_summary_start_turns: int = 5
    rag_summary_enabled: bool = True
    rag_summary_max_chars: int = 200
    rag_title_max_length: int = 30
    rag_query_rewrite_enabled: bool = True
    rag_query_rewrite_max_history_messages: int = 4
    rag_query_rewrite_max_history_chars: int = 500
    rag_global_rate_limit_enabled: bool = True
    rag_global_max_concurrent: int = 1
    rag_global_max_wait_seconds: int = 3
    rag_global_lease_seconds: int = 30
    rag_global_poll_interval_ms: int = 200
    rag_vector_global_confidence_threshold: float = 0.6
    rag_vector_global_top_k_multiplier: int = 3
    rag_intent_directed_min_intent_score: float = 0.4
    rag_intent_directed_top_k_multiplier: int = 2

    model_failure_threshold: int = 2
    model_open_duration_ms: int = 30000
    stream_message_chunk_size: int = 8

    @property
    def openai_provider(self) -> ProviderSettings:
        return ProviderSettings(
            api_key=self.openai_api_key,
            base_url=self.openai_base_url,
            chat_model=self.openai_chat_model,
            embedding_model=self.openai_embedding_model,
        )

    @property
    def deepseek_provider(self) -> ProviderSettings:
        return ProviderSettings(
            api_key=self.deepseek_api_key,
            base_url=self.deepseek_base_url,
            chat_model=self.deepseek_chat_model,
        )

    @property
    def anthropic_provider(self) -> ProviderSettings:
        return ProviderSettings(api_key=self.anthropic_api_key, chat_model=self.anthropic_model)

    @property
    def siliconflow_provider(self) -> ProviderSettings:
        return ProviderSettings(
            api_key=self.siliconflow_api_key,
            base_url=self.siliconflow_base_url,
            chat_model=self.siliconflow_chat_model,
            embedding_model=self.siliconflow_embedding_model,
            rerank_model=self.siliconflow_rerank_model,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
