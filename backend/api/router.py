from fastapi import APIRouter

from backend.api.routes import (
    auth,
    conversations,
    dashboard,
    ingestion,
    intent_tree,
    knowledge,
    rag,
    sample_questions,
    settings,
    traces,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(conversations.router, tags=["conversations"])
api_router.include_router(knowledge.router, tags=["knowledge"])
api_router.include_router(ingestion.router, tags=["ingestion"])
api_router.include_router(intent_tree.router, tags=["intent-tree"])
api_router.include_router(sample_questions.router, tags=["sample-questions"])
api_router.include_router(traces.router, tags=["rag-traces"])
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(rag.router, tags=["rag"])
