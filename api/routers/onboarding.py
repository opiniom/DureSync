"""사용 안내(말풍선 투어)와 화면별 첫 방문 힌트: '봤어요'를 계정에 저장해 한 번만 보여준다.

웹·설치한 앱·다른 기기가 같은 상태를 보므로, 한 곳에서 보거나 건너뛰면 다른 곳에서는 다시 뜨지 않는다.
· 전체 투어: 본 버전(users.tour_seen). 화면(js/shell/tour.js)의 TOUR_VERSION 을 올리면(내용이 크게 바뀔 때) 모두에게 한 번 더 보여준다.
· 화면별 힌트: 본 화면을 비트로(users.hints_seen) — 워크스페이스 1 · 회의록 2 · 캘린더 4.
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])

HINT_BITS = {"workspace": 1, "notes": 2, "calendar": 4}


class TourIn(BaseModel):
    version: int = Field(..., ge=0, le=1000)


class HintIn(BaseModel):
    key: str = Field(..., max_length=20)


@router.get("")
async def my_onboarding(user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {"tour_seen": user.tour_seen or 0, "hints_seen": user.hints_seen or 0}


@router.post("/tour")
async def tour_done(data: TourIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """투어를 끝까지 봤거나 건너뛴 순간 호출. 더 낮은 버전으로는 되돌리지 않는다."""
    if data.version > (user.tour_seen or 0):
        await db.execute(update(User).where(User.id == user.id).values(tour_seen=data.version))
        await db.commit()
    return {"ok": True, "tour_seen": max(data.version, user.tour_seen or 0)}


@router.post("/hint")
async def hint_done(data: HintIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """그 화면의 첫 방문 힌트를 봤어요(또는 닫았어요)."""
    bit = HINT_BITS.get(data.key)
    if not bit:
        raise HTTPException(400, "알 수 없는 화면이에요.")
    mask = (user.hints_seen or 0) | bit
    if mask != (user.hints_seen or 0):
        await db.execute(update(User).where(User.id == user.id).values(hints_seen=mask))
        await db.commit()
    return {"ok": True, "hints_seen": mask}
