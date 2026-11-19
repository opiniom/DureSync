#!/usr/bin/env bash
# 서버 디스크 정리: 배포(빌드)할 때마다 쌓이는 이전 이미지와 빌드 캐시를 지운다 (서버에서: bash ~/code-lounge/scripts/cleanup_docker.sh)
# · 지금 돌아가는 컨테이너·이미지, 설치한 언어(langs), 데이터(data)는 지우지 않는다.
# · 지우고 나면 다음 빌드가 처음부터라 한 번은 평소보다 오래 걸린다(캐시를 다시 만든다).
echo "== 정리 전"; df -h / | awk 'NR==1 || NR==2'; docker system df
docker image prune -f              # 이름 없는(이전 빌드) 이미지
docker builder prune -f            # 빌드 캐시
echo "== 정리 후"; df -h / | awk 'NR==1 || NR==2'; docker system df
