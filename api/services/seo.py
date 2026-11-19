"""검색엔진·공유 미리보기 준비 (SEO).

이 서비스의 화면은 브라우저에서 JS 로 그려서, 검색 로봇 중에는 내용이 비어 있다고 보는 곳이 있다(특히 네이버).
그래서 소개 화면(/ · /business · /institution)은 서버가 HTML 에 직접
  · 제목(title) · 설명(description) · 대표 주소(canonical) · 공유 미리보기(Open Graph · Twitter) · 구조화 데이터(JSON-LD)
  · 화면 밖에 둔 요약 글(JS 가 없어도 읽히는 소개 문장)
을 넣어 준다. 로그인이 필요한 화면(/app …)은 검색에 나오지 않게(noindex) 한다.
robots.txt · sitemap.xml 도 여기서 만든다.
"""
import html as _h
import json
import re
from typing import Dict, Optional

from config import settings

SITE = "DureSync"

PAGES: Dict[str, Dict[str, str]] = {
    "/": {
        "title": "DureSync(두레싱크) — 함께 코딩하고 일하는 AI 협업 워크스페이스",
        "desc": "설치 없이 브라우저에서 코드를 쓰고 실행하고, 팀 채팅·통화·회의록·일정까지 한곳에서. 코딩 입문자부터 팀 프로젝트까지, 지금은 무료 베타예요.",
        "h1": "DureSync(두레싱크) — 함께 코딩하고 일하는 AI 협업 워크스페이스",
        "body": (
            "<p>두레는 마을 사람들이 힘을 모아 함께 일하던 우리의 오래된 협동 방식이에요. DureSync는 그 마음을 코딩 공간에 옮겨 왔어요. 설치 없이 브라우저에서 코드를 쓰고 실행하고, 팀으로 함께 만들 수 있어요.</p>"
            "<ul><li>비즈니스: 코딩 입문자, 개인 개발자, 팀 프로젝트, 창업·공모전 준비까지 — 무료 베타(Free &amp; Beta)로 모든 기능을 써 볼 수 있어요.</li>"
            "<li>기관용: 학교·교수용으로 개발 중이에요. 수업 속 팀 프로젝트를 한눈에 살피고 공정하게 이끌 수 있도록 준비하고 있어요.</li>"
            "<li>기능: 코드 워크스페이스(여러 언어 실행), 디버거와 AI 에러 설명, 팀 채팅과 두레 AI, 팀 통화방, 회의록에서 자동으로 일정 찾기, 커뮤니티와 팀원 모집, 공모전·해커톤 모아 보기.</li></ul>"),
    },
    "/business": {
        "title": "DureSync 비즈니스 — 코딩 입문자부터 팀 프로젝트까지 · 무료 베타",
        "desc": "처음 시작하는 사람에게는 쉽게, 함께 만드는 팀에게는 자연스럽게. 코드 작성·실행, 디버거와 AI 에러 설명, 팀 채팅·통화, 자동 일정을 한곳에서. 지금은 Free & Beta.",
        "h1": "처음 시작하는 사람에게는 쉽게, 함께 만드는 팀에게는 자연스럽게",
        "body": (
            "<p>DureSync 비즈니스는 코딩을 이제 막 시작한 사람부터 팀 프로젝트를 이끄는 사람까지 쓰는 협업 워크스페이스예요. 설치 없이 브라우저에서 코드를 쓰고, 실행하고, 함께 만들어요.</p>"
            "<ul><li>코드 워크스페이스: 파이썬·자바·자바스크립트·C 등 여러 언어를 브라우저에서 바로 실행해요.</li>"
            "<li>디버거 + AI 에러 설명: 줄 번호 옆을 눌러 중단점을 걸고 한 줄씩 실행하며, 에러는 AI가 쉬운 말로 알려 줘요.</li>"
            "<li>팀 채팅·두레 AI, 팀 통화방, 회의록에서 날짜가 든 일정을 AI가 찾아 캘린더에 넣어 줘요.</li>"
            "<li>커뮤니티: 막힌 과제 질문, 팀원 구하기, 스터디 모집, 공모전·해커톤 정보.</li>"
            "<li>대상: 코딩 입문자, 개인 개발자, 전공 무관 학생, 창업·상업 프로젝트, 선생님, 교육 목적(스터디·동아리·수업 팀).</li></ul>"
            "<p>구글 또는 네이버 계정으로 바로 시작할 수 있어요. 지금은 무료 베타(Free &amp; Beta)로, 결제 정보가 필요 없어요.</p>"),
    },
    "/institution": {
        "title": "DureSync 기관용(개발 중) — 수업 속 팀 프로젝트를 한눈에 살피고 공정하게",
        "desc": "학교·교수용 기관용을 준비하고 있어요. 팀별 진행 현황, 계정 일괄 관리, 과제 스프레드시트와 AI 기본 채점, 인원별 파일 권한, 팀장과의 1:1 톡방을 소개해요.",
        "h1": "수업 속 팀 프로젝트를 한눈에 살피고, 공정하게 이끌어요",
        "body": (
            "<p>DureSync 기관용은 초·중·고·대학 어디서든 수업 속 팀 프로젝트를 이끄는 교수·교사·기관 담당자와 학생을 위한 협업 공간이에요. 현재 개발 중이며, 소개하는 기능은 개발 과정에서 바뀔 수 있어요.</p>"
            "<ul><li>팀별 진행 현황을 한눈에 살펴요.</li><li>계정을 일괄로 관리해요.</li>"
            "<li>과제 스프레드시트: AI가 기본 채점을 해 주면 평가자가 수정해서 확정해요.</li>"
            "<li>인원별 파일 자동 생성과 파일 권한: 교수·교사는 모든 권한, 학생은 내 파일 중심으로 써요.</li>"
            "<li>팀 채팅과 팀장과의 1:1 톡방.</li><li>학생 프로필과 학교 마크가 붙는 커뮤니티.</li></ul>"),
    },
}

