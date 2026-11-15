"""공지사항: 운영자가 올린 서비스 전체 안내를 사용자가 한곳에서 본다.

알림(/api/notifications)과는 따로다 — 알림은 '내 일정·초대·소식', 공지사항은 '서비스 전체 안내'.
· 목록은 최신 30개, 내가 아직 안 본 것은 new 로 표시한다.
· '여기까지 확인했어요'는 서버에 번호 하나(users.announce_seen)만 저장해서 웹·설치한 앱·다른 기기가 같은 상태를 본다.
"""
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Announcement, User
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])


def _iso(d) -> str:
    return d.replace(tzinfo=timezone.utc).isoformat() if isinstance(d, datetime) and d.tzinfo is None else (d.isoformat() if d else "")


async def _newest(db: AsyncSession) -> int:
    return (await db.execute(select(func.coalesce(func.max(Announcement.id), 0)))).scalar() or 0


@router.get("")
async def list_announcements(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    rows = (await db.execute(select(Announcement).order_by(Announcement.id.desc()).limit(30))).scalars().all()
    seen = user.announce_seen or 0
    items = []
    for a in rows:
        # 내가 가입하기 전에 올라온 공지는 '새 공지'로 세지 않는다
        is_new = a.id > seen and (user.created_at is None or a.created_at is None or a.created_at >= user.created_at)
        items.append({"id": a.id, "title": a.title, "message": a.message, "link": a.link, "created_at": _iso(a.created_at), "new": bool(is_new)})
    return {"items": items, "unseen": sum(1 for x in items if x["new"])}


@router.post("/seen")
async def mark_seen(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """공지사항을 열어 봤어요 → 지금까지의 공지를 모두 확인한 것으로 한다."""
    newest = await _newest(db)
    if newest > (user.announce_seen or 0):
        await db.execute(update(User).where(User.id == user.id).values(announce_seen=newest))
        await db.commit()
    return {"ok": True, "seen": newest}
