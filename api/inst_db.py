"""기관용(/institution) 전용 데이터베이스.

비즈니스 DB(database.py)와 파일·엔진·모델 기반을 완전히 따로 쓴다:
  · 기관용 계정(선생님·학생)과 학생 정보가 비즈니스 데이터와 섞이지 않는다 (백업·보관·삭제를 따로 정할 수 있다)
  · 나중에 기관용만 다른 컨테이너·서버로 옮길 때 이 파일(DB)과 routers/inst.py 만 옮기면 된다
"""
import os
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings


def inst_db_url() -> str:
    if settings.INST_DATABASE_URL:
        return settings.INST_DATABASE_URL
    base = settings.DATABASE_URL
    if base.startswith("sqlite"):
        path = make_url(base).database or ""
        stem, _ = os.path.splitext(path)
        return "sqlite+aiosqlite:///" + (stem + "_inst.db").replace("\\", "/")
    return base          # SQLite 가 아니면(PostgreSQL) 같은 서버의 다른 테이블로 둔다 — 운영에서 따로 지정하려면 INST_DATABASE_URL


INST_URL = inst_db_url()
if INST_URL.startswith("sqlite"):
    _f = make_url(INST_URL).database
    if _f and _f != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(_f)), exist_ok=True)

inst_engine = create_async_engine(INST_URL, echo=False, future=True)
if inst_engine.dialect.name == "sqlite":
    @event.listens_for(inst_engine.sync_engine, "connect")
    def _pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL"); cur.execute("PRAGMA synchronous=NORMAL"); cur.execute("PRAGMA busy_timeout=10000")
        finally:
            cur.close()

inst_session_maker = async_sessionmaker(inst_engine, class_=AsyncSession, expire_on_commit=False)
InstBase = declarative_base()


async def get_inst_db():
    async with inst_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_inst_db():
    import inst_models  # noqa: F401  (모델을 등록한다)
    async with inst_engine.begin() as conn:
        await conn.run_sync(InstBase.metadata.create_all)
