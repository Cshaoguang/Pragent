from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import Conversation, Message, RagTraceRun, User


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_overview(self, window: str) -> dict:
        now = datetime.now(timezone.utc)
        since = self._parse_window(window, now)
        total_users = await self.session.scalar(select(func.count()).select_from(User).where(User.deleted == 0)) or 0
        active_users = await self.session.scalar(
            select(func.count(func.distinct(Conversation.user_id))).where(Conversation.last_time >= since, Conversation.deleted == 0)
        ) or 0
        total_sessions = await self.session.scalar(select(func.count()).select_from(Conversation).where(Conversation.deleted == 0)) or 0
        sessions_recent = await self.session.scalar(select(func.count()).select_from(Conversation).where(Conversation.last_time >= since, Conversation.deleted == 0)) or 0
        total_messages = await self.session.scalar(select(func.count()).select_from(Message).where(Message.deleted == 0)) or 0
        messages_recent = await self.session.scalar(select(func.count()).select_from(Message).where(Message.create_time >= since, Message.deleted == 0)) or 0
        return {
            "window": window,
            "compareWindow": window,
            "updatedAt": int(now.timestamp() * 1000),
            "kpis": {
                "totalUsers": {"value": int(total_users)},
                "activeUsers": {"value": int(active_users)},
                "totalSessions": {"value": int(total_sessions)},
                "sessions24h": {"value": int(sessions_recent)},
                "totalMessages": {"value": int(total_messages)},
                "messages24h": {"value": int(messages_recent)},
            },
        }

    async def get_performance(self, window: str) -> dict:
        now = datetime.now(timezone.utc)
        since = self._parse_window(window, now)
        stmt = select(RagTraceRun).where(RagTraceRun.deleted == 0, RagTraceRun.start_time >= since)
        runs = (await self.session.execute(stmt)).scalars().all()
        durations = [run.duration_ms for run in runs if run.duration_ms is not None]
        errors = [run for run in runs if run.status == "ERROR"]
        avg_latency = int(sum(durations) / len(durations)) if durations else 0
        p95_index = max(int(len(durations) * 0.95) - 1, 0) if durations else 0
        p95_latency = sorted(durations)[p95_index] if durations else 0
        success_rate = round((len(runs) - len(errors)) / len(runs), 4) if runs else 1.0
        return {
            "window": window,
            "avgLatencyMs": avg_latency,
            "p95LatencyMs": p95_latency,
            "successRate": success_rate,
            "errorRate": round(1 - success_rate, 4),
            "noDocRate": 0,
            "slowRate": round(sum(1 for item in durations if item > 8000) / len(durations), 4) if durations else 0,
        }

    async def get_trends(self, metric: str, window: str, granularity: str) -> dict:
        now = datetime.now(timezone.utc)
        since = self._parse_window(window, now)
        step = timedelta(hours=1 if granularity == "hour" else 24)
        points = []
        cursor = since
        while cursor <= now:
            points.append({"ts": int(cursor.timestamp() * 1000), "value": 0})
            cursor += step
        return {
            "metric": metric,
            "window": window,
            "granularity": granularity,
            "series": [{"name": metric, "data": points}],
        }

    def _parse_window(self, window: str, now: datetime) -> datetime:
        if window.endswith("h"):
            return now - timedelta(hours=int(window[:-1]))
        if window.endswith("d"):
            return now - timedelta(days=int(window[:-1]))
        return now - timedelta(hours=24)