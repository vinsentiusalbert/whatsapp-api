#!/bin/sh
set -eu

# cPanel/hosting tertentu memberikan PORT secara otomatis. Jika tidak, pakai 8000.
exec uvicorn whatsapp:app \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --proxy-headers \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"
