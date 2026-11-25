"""기관용 계정 · 기관 (inst_db.py 의 별도 DB 에 저장)"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from inst_db import InstBase


class InstOrg(InstBase):
    """기관(학교 · 학원 · 수업 단위). code 는 학생이 로그인할 때 쓰는 기관 코드"""
    __tablename__ = "inst_orgs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(12), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class InstUser(InstBase):
    """기관용 계정. teacher(교수 · 교사 · 기관 담당자): 구글 로그인 / student: 기관 코드 + 아이디 + 비밀번호(선생님이 등록)"""
    __tablename__ = "inst_users"
    __table_args__ = (UniqueConstraint("org_id", "login_id", name="uq_inst_org_login"),)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role = Column(String(10), nullable=False)                      # 'teacher' | 'student'
    org_id = Column(Integer, ForeignKey("inst_orgs.id"), nullable=True, index=True)   # 선생님은 기관을 만들기 전까지 비어 있다
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)     # 선생님(구글)
    google_sub = Column(String(255), nullable=True)
    login_id = Column(String(40), nullable=True)                   # 학생 아이디 (대학: 학번, 중 · 고: 3-2-15 처럼 선생님이 정한 값)
    hashed_password = Column(String(255), nullable=True)
    must_change_password = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
