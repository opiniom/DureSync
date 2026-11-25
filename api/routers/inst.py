"""기관용(/institution) 로그인 · 기관 · 학생 계정 API.  비즈니스(/api/auth …)와 계정·DB·토큰이 완전히 따로다.

  · 선생님(교수 · 교사 · 기관 담당자): 구글 로그인 → 처음이면 기관을 만들고(기관 코드 발급) 학생을 등록한다
  · 학생: 기관 코드 + 아이디 + 비밀번호로 로그인 (선생님이 등록하면 초기 비밀번호가 만들어지고, 첫 로그인에서 바꾼다)
이 파일과 inst_db.py · inst_models.py · services/inst_auth.py 만 옮기면 기관용을 다른 서버로 분리할 수 있다."""
import logging
import re
import urllib.parse
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from inst_db import get_inst_db
from inst_models import InstOrg, InstUser
from services.inst_auth import (check_pw, check_state_token, create_inst_token, create_state_token, get_inst_user, hash_pw, new_org_code, new_password, require_teacher)
from services.rate_limit import limiter

logger = logging.getLogger("inst")
router = APIRouter(prefix="/api/inst", tags=["Institution"])
LOGIN_ID_RE = re.compile(r"^[0-9A-Za-z가-힣._-]{1,40}$")
MAX_BATCH = 100


class StudentLogin(BaseModel):
    org_code: str = Field(..., max_length=12)
    login_id: str = Field(..., max_length=40)
    password: str = Field(..., max_length=100)


class PasswordChange(BaseModel):
    old_password: str = Field(..., max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


class OrgCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class StudentIn(BaseModel):
    login_id: str = Field(..., max_length=40)
    name: str = Field(..., min_length=1, max_length=30)


class StudentBatch(BaseModel):
    students: List[StudentIn] = Field(..., min_length=1, max_length=MAX_BATCH)


async def _org_of(db: AsyncSession, user: InstUser) -> Optional[InstOrg]:
    return (await db.execute(select(InstOrg).where(InstOrg.id == user.org_id))).scalar_one_or_none() if user.org_id else None


async def _user_json(db: AsyncSession, user: InstUser) -> dict:
    org = await _org_of(db, user)
    return {"id": user.id, "role": user.role, "name": user.name, "email": user.email if user.role == "teacher" else None, "login_id": user.login_id,
            "must_change_password": bool(user.must_change_password),
            "org": ({"id": org.id, "name": org.name, "code": org.code if user.role == "teacher" else None} if org else None)}


async def _issue(db: AsyncSession, user: InstUser) -> dict:
    user.last_login_at = datetime.utcnow(); await db.commit()
    return {"access_token": create_inst_token(user), "token_type": "bearer", "user": await _user_json(db, user)}


def _dev_ok(request: Request) -> bool:
    from routers.auth import _dev_auto_allowed
    return _dev_auto_allowed(request)


@router.get("/config")
async def inst_config(request: Request):
    return {"google_enabled": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET), "dev_auto_login": _dev_ok(request)}


# ---------------- 학생 로그인 ----------------
@router.post("/auth/student-login", dependencies=[Depends(limiter("inst_login", 20, 600, "로그인 시도"))])
async def student_login(body: StudentLogin, db: AsyncSession = Depends(get_inst_db)):
    org = (await db.execute(select(InstOrg).where(InstOrg.code == body.org_code.strip().upper()))).scalar_one_or_none()
    user = None
    if org:
        user = (await db.execute(select(InstUser).where(InstUser.org_id == org.id, InstUser.login_id == body.login_id.strip(), InstUser.role == "student"))).scalar_one_or_none()
    ok = await check_pw(body.password, user.hashed_password if user else None)         # 없는 아이디도 같은 시간이 걸린다
    if not user or not ok or not user.is_active:
        raise HTTPException(401, "기관 코드, 아이디 또는 비밀번호가 맞지 않아요.")
    return await _issue(db, user)


