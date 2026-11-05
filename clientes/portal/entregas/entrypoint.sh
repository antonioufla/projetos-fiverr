#!/bin/sh
# Aponta /data para o volume do monorepo, garante a chave e sobe o gunicorn.
set -eu

DATA_DIR="${DATA_DIR:-/data}"

# deploy-projeto.sh monta ./dados em /srv/dados. O portal grava em /data.
# Se /data não for um volume próprio, usa esse mount.
if [ "$DATA_DIR" = "/data" ] && [ -d /srv/dados ]; then
  if [ -L /data ]; then
    :
  elif [ ! -e /data ]; then
    ln -sfn /srv/dados /data
  elif [ "$(stat -c '%d' /data)" = "$(stat -c '%d' /)" ] && [ -z "$(ls -A /data 2>/dev/null)" ]; then
    rmdir /data
    ln -sfn /srv/dados /data
  fi
fi

mkdir -p "$DATA_DIR/media"

if [ -z "${DJANGO_SECRET_KEY:-}" ] && [ ! -s "$DATA_DIR/secret_key" ]; then
  rm -f "$DATA_DIR/secret_key"
  DATA_DIR="$DATA_DIR" python - <<'PY'
import os
import secrets
from pathlib import Path

destino = Path(os.environ["DATA_DIR"]) / "secret_key"
fd = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
    arquivo.write(secrets.token_urlsafe(64) + "\n")
PY
fi

cd /srv
python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
