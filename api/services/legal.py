"""이용약관 · 개인정보처리방침 페이지 (서버가 직접 그리는 독립 HTML — 로그인 없이, 검색엔진도 읽을 수 있다).

서비스가 실제로 하는 일(코드에 구현된 보관 기간·수집 항목)에 맞춰 적었다. 운영 방식이 바뀌면 이 파일의 글과 EFFECTIVE 날짜를 함께 고친다.
운영 주체 이름·개인정보 문의 이메일은 환경 변수(OPERATOR_NAME · PRIVACY_CONTACT_EMAIL)로 정한다.
"""
import html as _h
from typing import List, Tuple

from config import settings

EFFECTIVE = "2026년 11월 19일"
SITE = "DureSync(두레싱크)"


def _contact() -> str:
    mail = (settings.PRIVACY_CONTACT_EMAIL or "").strip()
    base = "서비스 안의 <b>아바타 메뉴 &gt; 문의하기</b>로 남겨 주세요."
    return base + (f" 이메일: <a href=\"mailto:{_h.escape(mail)}\">{_h.escape(mail)}</a>" if mail else "")


def privacy_sections() -> List[Tuple[str, str]]:
    op = _h.escape(settings.OPERATOR_NAME)
    return [
        ("1. 수집하는 개인정보", f"""
<p>{op}(이하 “운영자”)은 {SITE} 서비스 제공에 필요한 최소한의 정보만 수집해요.</p>
<ul>
<li><b>가입·로그인할 때</b>: 구글 또는 네이버 계정에서 제공받는 <b>이름(또는 별명), 이메일 주소, 소셜 계정 식별번호</b>. 비밀번호는 받지 않아요(소셜 로그인 사용).</li>
<li><b>초대 링크로 참여할 때</b>: 팀에서 쓸 이름(별명). 이메일 없이 임시 계정이 만들어져요.</li>
<li><b>서비스를 쓰면서 직접 입력·생성하는 내용</b>: 프로젝트와 팀원 정보, 코드·파일, 채팅, 회의록, 일정, 커뮤니티 글·댓글, 프로필(한 줄 소개·기술 스택·링크 등), 1:1 문의 내용.</li>
<li><b>자동으로 생성되는 정보</b>: 접속 기록(접속 시각·IP 주소·종류), 코드 실행 기록(실행한 코드와 결과), 서비스 이용 환경(브라우저·화면 크기 — 문의를 남길 때 함께 전달).</li>
</ul>"""),
        ("2. 이용 목적", """
<ul>
<li>회원 식별과 로그인, 팀 프로젝트·채팅·회의록·일정 등 서비스 제공</li>
<li>코드 실행, AI 기능(에러 설명, 일정 감지, 채팅 AI, 음성 입력)의 제공</li>
<li>문의 응대와 서비스 개선, 공지 전달</li>
<li>부정 이용 방지와 서비스 안정 운영(접속 기록 확인, 이용 제한)</li>
</ul>"""),
        ("3. 보유 기간과 파기", """
<p>개인정보는 이용 목적을 이루면 지체 없이 파기해요. 서비스에서 정해 둔 보관 기간은 다음과 같아요.</p>
<ul>
<li><b>계정·활동 내용</b>: 탈퇴할 때까지. 탈퇴하면 이름·이메일 등 개인정보와 작성한 글·실행 기록 등을 삭제해요(식별할 수 없는 빈 계정 번호만 남아요).</li>
<li><b>탈퇴 처리 기록</b>: 7일 (문의 대응·부정 이용 확인 용도) 후 자동 삭제</li>
<li><b>접속 기록(IP 주소 등)</b>: 90일 후 자동 삭제</li>
<li><b>삭제한 프로젝트(휴지통)</b>: 14일 후 영구 삭제</li>
<li><b>완료된 1:1 문의</b>: 완료 후 90일이 지나면 자동 삭제</li>
<li>법령에서 보관을 요구하는 경우에는 그 기간 동안 보관해요.</li>
</ul>
<p>전자적 파일은 복구할 수 없는 방법으로 삭제하며, 서비스 장애에 대비한 백업 복사본은 최근 7일치만 보관하고 이후 순차적으로 덮어써서 지워져요.</p>"""),
        ("4. 제3자 제공과 처리 위탁", """
<p>운영자는 이용자의 개인정보를 동의 없이 제3자에게 제공하지 않아요. 다만 서비스 제공을 위해 다음 업체의 시설·기능을 이용해요.</p>
<ul>
<li><b>서버 호스팅</b>: Amazon Web Services(AWS) — 서비스 데이터가 저장되는 서버를 운영해요.</li>
<li><b>소셜 로그인</b>: Google, NAVER — 로그인 인증과 이름·이메일 제공에만 쓰여요.</li>
<li><b>AI 기능</b>: Google(Gemini) — AI 에러 설명, 일정 감지, 채팅 AI, 음성 입력을 쓰면 <b>그 기능에 필요한 내용(코드·채팅·회의록·음성 변환에 필요한 내용)이 처리를 위해 전송</b>될 수 있어요. 개인정보나 비밀번호 같은 민감한 내용은 AI 기능에 입력하지 않는 것을 권해요.</li>
</ul>"""),
        ("5. 이용자의 권리", f"""
<ul>
<li>이용자는 언제든지 자신의 정보를 확인하고 <b>프로필에서 수정</b>할 수 있어요.</li>
<li><b>마이페이지의 ‘계정 탈퇴’</b>로 계정과 활동 데이터를 삭제할 수 있어요. 탈퇴 전에 무엇이 어떻게 되는지 화면에서 미리 확인할 수 있어요.</li>
<li>개인정보의 열람·정정·삭제·처리 정지를 요청하려면 {_contact()}</li>
<li>만 14세 미만 아동은 보호자의 동의 없이 가입할 수 없어요.</li>
</ul>"""),
        ("6. 쿠키와 브라우저 저장소", """
<p>로그인 상태를 유지하고 화면 설정(테마·홈 위젯·단축키 등)을 기억하기 위해 <b>브라우저 저장소(localStorage)</b>를 사용해요. 광고·추적용 쿠키는 사용하지 않아요. 브라우저 설정에서 저장된 데이터를 지우면 로그인 상태와 화면 설정이 초기화돼요.</p>"""),
        ("7. 안전성 확보 조치", """
<ul>
<li>서비스와 브라우저 사이의 통신은 HTTPS로 암호화해요.</li>
<li>관리자 기능은 지정된 계정과 별도 확인 코드를 거쳐야 쓸 수 있고, 관리자의 조치는 감사 기록으로 남겨요.</li>
<li>사용자가 실행한 코드는 서버에서 시간·출력량·동시 실행 수를 제한해 다른 이용자에게 영향이 없게 해요.</li>
<li>서비스 데이터는 하루 한 번 자동으로 백업해요.</li>
</ul>"""),
        ("8. 개인정보 보호 문의", f"""
<p>개인정보 처리에 관한 문의·불만·피해 구제는 {_contact()} 개인정보 침해 신고나 상담은 개인정보침해신고센터(privacy.kisa.or.kr, 118)에서도 받을 수 있어요.</p>"""),
        ("9. 방침의 변경", f"""
<p>이 방침의 내용이 바뀌면 시행 7일 전부터 서비스 안의 공지사항으로 알려요(이용자에게 불리한 변경은 30일 전). 이 방침은 <b>{EFFECTIVE}</b>부터 적용돼요.</p>"""),
    ]


