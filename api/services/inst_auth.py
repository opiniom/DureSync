"""기관용 로그인 증표(토큰) · 로그인 확인 · 코드/비밀번호 만들기.

기관용 토큰에는 typ='inst' 가 들어 있어서, 비즈니스 쪽(auth_service.decode_access_token)은 이 토큰을 받아들이지 않는다.
(사용자 번호가 우연히 같아도 기관용 계정이 비즈니스 계정으로 오인되지 않는다. 반대로 비즈니스 토큰도 기관용에서는 쓸 수 없다.)
"""
import asyncio
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from inst_db import get_inst_db
from inst_models import InstUser

security = HTTPBearer(auto_error=False)
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"            # 헷갈리는 글자(O/0, I/1)는 뺀다
PW_CHARS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_org_code() -> str:
    return "".join(secrets.choice(CODE_CHARS) for _ in range(6))


def new_password() -> str:
    return "".join(secrets.choice(PW_CHARS) for _ in range(8))


def _hash(pw: str, rounds: int) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


async def hash_pw(pw: str, rounds: int = 12) -> str:
    return await asyncio.to_thread(_hash, pw, rounds)             # bcrypt 는 느려서 다른 요청을 멈추지 않게 따로 돌린다


async def check_pw(pw: str, hashed: Optional[str]) -> bool:
    def _c():
        try:
            return bcrypt.checkpw(pw.encode("utf-8"), (hashed or _DUMMY).encode("utf-8")) and bool(hashed)
        except Exception:
            return False
    return await asyncio.to_thread(_c)


_DUMMY = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt(rounds=12)).decode("utf-8")      # 없는 아이디도 같은 시간이 걸리게(아이디 존재 여부 추측 방지)


def create_inst_token(user: InstUser) -> str:
    now = datetime.utcnow()
    payload = {"typ": "inst", "sub": str(user.id), "role": user.role, "org": user.org_id, "iat": now, "exp": now + timedelta(days=settings.INST_TOKEN_DAYS)}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_state_token() -> str:
    """구글 로그인 왕복 중 위조 방지용(10분)"""
    return jwt.encode({"typ": "inst_state", "n": secrets.token_hex(8), "exp": datetime.utcnow() + timedelta(minutes=10)}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def check_state_token(tok: str) -> bool:
    try:
        return jwt.decode(tok or "", settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]).get("typ") == "inst_state"
    except jwt.PyJWTError:
        return False


def decode_inst_token(token: str) -> Optional[dict]:
    try:
        p = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    return p if p.get("typ") == "inst" else None


async def get_inst_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db: AsyncSession = Depends(get_inst_db)) -> InstUser:
    if not credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "기관용 로그인이 필요해요.", headers={"WWW-Authenticate": "Bearer"})
    p = decode_inst_token(credentials.credentials)
    if not p or not str(p.get("sub", "")).isdigit():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "기관용 로그인이 만료됐거나 올바르지 않아요.", headers={"WWW-Authenticate": "Bearer"})
    user = (await db.execute(select(InstUser).where(InstUser.id == int(p["sub"])))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "사용할 수 없는 계정이에요.", headers={"WWW-Authenticate": "Bearer"})
    return user


async def require_teacher(user: InstUser = Depends(get_inst_user)) -> InstUser:
    if user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "선생님만 할 수 있어요.")
    return user
