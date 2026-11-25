"""기관용 DB(학생 계정 포함) 백업 — services/backup.py 와 같은 방식(하루 한 번 · 온라인 백업 · 압축 · BACKUP_KEEP 개 보관).
저장 위치는 기관용 DB 파일 옆 backups/inst-날짜-시각.db.gz  (비즈니스 백업 app-*.db.gz 와 따로 센다)"""
import glob
import gzip
import logging
import os
import shutil
import sqlite3
import time
from datetime import datetime
from typing import Optional

from sqlalchemy.engine import make_url

from config import settings
import inst_db

logger = logging.getLogger("backup")


def _src() -> Optional[str]:
    if not inst_db.INST_URL.startswith("sqlite"):
        return None
    p = make_url(inst_db.INST_URL).database
    return os.path.abspath(p) if p and p != ":memory:" else None


def _dir() -> Optional[str]:
    s = _src()
    return os.path.join(os.path.dirname(s), "backups") if s else None


def _list() -> list:
    d = _dir()
    return sorted(glob.glob(os.path.join(d, "inst-*.db.gz"))) if d else []


def latest_age_seconds() -> Optional[float]:
    f = _list()
    return (time.time() - os.path.getmtime(f[-1])) if f else None


def backup_once() -> Optional[str]:
    src = _src()
    if not src or not os.path.exists(src):
        return None
    d = _dir(); os.makedirs(d, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tmp = os.path.join(d, f".tmp-inst-{stamp}.db"); out = os.path.join(d, f"inst-{stamp}.db.gz")
    try:
        s = sqlite3.connect(src, timeout=30); t = sqlite3.connect(tmp)
        try:
            s.backup(t)
        finally:
            t.close(); s.close()
        with open(tmp, "rb") as fi, gzip.open(out + ".part", "wb", compresslevel=6) as fo:
            shutil.copyfileobj(fi, fo)
        os.replace(out + ".part", out)
    except Exception:
        logger.exception("기관용 DB 백업 실패")
        if os.path.exists(out + ".part"): os.remove(out + ".part")
        return None
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    for old in _list()[:-max(1, int(settings.BACKUP_KEEP or 7))]:
        try: os.remove(old)
        except OSError: pass
    return out
