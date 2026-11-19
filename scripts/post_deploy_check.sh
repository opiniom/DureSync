#!/usr/bin/env bash
# 배포 뒤 점검: 서버가 정상으로 올라왔는지 한 번에 확인한다 (서버에서: bash ~/code-lounge/scripts/post_deploy_check.sh)
#   사용법: post_deploy_check.sh [주소]    (기본값 https://duresync.cloud)
BASE="${1:-https://duresync.cloud}"
ok=0; bad=0
check() {   # 이름 · 주소 · 기대 상태코드
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$BASE$2")
  if [ "$code" = "$3" ]; then echo "  OK    $1 ($2) → $code"; ok=$((ok+1)); else echo "  이상  $1 ($2) → $code (기대 $3)"; bad=$((bad+1)); fi
}
echo "== 배포 점검: $BASE"
check "서버 상태"            /health 200
check "메인 홈"              /  200
check "비즈니스"             /business 200
check "기관용"               /institution 200
check "로그인 화면(앱)"      /app/login 200
check "이용약관"             /terms 200
check "개인정보 처리방침"    /privacy 200
check "robots.txt"           /robots.txt 200
check "sitemap.xml"          /sitemap.xml 200
check "화면 묶음(JS)"        "/static/bundle.js?v=check" 200
check "로그인 필요한 API(문의)"   /api/inquiries 401      # 401 이면 새 버전이 떠 있는 것 (404 면 이전 버전)
check "로그인 필요한 API(공지)"   /api/announcements 401
echo "== 메모리 · 디스크"
free -m | awk 'NR==1 || NR==2'
df -h / | awk 'NR==1 || NR==2'
echo "== 최근 DB 백업"
ls -1t "$(dirname "$0")/../data/backups" 2>/dev/null | head -3 || true
echo
if [ "$bad" -eq 0 ]; then echo "결과: 모두 정상 ($ok/$((ok+bad)))"; else echo "결과: 이상 $bad 건 — 위 '이상' 줄을 확인하세요 (docker compose -f docker-compose.prod.yml logs app --tail 50)"; exit 1; fi
