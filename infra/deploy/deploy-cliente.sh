#!/usr/bin/env bash
# Publica um cliente: copia para /opt/projetos-fiver/<id>, sobe os containers e cria o site no Nginx.
set -euo pipefail
ID="$1"
SRC="$GITHUB_WORKSPACE/clientes/$ID"
DEST="/opt/projetos-fiver/$ID"
NGINX_DIR="/etc/nginx/projetos-fiver"

[ -f "$SRC/deploy.env" ] || { echo "Sem deploy.env em $ID, pulando"; exit 0; }
set -a; . "$SRC/deploy.env"; set +a
: "${SUBDOMINIO:?SUBDOMINIO vazio}"; : "${PORTA:?PORTA vazia}"
[[ "$SUBDOMINIO" =~ ^[a-z0-9-]+$ ]] || { echo "SUBDOMINIO invalido"; exit 1; }
[[ "$PORTA" =~ ^81[0-9][0-9]$ ]] || { echo "PORTA fora da faixa 8100-8199"; exit 1; }

mkdir -p "$DEST"
find "$DEST" -mindepth 1 -maxdepth 1 ! -name 'dados' -exec rm -rf {} +
cp -a "$SRC/." "$DEST/"
cp "$DEST/deploy.env" "$DEST/.env"
sed -i "s/__VERSAO__/${GITHUB_SHA:0:7} ($(date -u +%Y-%m-%dT%H:%MZ))/g" $(grep -rl "__VERSAO__" "$DEST" 2>/dev/null) 2>/dev/null || true

cd "$DEST"
docker compose -p "fiverr-$ID" up -d --build --remove-orphans

cat > "$NGINX_DIR/$SUBDOMINIO.viralmedia.vip.conf" <<NGX
server {
    listen 80;
    server_name $SUBDOMINIO.viralmedia.vip;
    client_max_body_size 50m;
    location / {
        proxy_pass http://127.0.0.1:$PORTA;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGX
sudo /usr/sbin/nginx -t
sudo /usr/bin/systemctl reload nginx
sleep 3
curl -fsS -o /dev/null -w "Local: HTTP %{http_code}\n" -H "Host: $SUBDOMINIO.viralmedia.vip" http://127.0.0.1/
echo "Publicado: https://$SUBDOMINIO.viralmedia.vip"
