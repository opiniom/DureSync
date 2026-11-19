"""프로젝트 인원 한도: 팀장 포함 PROJECT_MAX_MEMBERS 명(기본 6명)까지.

베타(무료) 기간에 한 프로젝트가 한없이 커지지 않게 막는다. 팀원이 늘어나는 모든 길(이메일 초대 · 초대 링크 · 게스트 참여 · 모집 지원 수락)이
같은 함수를 쓰므로 어느 길로 와도 한도가 똑같이 적용된다. 이미 한도를 넘은 예전 프로젝트의 팀원은 내보내지 않고, 더 늘어나지만 않게 한다.
"""
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import ProjectMember


def max_members() -> int:
    return max(2, int(settings.PROJECT_MAX_MEMBERS or 6))


async def member_total(db: AsyncSession, project) -> int:
    """지금 인원(팀장 포함)"""
    n = (await db.execute(select(func.count(func.distinct(ProjectMember.user_id))).where(
        ProjectMember.project_id == project.id, ProjectMember.user_id != project.owner_id))).scalar() or 0
    return 1 + int(n)


async def room_left(db: AsyncSession, project) -> int:
    return max(0, max_members() - await member_total(db, project))


def full_message() -> str:
    return f"이 프로젝트는 팀장 포함 최대 {max_members()}명까지 함께할 수 있어요. 지금은 자리가 다 찼어요."


async def ensure_room(db: AsyncSession, project) -> None:
    """자리가 없으면 안내와 함께 400 을 낸다"""
    if await room_left(db, project) <= 0:
        raise HTTPException(status_code=400, detail=full_message())
