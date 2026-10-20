#!/usr/bin/env bash
# Idempotente: garante rede Docker, certificado de origem, bloco curinga do Nginx e Traefik.
set -euo pipefail
REPO="$GITHUB_WORKSPACE"
NGINX_DIR="/etc/nginx/projetos-fiver"
SSL_DIR="$NGINX_DIR/ssl"

docker network inspect fiverr >/dev/null 2>&1 || docker network create fiverr

mkdir -p "$SSL_DIR"
if [ ! -f "$SSL_DIR/origem.crt" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
    -keyout "$SSL_DIR/origem.key" -out "$SSL_DIR/origem.crt" \
    -subj "/CN=*.viralmedia.vip" -addext "subjectAltName=DNS:*.viralmedia.vip,DNS:viralmedia.vip"
  chmod 600 "$SSL_DIR/origem.key"
fi

# Traefik primeiro (o Nginx vai apontar para ele)
docker compose -p fiverr-traefik -f "$REPO/infra/traefik/docker-compose.yml" up -d

# Nginx: instala o bloco curinga e remove blocos antigos por cliente
BACKUP=$(mktemp -d)
cp -a "$NGINX_DIR"/*.conf "$BACKUP"/ 2>/dev/null || true
rm -f "$NGINX_DIR"/*.viralmedia.vip.conf
# Exclui da regex todo subdominio que ja tem site proprio no Nginx (sites antigos)
EXISTENTES=$(grep -hoE 'server_name[^;]*' /etc/nginx/sites-enabled/* /etc/nginx/conf.d/* 2>/dev/null \
  | sed 's/server_name//' | tr ' ' '\n' | grep -E '^[a-z0-9-]+\.viralmedia\.vip$' \
  | sed 's/\.viralmedia\.vip$//' | sort -u | paste -sd'|' || true)
echo "Subdominios existentes preservados: $EXISTENTES"
if [ -z "$EXISTENTES" ]; then
  echo "Nao consegui ler os sites existentes; mantendo configuracao anterior"
  cp -a "$BACKUP"/*.conf "$NGINX_DIR"/ 2>/dev/null || true
  exit 1
fi
REGEX="~^(?!(?:$EXISTENTES)\\.)(?<cliente>[a-z0-9-]+)\\.viralmedia\\.vip\$"
MODELO=$(cat "$REPO/infra/nginx/00-fiverr-curinga.conf")
printf '%s\n' "${MODELO//__REGEX__/$REGEX}" > "$NGINX_DIR/00-fiverr-curinga.conf"
grep server_name "$NGINX_DIR/00-fiverr-curinga.conf"
if sudo /usr/sbin/nginx -t; then
  sudo /usr/bin/systemctl reload nginx
else
  echo "nginx -t falhou: restaurando configuracao anterior"
  rm -f "$NGINX_DIR"/*.conf
  cp -a "$BACKUP"/*.conf "$NGINX_DIR"/ 2>/dev/null || true
  exit 1
fi


# Diagnostico (somente leitura): quem atende o dominio principal e o www neste Nginx
echo "== Diagnostico dominio principal"
grep -rnE 'default_server|server_name[^;]*([[:space:]])(www\.)?viralmedia\.vip([[:space:];]|$)|server_name[[:space:]]+_' /etc/nginx 2>/dev/null | grep -v '/projetos-fiver/' | head -30 || true
grep -rnE '^[[:space:]]*include' /etc/nginx/nginx.conf 2>/dev/null || true
for f in $(grep -rlE 'default_server' /etc/nginx/sites-enabled /etc/nginx/conf.d 2>/dev/null); do
  echo "-- default: $f"; grep -nE 'server_name|listen|proxy_pass|root |return ' "$f" | head -30
done
echo "== fim diagnostico"

# Remove containers do formato antigo (porta por cliente)
docker compose -p fiverr-teste down --remove-orphans 2>/dev/null || true

# Conferencia: sites existentes continuam respondendo localmente
for s in cafe.viralmedia.vip app.viralmedia.vip; do
  echo "$s: HTTP $(curl -s -o /dev/null -w '%{http_code}' -H "Host: $s" http://127.0.0.1/)"
done
