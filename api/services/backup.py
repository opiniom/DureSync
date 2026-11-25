"""DB 자동 백업 (SQLite): 하루에 한 번 안전하게 복사해서 압축해 둔다.

· SQLite 의 '온라인 백업'을 쓰므로 서비스가 돌아가는 중에 복사해도 깨지지 않는다 (파일을 그냥 cp 하면 저장 중인 내용이 섞일 수 있다).
· 저장 위치: DB 파일 옆 backups/app-날짜-시각.db.gz (도커 볼륨 ./data 안이라 컨테이너를 새로 만들어도 남는다)
· BACKUP_KEEP 개(기본 7)만 남기고 오래된 것은 지운다.
· 같은 서버 안의 복사본이라 서버(디스크)가 통째로 사라지는 사고는 막지 못한다 → 가끔 서버 밖(내 컴퓨터·클라우드)으로 내려받아 두는 것이 필요하다.
"""
import asyncio
import glob
import gzip
import logging
import os
import re
import shutil
import sqlite3
import time
from datetime import datetime
from typing import Optional

from sqlalchemy.engine import make_url

from config import settings

logger = logging.getLogger("backup")
INTERVAL_SECONDS = 23 * 3600          # 마지막 백업이 이보다 오래됐으면 새로 만든다


def _db_path() -> Optional[str]:
    if not settings.DATABASE_URL.startswith("sqlite"):
        return None
    p = make_url(settings.DATABASE_URL).database
    return os.path.abspath(p) if p and p != ":memory:" else None


def backup_dir() -> Optional[str]:
    p = _db_path()
    return os.path.join(os.path.dirname(p), "backups") if p else None


def _list() -> list:
    d = backup_dir()
    return sorted(glob.glob(os.path.join(d, "app-*.db.gz"))) if d else []


def latest_age_seconds() -> Optional[float]:
    files = _list()
    return (time.time() - os.path.getmtime(files[-1])) if files else None


NAME_RE = re.compile(r"^app-\d{8}-\d{6}\.db\.gz$")


def list_info() -> list:
    """보관 중인 백업 목록 (최신이 먼저): 이름 · 크기 · 만든 시각"""
    out = []
    for f in reversed(_list()):
        try:
            st = os.stat(f)
            out.append({"name": os.path.basename(f), "size_bytes": st.st_size, "created_at": datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z"})
        except OSError:
            pass
    return out


def safe_path(name: str) -> Optional[str]:
    """내려받기용: 정해진 이름 모양(app-날짜-시각.db.gz)이고 백업 폴더 안에 있는 파일만 허용한다 (../ 같은 경로 조작 방지)"""
    d = backup_dir()
    if not d or not NAME_RE.match(name or ""):
        return None
    p = os.path.realpath(os.path.join(d, name))
    return p if p.startswith(os.path.realpath(d) + os.sep) and os.path.isfile(p) else None


def backup_once() -> Optional[str]:
    """백업 하나를 만든다. 성공하면 파일 경로, SQLite 가 아니거나 실패하면 None (서비스에는 영향 없음)"""
    src = _db_path()
    if not src or not os.path.exists(src):
        return None
    d = backup_dir(); os.makedirs(d, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tmp = os.path.join(d, f".tmp-{stamp}.db"); out = os.path.join(d, f"app-{stamp}.db.gz")
    try:
        s = sqlite3.connect(src, timeout=30); t = sqlite3.connect(tmp)
        try:
            s.backup(t)                                      # 온라인 백업: 저장 중에도 일관된 복사본
        finally:
            t.close(); s.close()
        with open(tmp, "rb") as fi, gzip.open(out + ".part", "wb", compresslevel=6) as fo:
            shutil.copyfileobj(fi, fo)
        os.replace(out + ".part", out)
    except Exception:
        logger.exception("DB 백업 실패")
        for f in (out + ".part",):
            if os.path.exists(f): os.remove(f)
        return None
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    keep = max(1, int(settings.BACKUP_KEEP or 7))
    for old in _list()[:-keep]:                              # 오래된 백업 정리
        try: os.remove(old)
        except OSError: pass
    return out


async def backup_loop() -> None:
    """서버가 켜져 있는 동안 한 시간마다 확인해서, 마지막 백업이 하루 넘게 지났으면 새로 만든다 (배포로 자주 다시 켜져도 하루 한 번 수준을 지킨다)"""
    await asyncio.sleep(90)                                  # 켜진 직후의 몰림이 지나간 뒤에 시작
    while True:
        try:
            age = latest_age_seconds()
            if age is None or age >= INTERVAL_SECONDS:
                path = await asyncio.to_thread(backup_once)
                if path:
                    logger.info("DB 백업 완료: %s (%.1fMB)", os.path.basename(path), os.path.getsize(path) / 1048576)
            from services import inst_backup                     # 기관용 DB(학생 계정)도 같은 주기로
            iage = inst_backup.latest_age_seconds()
            if iage is None or iage >= INTERVAL_SECONDS:
                ipath = await asyncio.to_thread(inst_backup.backup_once)
                if ipath:
                    logger.info("기관용 DB 백업 완료: %s", os.path.basename(ipath))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("백업 반복 실패")
        await asyncio.sleep(3600)
