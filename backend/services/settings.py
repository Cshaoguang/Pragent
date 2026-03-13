from backend.config.settings import get_settings


class SettingsService:
    def get_system_settings(self) -> dict:
        settings = get_settings()
        return {
            "rag": {
                "default": {
                    "collectionName": settings.rag_default_collection,
                    "dimension": settings.rag_embedding_dimension,
                    "metricType": settings.rag_metric_type,
                },
                "queryRewrite": {
                    "enabled": settings.rag_query_rewrite_enabled,
                    "maxHistoryMessages": settings.rag_query_rewrite_max_history_messages,
                    "maxHistoryChars": settings.rag_query_rewrite_max_history_chars,
                },
                "rateLimit": {
                    "global": {
                        "enabled": settings.rag_global_rate_limit_enabled,
                        "maxConcurrent": settings.rag_global_max_concurrent,
                        "maxWaitSeconds": settings.rag_global_max_wait_seconds,
                        "leaseSeconds": settings.rag_global_lease_seconds,
                        "pollIntervalMs": settings.rag_global_poll_interval_ms,
                    }
                },
                "memory": {
                    "historyKeepTurns": settings.rag_history_keep_turns,
                    "summaryStartTurns": settings.rag_summary_start_turns,
                    "summaryEnabled": settings.rag_summary_enabled,
                    "ttlMinutes": 60,
                    "summaryMaxChars": settings.rag_summary_max_chars,
                    "titleMaxLength": settings.rag_title_max_length,
                },
            },
            "ai": {
                "providers": {
                    "openai": {
                        "url": settings.openai_base_url,
                        "apiKey": settings.openai_api_key,
                        "endpoints": {"chat": "/chat/completions", "embedding": "/embeddings"},
                    },
                    "deepseek": {
                        "url": settings.deepseek_base_url,
                        "apiKey": settings.deepseek_api_key,
                        "endpoints": {"chat": "/chat/completions"},
                    },
                    "anthropic": {
                        "url": "https://api.anthropic.com",
                        "apiKey": settings.anthropic_api_key,
                        "endpoints": {"chat": "/v1/messages"},
                    },
                    "siliconflow": {
                        "url": settings.siliconflow_base_url,
                        "apiKey": settings.siliconflow_api_key,
                        "endpoints": {
                            "chat": "/chat/completions",
                            "embedding": "/embeddings",
                            "rerank": "/rerank",
                        },
                    },
                },
                "selection": {
                    "failureThreshold": settings.model_failure_threshold,
                    "openDurationMs": settings.model_open_duration_ms,
                },
                "stream": {"messageChunkSize": settings.stream_message_chunk_size},
                "chat": {
                    "defaultModel": settings.openai_chat_model or settings.deepseek_chat_model,
                    "deepThinkingModel": settings.anthropic_model or settings.openai_chat_model,
                    "candidates": [
                        {
                            "id": "openai",
                            "provider": "openai",
                            "model": settings.openai_chat_model,
                            "priority": 1,
                            "supportsThinking": False,
                        },
                        {
                            "id": "deepseek",
                            "provider": "deepseek",
                            "model": settings.deepseek_chat_model,
                            "priority": 2,
                            "supportsThinking": True,
                        },
                        {
                            "id": "anthropic",
                            "provider": "anthropic",
                            "model": settings.anthropic_model,
                            "priority": 3,
                            "supportsThinking": True,
                        },
                        {
                            "id": "siliconflow",
                            "provider": "siliconflow",
                            "model": settings.siliconflow_chat_model,
                            "priority": 4,
                            "supportsThinking": True,
                        },
                    ],
                },
                "embedding": {
                    "defaultModel": settings.openai_embedding_model or settings.siliconflow_embedding_model,
                    "candidates": [
                        {
                            "id": "openai-embedding",
                            "provider": "openai",
                            "model": settings.openai_embedding_model,
                            "dimension": settings.rag_embedding_dimension,
                            "priority": 1,
                        },
                        {
                            "id": "siliconflow-embedding",
                            "provider": "siliconflow",
                            "model": settings.siliconflow_embedding_model,
                            "dimension": settings.rag_embedding_dimension,
                            "priority": 2,
                        },
                    ],
                },
                "rerank": {
                    "defaultModel": settings.siliconflow_rerank_model,
                    "candidates": [
                        {
                            "id": "siliconflow-rerank",
                            "provider": "siliconflow",
                            "model": settings.siliconflow_rerank_model,
                            "priority": 1,
                        }
                    ],
                },
            },
        }
