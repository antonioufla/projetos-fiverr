# Infra (servidor 177.70.13.133)

```
Cloudflare (SSL) -> Nginx :443/:80 -> bloco curinga *.viralmedia.vip -> Traefik 127.0.0.1:8100
                                                                         -> container fiverr-<id>-<projeto> :8000 (uvicorn)
```

- **Nginx:** sites existentes (server_name exato) nao sao afetados. O bloco `infra/nginx/00-fiverr-curinga.conf` fica em `/etc/nginx/projetos-fiver/`.
- **Traefik:** `infra/traefik/docker-compose.yml`, rede Docker `fiverr`. Roteia por Host e caminho usando labels.
- **Projetos:** `/opt/projetos-fiver/<id>/<projeto>`. Sem portas no host.
- **Segredos do cliente:** `/opt/projetos-fiver/<id>/<projeto>/.env.secrets` (so no servidor).
- **Dados persistentes:** `/opt/projetos-fiver/<id>/<projeto>/dados` -> `/srv/dados` no container.
- **Scripts:** `deploy/setup-infra.sh` (idempotente, roda em todo deploy) e `deploy/deploy-projeto.sh <id> <projeto>`.
