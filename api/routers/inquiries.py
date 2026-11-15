"""1:1 문의: 사용자가 관리자에게 직접 남기는 문의 (앱 안에서 바로 접수).

· 문의를 남기면 관리자 페이지 '문의' 탭에 실시간으로 올라온다. 어느 화면에서 남겼는지·웹/앱·화면 크기는 자동으로 붙는다.
· 관리자가 답하면 내 알림으로 온다. 같은 문의 안에서 이어서 대화할 수 있다.
· 남용 방지: 하루 5건까지, 한 문의에 글은 60개까지.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Inquiry, InquiryMessage, User
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/inquiries", tags=["Inquiries"])

CATEGORIES = {"bug": "오류 · 불편", "idea": "건의 · 아이디어", "account": "계정", "etc": "기타"}
STATUS_LABEL = {"open": "접수", "progress": "처리 중", "done": "완료"}
DAILY_LIMIT = 5
MAX_MESSAGES = 60


def iso(d) -> Optional[str]:
    if not d:
        return None
    return (d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d).isoformat()


class InquiryIn(BaseModel):
    category: str = Field(default="etc", max_length=12)
    title: str = Field(..., min_length=1, max_length=120)
    message: str = Field(..., min_length=1, max_length=2000)
    page: Optional[str] = Field(default=None, max_length=60)
    client: Optional[str] = Field(default=None, max_length=200)


class InquiryMsgIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


def _row(q: Inquiry) -> Dict[str, Any]:
    unread = q.last_by == "admin" and (q.user_seen_at is None or q.user_seen_at < q.updated_at)
    return {"id": q.id, "category": q.category, "category_label": CATEGORIES.get(q.category, "기타"), "title": q.title, "status": q.status, "status_label": STATUS_LABEL.get(q.status, q.status),
            "last_by": q.last_by, "unread": bool(unread), "created_at": iso(q.created_at), "updated_at": iso(q.updated_at)}


async def _thread(db: AsyncSession, qid: int):
    rows = (await db.execute(select(InquiryMessage).where(InquiryMessage.inquiry_id == qid).order_by(InquiryMessage.id))).scalars().all()
    return [{"id": m.id, "sender": m.sender, "text": m.text, "created_at": iso(m.created_at)} for m in rows]


async def _mine(db: AsyncSession, user: User, qid: int) -> Inquiry:
    q = (await db.execute(select(Inquiry).where(Inquiry.id == qid, Inquiry.user_id == user.id))).scalar_one_or_none()
    if not q:
        raise HTTPException(404, "문의를 찾을 수 없어요.")
    return q


@router.get("")
async def my_inquiries(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    rows = (await db.execute(select(Inquiry).where(Inquiry.user_id == user.id).order_by(Inquiry.updated_at.desc()).limit(50))).scalars().all()
    items = [_row(q) for q in rows]
    return {"items": items, "unread": sum(1 for x in items if x["unread"])}


@router.post("")
async def create_inquiry(data: InquiryIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    title = data.title.strip(); message = data.message.strip()
    if not title or not message:
        raise HTTPException(400, "제목과 내용을 입력해 주세요.")
    cat = data.category if data.category in CATEGORIES else "etc"
    since = datetime.utcnow() - timedelta(days=1)
    n = (await db.execute(select(func.count()).select_from(Inquiry).where(Inquiry.user_id == user.id, Inquiry.created_at >= since))).scalar() or 0
    if n >= DAILY_LIMIT:
        raise HTTPException(429, f"문의는 하루에 {DAILY_LIMIT}건까지 남길 수 있어요. 이미 남긴 문의에 이어서 적어 주세요.")
    q = Inquiry(user_id=user.id, category=cat, title=title, status="open", page=(data.page or "").strip()[:60] or None, client=(data.client or "").strip()[:200] or None, last_by="user",
                user_seen_at=datetime.utcnow())
    db.add(q)
    await db.flush()
    db.add(InquiryMessage(inquiry_id=q.id, sender="user", sender_id=user.id, text=message))
    await db.commit()
    return {"ok": True, "id": q.id}


@router.get("/{qid}")
async def inquiry_detail(qid: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    q = await _mine(db, user, qid)
    q.user_seen_at = datetime.utcnow() + timedelta(seconds=1)            # 열어 본 순간 '새 답변' 표시를 끈다
    await db.commit()
    return {**_row(q), "messages": await _thread(db, qid)}


@router.post("/{qid}/messages")
async def add_message(qid: int, data: InquiryMsgIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    q = await _mine(db, user, qid)
    text = data.text.strip()
    if not text:
        raise HTTPException(400, "내용을 입력해 주세요.")
    cnt = (await db.execute(select(func.count()).select_from(InquiryMessage).where(InquiryMessage.inquiry_id == qid))).scalar() or 0
    if cnt >= MAX_MESSAGES:
        raise HTTPException(400, "한 문의에 남길 수 있는 글 수를 넘었어요. 새 문의로 이어서 남겨 주세요.")
    db.add(InquiryMessage(inquiry_id=qid, sender="user", sender_id=user.id, text=text))
    q.last_by = "user"; q.updated_at = datetime.utcnow(); q.user_seen_at = q.updated_at + timedelta(seconds=1)
    if q.status == "done":                                                 # 완료된 문의에 다시 쓰면 접수 상태로 돌아간다
        q.status = "open"
    await db.commit()
    return {"ok": True}