@router.post("/auth/change-password", dependencies=[Depends(limiter("inst_pw", 20, 600, "비밀번호 변경"))])
async def change_password(body: PasswordChange, db: AsyncSession = Depends(get_inst_db), user: InstUser = Depends(get_inst_user)):
    if user.role != "student":
        raise HTTPException(400, "학생 계정만 비밀번호를 바꿀 수 있어요. (선생님은 구글 로그인을 써요)")
    if not await check_pw(body.old_password, user.hashed_password):
        raise HTTPException(400, "지금 비밀번호가 맞지 않아요.")
    if body.new_password == body.old_password:
        raise HTTPException(400, "새 비밀번호는 지금 비밀번호와 달라야 해요.")
    user.hashed_password = await hash_pw(body.new_password); user.must_change_password = False
    await db.commit()
    return {"ok": True}


@router.get("/me")
async def me(db: AsyncSession = Depends(get_inst_db), user: InstUser = Depends(get_inst_user)):
    return await _user_json(db, user)


# ---------------- 선생님 로그인 (구글) ----------------
def _redirect_uri() -> str:
    return f"{settings.PUBLIC_BASE_URL}/api/inst/auth/google/callback"


def _back(qs: str) -> RedirectResponse:
    return RedirectResponse(f"{settings.PUBLIC_BASE_URL}/institution/login?{qs}" if qs.startswith("inst_error") else f"{settings.PUBLIC_BASE_URL}/institution/app?{qs}")


@router.get("/auth/google/login", dependencies=[Depends(limiter("inst_oauth", 60, 600, "로그인"))])
async def google_login():
    if not settings.GOOGLE_CLIENT_ID:
        return _back("inst_error=google_keys_missing")
    params = {"client_id": settings.GOOGLE_CLIENT_ID, "redirect_uri": _redirect_uri(), "response_type": "code", "scope": "openid email profile",
              "access_type": "online", "prompt": "select_account", "state": create_state_token()}
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params))


@router.get("/auth/google/callback", dependencies=[Depends(limiter("inst_oauth_cb", 60, 600, "로그인"))])
async def google_callback(code: Optional[str] = None, error: Optional[str] = None, state: Optional[str] = None, db: AsyncSession = Depends(get_inst_db)):
    from routers.auth import _once
    if error or not code:
        return _back("inst_error=cancelled")
    if not check_state_token(state or ""):
        return _back("inst_error=state")
    return await _once("inst-google", code, lambda: _google_work(code, db))


async def _google_work(code: str, db: AsyncSession):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tr = await client.post("https://oauth2.googleapis.com/token", data={"code": code, "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
                                                                                "redirect_uri": _redirect_uri(), "grant_type": "authorization_code"})
            if tr.status_code != 200:
                logger.warning("inst google token failed: http%s", tr.status_code); return _back("inst_error=token_failed")
            at = tr.json().get("access_token")
            ur = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {at}"}) if at else None
            if not ur or ur.status_code != 200:
                return _back("inst_error=profile_failed")
            info = ur.json()
        email = info.get("email")
        if not email:
            return _back("inst_error=no_email")
        user = (await db.execute(select(InstUser).where(InstUser.email == email))).scalar_one_or_none()
        if not user:
            user = InstUser(role="teacher", name=info.get("name") or email.split("@")[0], email=email, google_sub=info.get("sub"))
            db.add(user); await db.commit(); await db.refresh(user)
        elif not user.is_active:
            return _back("inst_error=inactive")
        user.last_login_at = datetime.utcnow(); await db.commit()
        return _back("itoken=" + create_inst_token(user))
    except Exception:
        logger.exception("inst google login failed")
        return _back("inst_error=failed")


@router.post("/auth/dev-auto")
async def dev_auto(request: Request, db: AsyncSession = Depends(get_inst_db)):
    """임시(로컬) 서버 전용: DEV_AUTO_LOGIN_EMAIL 로 선생님 로그인 (구글을 거치지 않는다)"""
    if not _dev_ok(request) or not settings.DEV_AUTO_LOGIN_EMAIL:
        raise HTTPException(404, "Not Found")
    email = settings.DEV_AUTO_LOGIN_EMAIL
    user = (await db.execute(select(InstUser).where(InstUser.email == email))).scalar_one_or_none()
    if not user:
        user = InstUser(role="teacher", name=email.split("@")[0], email=email); db.add(user); await db.commit(); await db.refresh(user)
    return await _issue(db, user)


