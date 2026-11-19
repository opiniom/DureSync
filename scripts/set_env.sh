#!/usr/bin/env bash
# 서버 설정(.env) 한 줄을 안전하게 추가하거나 바꾼다.   서버에서:  bash ~/code-lounge/scripts/set_env.sh 이름 "값" [--restart]
#   예)  bash scripts/set_env.sh OPERATOR_NAME "DureSync 운영팀"
#        bash scripts/set_env.sh PRIVACY_CONTACT_EMAIL "privacy@example.com" --restart
# · 바꾸기 전에 .env 를 .env.bak-날짜 로 복사해 둔다 (잘못 넣었으면 그 파일로 되돌리면 된다)
# · 이미 있는 이름이면 그 줄만 바꾸고, 없으면 맨 아래에 추가한다 (같은 줄이 두 번 생기지 않는다)
# · 아래 허용 목록의 이름만 받는다 — 비밀 값(API 키 등)을 실수로 건드리지 않게
# · 설정은 서버를 다시 시작해야 적용된다: --restart 를 붙이면 app 만 다시 시작한다 (다시 빌드하지 않아서 금방 끝난다)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
ALLOWED="OPERATOR_NAME PRIVACY_CONTACT_EMAIL GOOGLE_SITE_VERIFICATION NAVER_SITE_VERIFICATION PROJECT_MAX_MEMBERS TERMINAL_MAX_CONCURRENT TERMINAL_MAX_PER_USER TERMINAL_MAX_SECONDS GUEST_KEEP_DAYS INQUIRY_KEEP_DAYS ACCESS_LOG_DAYS BACKUP_KEEP"

key="${1:-}"; val="${2-}"; restart="no"; [ "${3:-}" = "--restart" ] && restart="yes"
if [ -z "$key" ] || [ "$#" -lt 2 ]; then
  echo "사용법: bash scripts/set_env.sh 이름 \"값\" [--restart]"; echo "바꿀 수 있는 이름: $ALLOWED"; exit 2
fi
case " $ALLOWED " in *" $key "*) ;; *) echo "'$key' 는 이 스크립트로 바꿀 수 없는 이름이에요. 바꿀 수 있는 이름: $ALLOWED"; exit 2;; esac
case "$val" in *$'\n'*|*$'\r'*) echo "값에는 줄바꿈을 넣을 수 없어요."; exit 2;; esac
[ -f "$ENV_FILE" ] || { echo ".env 파일이 없어요: $ENV_FILE"; exit 1; }

cp "$ENV_FILE" "$ENV_FILE.bak-$(date +%Y%m%d-%H%M%S)"
if grep -q "^${key}=" "$ENV_FILE"; then
  tmp="$(mktemp)"
  awk -v k="$key" -v v="$val" 'BEGIN{FS=OFS="="} $1==k && !done {print k "=" v; done=1; next} {print}' "$ENV_FILE" > "$tmp"
  cat "$tmp" > "$ENV_FILE"; rm -f "$tmp"; echo "바꿨어요:  $key=$val"
else
  [ -n "$(tail -c1 "$ENV_FILE")" ] && echo >> "$ENV_FILE"          # 마지막 줄이 줄바꿈 없이 끝났으면 먼저 줄을 바꾼다
  echo "${key}=${val}" >> "$ENV_FILE"; echo "추가했어요:  $key=$val"
fi
if [ "$restart" = "yes" ]; then
  echo "서버(app)를 다시 시작해요…"; (cd "$ROOT" && docker compose -f docker-compose.prod.yml up -d --force-recreate app)
else
  echo "※ 적용하려면 서버를 다시 시작하세요:  cd ~/code-lounge && docker compose -f docker-compose.prod.yml up -d --force-recreate app"
fi
