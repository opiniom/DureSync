"""요청 속도 제한 (IP 기준): 로그인·가입·초대 참여처럼 계정을 만들거나 비밀을 맞춰 보는 곳을 한꺼번에 두드리는 것을 막는다.

· 메모리에서 센다 — 서버가 다시 켜지면 0 으로 돌아간다 (이 서비스는 서버 한 대라 충분하다).
· 같은 주소(IP)에서 정해진 시간 안에 정해진 횟수를 넘으면 429 + 몇 분 뒤에 다시 하라는 안내.
· 사용자 한 명 한 명의 정상 사용을 막지 않도록 넉넉하게 잡는다(학교·동아리처럼 한 공유기 뒤에 여러 명이 있을 수 있다).
"""
import time
from collections import deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request

from services.client_ip import client_ip

_HITS: Dict[Tuple[str, str], Deque[float]] = {}
_LAST_SWEEP = [0.0]


def _sweep(now: float) -> None:
    """오래 안 쓴 칸을 지워 메모리가 늘지 않게 한다 (10분에 한 번)"""
    if now - _LAST_SWEEP[0] < 600:
        return
    _LAST_SWEEP[0] = now
    for k in [k for k, q in _HITS.items() if not q or now - q[-1] > 7200]:
        _HITS.pop(k, None)


def hit(name: str, ip: str, limit: int, window: float) -> float:
    """한 번 센다. 한도 안이면 0, 넘었으면 다시 해도 되는 때까지 남은 초를 돌려준다"""
    now = time.monotonic(); _sweep(now)
    q = _HITS.setdefault((name, ip or "?"), deque())
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return max(1.0, window - (now - q[0]))
    q.append(now)
    return 0.0


def limiter(name: str, limit: int, window: float, what: str = "요청"):
    """FastAPI 의존성: Depends(limiter('guest', 15, 3600, '초대 참여')) 처럼 쓴다"""
    async def dep(request: Request) -> None:
        wait = hit(name, client_ip(request) or "?", limit, window)
        if wait:
            mins = int(wait // 60) + 1
            raise HTTPException(status_code=429, detail=f"{what}을(를) 너무 자주 했어요. 약 {mins}분 뒤에 다시 해 주세요.", headers={"Retry-After": str(int(wait) + 1)})
    return dep