# ---------------- 기관 · 학생 등록 (선생님) ----------------
@router.post("/org", dependencies=[Depends(limiter("inst_org", 10, 3600, "기관 만들기"))])
async def create_org(body: OrgCreate, db: AsyncSession = Depends(get_inst_db), user: InstUser = Depends(require_teacher)):
    if user.org_id:
        raise HTTPException(409, "이미 기관이 있어요.")
    for _ in range(8):
        org = InstOrg(name=body.name.strip(), code=new_org_code())
        db.add(org)
        try:
            await db.flush(); break
        except IntegrityError:
            await db.rollback(); user = (await db.execute(select(InstUser).where(InstUser.id == user.id))).scalar_one()
    else:
        raise HTTPException(500, "기관 코드를 만들지 못했어요. 다시 시도해 주세요.")
    user.org_id = org.id; await db.commit()
    return await _issue(db, user)                        # 기관이 생겼으니 새 증표를 준다


def _student_json(u: InstUser) -> dict:
    return {"id": u.id, "login_id": u.login_id, "name": u.name, "must_change_password": bool(u.must_change_password), "is_active": bool(u.is_active),
            "last_login_at": (u.last_login_at.isoformat() + "Z") if u.last_login_at else None}


@router.get("/students")
async def list_students(db: AsyncSession = Depends(get_inst_db), user: InstUser = Depends(require_teacher)):
    if not user.org_id:
        return {"students": []}
    rows = (await db.execute(select(InstUser).where(InstUser.org_id == user.org_id, InstUser.role == "student").order_by(InstUser.login_id))).scalars().all()
    return {"students": [_student_json(u) for u in rows]}


@router.post("/students", dependencies=[Depends(limiter("inst_students", 30, 3600, "학생 등록"))])
async def add_students(body: StudentBatch, db: AsyncSession = Depends(get_inst_db), user: InstUser = Depends(require_teacher)):
    """명단으로 학생 계정을 만든다. 초기 비밀번호는 이 응답에서 한 번만 보여 준다(서버에는 해시만 남는다)"""
    if not user.org_id:
        raise HTTPException(400, "먼저 기관을 만들어 주세요.")
    have = {r[0] for r in (await db.execute(select(InstUser.login_id).where(InstUser.org_id == user.org_id, InstUser.role == "student"))).all()}
    created, skipped, seen = [], [], set()
    for s in body.students:
        lid = s.login_id.strip()
        if not LOGIN_ID_RE.match(lid):
            skipped.append({"login_id": lid, "reason": "아이디는 글자·숫자·. _ - 만 40자까지 쓸 수 있어요"}); continue
        if lid in have or lid in seen:
            skipped.append({"login_id": lid, "reason": "이미 있는 아이디예요"}); continue
        seen.add(lid)
        pw = new_password()
        u = InstUser(role="student", org_id=user.org_id, name=s.name.strip(), login_id=lid, hashed_password=await hash_pw(pw, 10), must_change_password=True)
        db.add(u); created.append((u, pw))
    await db.commit()
    return {"created": [dict(_student_json(u), initial_password=pw) for u, pw in created], "skipped": skipped}


async def _my_student(db: AsyncSession, teacher: InstUser, sid: int) -> InstUser:
    u = (await db.execute(select(InstUser).where(InstUser.id == sid, InstUser.org_id == teacher.org_id, InstUser.role == "student"))).scalar_one_or_none() if teacher.org_id else None
    if not u:
        raise HTTPException(404, "학생을 찾을 수 없어요.")
    return u


@router.post("/students/{sid}/reset-password")
async def reset_password(sid: int, db: AsyncSession = Depends(get_inst_db), user: InstUser = Depends(require_teacher)):
    u = await _my_student(db, user, sid)
    pw = new_password(); u.hashed_password = await hash_pw(pw, 10); u.must_change_password = True
    await db.commit()
    return {"id": u.id, "login_id": u.login_id, "initial_password": pw}


@router.delete("/students/{sid}")
async def delete_student(sid: int, db: AsyncSession = Depends(get_inst_db), user: InstUser = Depends(require_teacher)):
    u = await _my_student(db, user, sid)
    await db.delete(u); await db.commit()
    return {"ok": True}
