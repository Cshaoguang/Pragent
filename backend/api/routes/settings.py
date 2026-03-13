from fastapi import APIRouter

from backend.api.responses import success
from backend.services.settings import SettingsService

router = APIRouter()


@router.get("/rag/settings")
async def get_settings():
    return success(SettingsService().get_system_settings())