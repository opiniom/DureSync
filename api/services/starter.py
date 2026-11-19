"""새로 가입한 사용자에게 '시작하기' 예제 프로젝트를 하나 만들어 준다.

가입하고 처음 들어오면 프로젝트도 파일도 없어서 무엇부터 해야 할지 막막하다. 바로 ▶ 실행을 눌러 볼 수 있는 파일이 하나 있으면
첫 실행까지 걸리는 시간이 줄어든다. 가입 직후 한 번만 만들고, 실패해도 로그인에는 영향을 주지 않는다. 지우고 싶으면 일반 프로젝트처럼 지우면 된다.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from models import Project, ProjectFile, User

logger = logging.getLogger("starter")

STARTER_TITLE = "시작하기 · 예제 프로젝트"
STARTER_CODE = '''# 두레에 오신 걸 환영해요!
# 처음 오신 분을 위한 예제 파일이에요. 아래 순서대로 해 보세요.
#
#  1) 위쪽의 [실행] 버튼을 눌러 보세요. 결과는 아래 '실행 콘솔'에 나와요.
#  2) 코드를 바꿔서 다시 실행해 보세요. (예: name 을 내 이름으로)
#  3) 에러가 나면 AI가 어디가 왜 틀렸는지 쉬운 말로 알려 줘요.
#     채팅에서 "두레야"라고 불러 보세요.

name = "두레"
print(f"안녕하세요, {name}님!")

# 1부터 5까지 더하기
total = 0
for n in range(1, 6):
    total += n
print("1부터 5까지의 합:", total)

# 에러도 한번 만나 보세요: 아래 줄 맨 앞의 # 을 지우고 실행해 보면 에러가 나요.
# print(result)
'''


async def create_starter_project(db: AsyncSession, user: User) -> None:
    """예제 프로젝트(+ main.py)를 만든다. 실패하면 조용히 넘어간다."""
    try:
        project = Project(owner_id=user.id, title=STARTER_TITLE)
        db.add(project)
        await db.flush()
        db.add(ProjectFile(project_id=project.id, path="main.py", content=STARTER_CODE, updated_by=user.id))
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("예제 프로젝트를 만들지 못했어요 (user %s)", getattr(user, "id", "?"))