def terms_sections() -> List[Tuple[str, str]]:
    op = _h.escape(settings.OPERATOR_NAME)
    mx = int(settings.PROJECT_MAX_MEMBERS or 6)
    return [
        ("제1조 (목적)", f"<p>이 약관은 {op}(이하 “운영자”)이 제공하는 {SITE} 서비스(이하 “서비스”)의 이용 조건과 운영자·이용자의 권리와 의무를 정해요.</p>"),
        ("제2조 (서비스의 내용)", """
<p>서비스는 브라우저에서 코드를 쓰고 실행하며 팀 채팅·통화·회의록·일정·커뮤니티 등으로 함께 일할 수 있게 해 주는 협업 도구예요. 현재는 <b>무료 베타(Free &amp; Beta)</b>로 제공돼요.</p>"""),
        ("제3조 (계정)", """
<ol>
<li>이용자는 구글 또는 네이버 계정으로 로그인해 이용할 수 있어요. 초대 링크로 이름만 정해 참여하는 임시 이용도 가능해요.</li>
<li>계정은 본인만 사용해야 하며, 타인의 계정을 도용하거나 자신의 계정을 다른 사람이 쓰게 해서는 안 돼요.</li>
<li>만 14세 미만은 보호자의 동의 없이 이용할 수 없어요.</li>
</ol>"""),
        ("제4조 (이용자의 의무와 금지 행위)", """
<p>이용자는 다음 행위를 해서는 안 돼요.</p>
<ul>
<li>법령 또는 타인의 권리를 침해하는 행위, 불법·유해 콘텐츠의 게시</li>
<li>서비스의 코드 실행 기능으로 서버나 다른 이용자를 공격·방해하는 행위(악성 코드, 과도한 자원 사용, 외부 시스템 공격, 채굴 등)</li>
<li>서비스의 보안 장치나 이용 한도를 우회하는 행위, 자동화된 수단으로 과도하게 접속하는 행위</li>
<li>스팸·광고성 글, 다른 이용자를 괴롭히거나 사칭하는 행위</li>
</ul>
<p>위반하면 운영자는 해당 콘텐츠를 숨기거나 삭제하고, 계정을 정지하거나 이용을 제한할 수 있어요.</p>"""),
        ("제5조 (이용 한도)", f"""
<p>안정적인 운영을 위해 다음과 같은 한도를 둘 수 있고, 한도는 서비스 상황에 따라 바뀔 수 있어요.</p>
<ul>
<li>코드 실행: 한 번에 실행할 수 있는 시간·출력량, 동시에 실행할 수 있는 수</li>
<li>프로젝트 인원: 한 프로젝트는 팀장을 포함해 최대 {mx}명</li>
<li>글·문의·AI 기능 등의 하루(또는 시간당) 사용 횟수</li>
</ul>"""),
        ("제6조 (콘텐츠의 권리)", """
<ol>
<li>이용자가 서비스에 올린 코드·글 등 콘텐츠의 권리는 이용자에게 있어요.</li>
<li>운영자는 서비스를 제공·운영하는 데 필요한 범위 안에서만 콘텐츠를 저장·표시·처리해요(예: 팀원에게 보여주기, 백업).</li>
<li>커뮤니티에 올린 글은 다른 이용자에게 공개되니, 개인정보나 비밀 정보를 올리지 않도록 주의해 주세요.</li>
</ol>"""),
        ("제7조 (서비스의 변경과 중단)", """
<p>베타 기간 동안 서비스의 기능·한도·요금 정책은 바뀔 수 있어요. 점검·장애·불가피한 사유로 서비스가 일시 중단될 수 있고, 중요한 변경은 공지사항으로 미리 알려요. 유료 요금제를 도입하게 되면 사전에 따로 안내하고 동의를 받아요.</p>"""),
        ("제8조 (책임의 제한)", """
<ol>
<li>베타 서비스는 있는 그대로 제공돼요. 운영자는 서비스를 안정적으로 운영하려고 노력하며 데이터를 정기적으로 백업하지만, 장애 등으로 인한 데이터 손실이 생길 수 있으니 <b>중요한 코드는 별도로 보관</b>해 주세요.</li>
<li>이용자가 올린 콘텐츠와 이용자 사이의 분쟁은 이용자 본인에게 책임이 있어요. 다만 운영자는 신고된 콘텐츠를 확인해 조치할 수 있어요.</li>
<li>운영자의 고의 또는 중대한 과실이 없는 한 서비스 이용으로 생긴 간접 손해에 대해서는 책임지지 않아요.</li>
</ol>"""),
        ("제9조 (탈퇴와 이용 제한)", """
<p>이용자는 마이페이지의 ‘계정 탈퇴’로 언제든 탈퇴할 수 있고, 탈퇴하면 개인정보와 활동 데이터가 삭제돼요(자세한 내용은 개인정보처리방침). 운영자는 제4조를 위반한 이용자의 계정을 정지하거나 이용을 제한할 수 있어요.</p>"""),
        ("제10조 (약관의 변경과 문의)", f"""
<p>약관이 바뀌면 시행 7일 전부터 공지사항으로 알려요(이용자에게 불리한 변경은 30일 전). 변경된 약관을 알린 뒤에도 계속 이용하면 동의한 것으로 봐요. 문의는 {_contact()} 이 약관은 <b>{EFFECTIVE}</b>부터 적용되고, 대한민국 법령을 따라요.</p>"""),
    ]


