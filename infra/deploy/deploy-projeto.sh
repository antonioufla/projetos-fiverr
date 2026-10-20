#!/usr/bin/env bash
# Publica clientes/<id>/<projeto>: monta a imagem e sobe o container com labels do Traefik.
# Uso: deploy-projeto.sh <id-cliente> <projeto>
set -euo pipefail
ID="$1"; PROJ="$2"
[[ "$ID" =~ ^[a-z0-9-]+$ && "$PROJ" =~ ^[a-z0-9-]+$ ]] || { echo "Nome invalido: $ID/$PROJ (use a-z, 0-9, -)"; exit 1; }
SRC="$GITHUB_WORKSPACE/clientes/$ID/$PROJ"
DEST="/opt/projetos-fiver/$ID/$PROJ"
NOME="fiverr-$ID-$PROJ"

if [ ! -d "$SRC" ]; then
  echo "Projeto removido do repositorio: derrubando $NOME"
  [ -f "$DEST/.deploy-compose.yml" ] && docker compose -p "$NOME" -f "$DEST/.deploy-compose.yml" down --remove-orphans || true
  exit 0
fi
[ -f "$SRC/Dockerfile" ] || { echo "Sem Dockerfile em $ID/$PROJ, pulando"; exit 0; }

CAMINHO=/
[ -f "$SRC/projeto.env" ] && { set -a; . "$SRC/projeto.env"; set +a; }
CAMINHO="/${CAMINHO#/}"; CAMINHO="${CAMINHO%/}"; [ -z "$CAMINHO" ] && CAMINHO=/
HOST="$ID.viralmedia.vip"
VERSAO="${GITHUB_SHA:0:7}"

mkdir -p "$DEST"
find "$DEST" -mindepth 1 -maxdepth 1 ! -name 'dados' ! -name '.env.secrets' -exec rm -rf {} +
cp -a "$SRC/." "$DEST/"
mkdir -p "$DEST/dados"
touch "$DEST/.env.secrets"   # segredos do cliente ficam so no servidor, nunca no Git

R="r-$ID-$PROJ"
if [ "$CAMINHO" = "/" ]; then
  RULE="Host(\`$HOST\`)"; ROOT_PATH=""; MW=""
else
  RULE="Host(\`$HOST\`) && PathPrefix(\`$CAMINHO\`)"; ROOT_PATH="$CAMINHO"
  MW="      - traefik.http.middlewares.$R-strip.stripprefix.prefixes=$CAMINHO
      - traefik.http.routers.$R.middlewares=$R-strip"
fi

cat > "$DEST/.deploy-compose.yml" <<YML
services:
  app:
    build: .
    image: $NOME:$VERSAO
    container_name: $NOME
    restart: unless-stopped
    env_file:
      - path: .env.secrets
        required: false
    environment:
      VERSAO: "$VERSAO"
      ROOT_PATH: "$ROOT_PATH"
      CLIENTE: "$ID"
    volumes:
      - ./dados:/srv/dados
    networks: [fiverr]
    labels:
      - traefik.enable=true
      - traefik.http.routers.$R.rule=$RULE
      - traefik.http.routers.$R.entrypoints=web
      - traefik.http.services.$R.loadbalancer.server.port=8000
$MW
networks:
  fiverr:
    external: true
YML
sed -i '/^$/d' "$DEST/.deploy-compose.yml"

cd "$DEST"
docker compose -p "$NOME" -f .deploy-compose.yml up -d --build --remove-orphans
docker image prune -f >/dev/null 2>&1 || true

# Espera o app responder via Nginx -> Traefik
ALVO="https://$HOST${CAMINHO%/}/saude"
C=000
for i in $(seq 1 20); do
  C=$(curl -sk -o /dev/null -w '%{http_code}' --resolve "$HOST:443:127.0.0.1" "$ALVO" || true)
  [ "$C" = "200" ] && break; sleep 2
done
echo "Saude ($ALVO): HTTP $C"
[ "$C" = "200" ] || { docker logs --tail 50 "$NOME"; exit 1; }
echo "Publicado: https://$HOST$([ "$CAMINHO" = "/" ] || echo "$CAMINHO")"
