from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_admin_user, get_db_session
from backend.api.responses import success
from backend.models.schemas import BatchIdsRequest, IntentNodePayload, IntentNodeUpdatePayload
from backend.services.intent_tree import IntentTreeService

router = APIRouter()


@router.get("/intent-tree/trees")
async def list_trees(_: object = Depends(get_admin_user), session: AsyncSession = Depends(get_db_session)):
    return success(await IntentTreeService(session).list_tree())


@router.post("/intent-tree")
async def create_intent(
    payload: IntentNodePayload,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    item_id = await IntentTreeService(session).create(payload, user.username)
    return success(item_id)


@router.put("/intent-tree/{node_id}")
async def update_intent(
    node_id: str,
    payload: IntentNodeUpdatePayload,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await IntentTreeService(session).update(node_id, payload, user.username)
    return success()


@router.delete("/intent-tree/{node_id}")
async def delete_intent(
    node_id: str,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await IntentTreeService(session).delete(node_id)
    return success()


@router.post("/intent-tree/batch/enable")
async def batch_enable(
    payload: BatchIdsRequest,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await IntentTreeService(session).batch_update_enabled(payload, 1)
    return success()


@router.post("/intent-tree/batch/disable")
async def batch_disable(
    payload: BatchIdsRequest,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await IntentTreeService(session).batch_update_enabled(payload, 0)
    return success()


@router.post("/intent-tree/batch/delete")
async def batch_delete(
    payload: BatchIdsRequest,
    _: object = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    await IntentTreeService(session).batch_delete(payload)
    return success()