_CSS = """
:root{--bg:#fff;--fg:#14161f;--mut:#555b6e;--line:#e3e6ee;--acc:#4f6df5;--card:#f6f7fb}
@media (prefers-color-scheme:dark){:root{--bg:#0e1017;--fg:#eceef6;--mut:#a3a9bd;--line:#262a38;--acc:#8ea2ff;--card:#161925}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.8 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;word-break:keep-all;overflow-wrap:break-word}
a{color:var(--acc)}
header{border-bottom:1px solid var(--line)}
.bar{max-width:820px;margin:0 auto;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.bar b{font-size:19px;letter-spacing:-.04em;color:var(--fg);text-decoration:none}
.bar nav{display:flex;gap:16px;font-size:14px}.bar nav a{color:var(--mut);text-decoration:none}.bar nav a[aria-current]{color:var(--fg);font-weight:700}
main{max-width:820px;margin:0 auto;padding:34px 20px 70px}
h1{font-size:clamp(26px,5vw,34px);letter-spacing:-.05em;margin:0 0 6px;line-height:1.3}
.eff{color:var(--mut);font-size:14px;margin:0 0 30px}
section{margin:0 0 26px;padding:22px 22px 8px;background:var(--card);border:1px solid var(--line);border-radius:18px}
h2{font-size:18px;letter-spacing:-.03em;margin:0 0 8px}
p,li{color:var(--mut);font-size:15.5px}li{margin:4px 0}ul,ol{padding-left:22px;margin:8px 0 14px}b{color:var(--fg)}
footer{max-width:820px;margin:0 auto;padding:0 20px 50px;color:var(--mut);font-size:13.5px}
"""