_BODY_RE = re.compile(r"(<body[^>]*>)", re.I)
_TITLE_RE = re.compile(r"<title>[^<]*</title>", re.I)


def base_url() -> str:
    return settings.PUBLIC_BASE_URL.rstrip("/")


def norm(path: str) -> str:
    p = "/" + (path or "").strip("/")
    return "/" if p in ("/", "/ui") else p


def _jsonld(page: Dict[str, str], url: str) -> str:
    data = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "alternateName": "두레싱크", "url": base_url() + "/", "inLanguage": "ko"},
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": SITE, "applicationCategory": "DeveloperApplication", "operatingSystem": "Web", "url": url,
         "description": page["desc"], "inLanguage": "ko", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "KRW"}},
    ]
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def decorate(html: str, path: str) -> str:
    """index.html 에 검색·공유용 정보를 넣는다. 소개 화면이 아니면(로그인 필요한 /app …) noindex"""
    p = norm(path)
    page: Optional[Dict[str, str]] = PAGES.get(p)
    if page is None:
        return _TITLE_RE.sub("<title>DureSync</title>\n<meta name=\"robots\" content=\"noindex,nofollow\">", html, count=1)
    url = base_url() + ("" if p == "/" else p) + ("/" if p == "/" else "")
    e = _h.escape
    img = base_url() + "/static/icons/icon-light-512.png"
    head = (f"<title>{e(page['title'])}</title>\n"
            f"<meta name=\"description\" content=\"{e(page['desc'])}\">\n"
            f"<link rel=\"canonical\" href=\"{url}\">\n<meta name=\"robots\" content=\"index,follow\">\n"
            f"<meta property=\"og:type\" content=\"website\"><meta property=\"og:site_name\" content=\"{SITE}\"><meta property=\"og:locale\" content=\"ko_KR\">\n"
            f"<meta property=\"og:title\" content=\"{e(page['title'])}\"><meta property=\"og:description\" content=\"{e(page['desc'])}\"><meta property=\"og:url\" content=\"{url}\"><meta property=\"og:image\" content=\"{img}\">\n"
            f"<meta name=\"twitter:card\" content=\"summary\"><meta name=\"twitter:title\" content=\"{e(page['title'])}\"><meta name=\"twitter:description\" content=\"{e(page['desc'])}\"><meta name=\"twitter:image\" content=\"{img}\">\n"
            + _jsonld(page, url))
    if p == "/":                                            # 검색 등록 때 소유권을 확인하는 태그 (환경 설정에 값이 있을 때만)
        for name, val in (("google-site-verification", settings.GOOGLE_SITE_VERIFICATION), ("naver-site-verification", settings.NAVER_SITE_VERIFICATION)):
            if (val or "").strip():
                head += f"\n<meta name=\"{name}\" content=\"{e((val or '').strip())}\">"
    out = _TITLE_RE.sub(lambda m: head, html, count=1)
    fb = (f"<div class=\"seo-fb\" aria-hidden=\"true\" style=\"position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden\"><h1>{e(page['h1'])}</h1>{page['body']}"
          f"<p><a href=\"/\">메인 홈</a> · <a href=\"/business\">비즈니스</a> · <a href=\"/institution\">기관용</a> · <a href=\"/terms\">이용약관</a> · <a href=\"/privacy\">개인정보 처리방침</a></p></div>")
    return _BODY_RE.sub(lambda m: m.group(1) + fb, out, count=1)


def robots_txt() -> str:
    return ("User-agent: *\nAllow: /\nDisallow: /app\nDisallow: /api/\nDisallow: /ws/\nDisallow: /runner/\n"
            f"Sitemap: {base_url()}/sitemap.xml\n")


def sitemap_xml() -> str:
    urls = [("/", "1.0"), ("/business", "0.9"), ("/institution", "0.6"), ("/terms", "0.3"), ("/privacy", "0.3")]
    items = "".join(f"<url><loc>{base_url()}{'/' if u == '/' else u}</loc><priority>{pr}</priority></url>" for u, pr in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>\n'
