from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.entities import SampleQuestion
from backend.models.schemas import SampleQuestionPayload
from backend.services.common import paginate
from backend.services.ids import new_long_id


DEFAULT_SAMPLE_QUESTIONS: list[dict[str, str]] = [
    {
        "title": "内容总结",
        "description": "提炼 3-5 条关键信息与行动点",
        "question": "请帮我总结以下内容，并列出3-5条要点：",
    },
    {
        "title": "任务拆解",
        "description": "把目标拆成可执行步骤与优先级",
        "question": "请把下面需求拆解为步骤，并给出优先级和里程碑：",
    },
    {
        "title": "灵感扩展",
        "description": "给出多个方案并比较优缺点",
        "question": "围绕以下主题给出5-8个方案，并注明优缺点：",
    },
]


class SampleQuestionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def ensure_defaults(self) -> None:
        stmt = select(SampleQuestion.id).where(SampleQuestion.deleted == 0).limit(1)
        exists = (await self.session.execute(stmt)).scalar_one_or_none()
        if exists is not None:
            return

        for item in DEFAULT_SAMPLE_QUESTIONS:
            self.session.add(
                SampleQuestion(
                    id=new_long_id(),
                    title=item["title"],
                    description=item["description"],
                    question=item["question"],
                )
            )
        await self.session.commit()

    async def list_public(self) -> list[SampleQuestion]:
        await self.ensure_defaults()
        stmt = select(SampleQuestion).where(SampleQuestion.deleted == 0).order_by(SampleQuestion.id.desc())
        return (await self.session.execute(stmt)).scalars().all()

    async def list_page(self, current: int, size: int, keyword: str | None):
        await self.ensure_defaults()
        stmt = select(SampleQuestion).where(SampleQuestion.deleted == 0)
        if keyword:
            stmt = stmt.where(
                or_(
                    SampleQuestion.title.like(f"%{keyword}%"),
                    SampleQuestion.question.like(f"%{keyword}%"),
                )
            )
        stmt = stmt.order_by(SampleQuestion.id.desc())
        return await paginate(self.session, stmt, current, size)

    async def create(self, payload: SampleQuestionPayload) -> str:
        item = SampleQuestion(
            id=new_long_id(),
            title=payload.title,
            description=payload.description,
            question=payload.question or "",
        )
        self.session.add(item)
        await self.session.commit()
        return str(item.id)

    async def update(self, item_id: str, payload: SampleQuestionPayload) -> None:
        item = await self.session.get(SampleQuestion, int(item_id))
        if item is None or item.deleted != 0:
            raise ValueError("示例问题不存在")
        if payload.title is not None:
            item.title = payload.title
        if payload.description is not None:
            item.description = payload.description
        if payload.question is not None:
            item.question = payload.question
        await self.session.commit()

    async def delete(self, item_id: str) -> None:
        item = await self.session.get(SampleQuestion, int(item_id))
        if item is None:
            return
        item.deleted = 1
        await self.session.commit()