def render_page(kind: str) -> str:
    """kind: 'terms' | 'privacy' → 완성된 HTML 문서"""
    terms = kind == "terms"
    title = "이용약관" if terms else "개인정보 처리방침"
    secs = terms_sections() if terms else privacy_sections()
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    desc = (f"{SITE} 이용약관 — 서비스 이용 조건과 이용자·운영자의 권리와 의무" if terms else f"{SITE} 개인정보 처리방침 — 수집 항목, 이용 목적, 보유 기간, 이용자의 권리")
    body = "".join(f"<section><h2>{_h.escape(t)}</h2>{c}</section>" for t, c in secs)
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · DureSync</title>
<meta name="description" content="{_h.escape(desc)}">
<link rel="canonical" href="{base}/{'terms' if terms else 'privacy'}">
<meta name="robots" content="index,follow">
<meta property="og:type" content="website"><meta property="og:site_name" content="DureSync"><meta property="og:title" content="{title} · DureSync"><meta property="og:description" content="{_h.escape(desc)}"><meta property="og:url" content="{base}/{'terms' if terms else 'privacy'}">
<link rel="icon" type="image/png" href="/static/icons/favicon-light-64.png">
<style>{_CSS}</style></head><body>
<header><div class="bar"><a href="/"><b>DureSync</b></a><nav><a href="/terms"{' aria-current="page"' if terms else ''}>이용약관</a><a href="/privacy"{'' if terms else ' aria-current="page"'}>개인정보 처리방침</a><a href="/business">서비스 소개</a></nav></div></header>
<main><h1>{title}</h1><p class="eff">시행일: {EFFECTIVE}</p>{body}</main>
<footer>© DureSync · <a href="/">메인 홈</a> · <a href="/business">비즈니스</a> · <a href="/institution">기관용</a></footer>
</body></html>"""
