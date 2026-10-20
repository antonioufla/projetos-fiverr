# projetos-fiverr

Monorepo privado com os projetos de clientes do Fiverr (@antoniorochanet).

## Estrutura

```
clientes/
  <id-cliente>/                 # uma pasta por cliente (usuário do Fiverr)
    PROJETO.md                  # pedidos, escopo, prazos, status
    deploy.env                  # SUBDOMINIO e PORTA
    docker-compose.yml          # ponto de entrada (uma porta em 127.0.0.1)
    <projeto>/                  # código de cada projeto do cliente
  _modelo/                      # copiar ao iniciar um cliente
infra/
  deploy/deploy-cliente.sh      # publica um cliente no servidor
  portas.md                     # portas locais em uso
```

## Convenções

- **Pasta:** `clientes/<id-cliente>`, em minúsculas, `_` vira `-`. Exemplo: `clientes/johnsmith`.
- **Entrega online:** `https://<id-cliente>.viralmedia.vip`; um segundo projeto do mesmo cliente vai em `/<projeto>`.
- **Deploy:** push na `main` publica só os clientes alterados (runner `servidor-133`, código em `/opt/projetos-fiver/<id-cliente>`, Nginx em `/etc/nginx/projetos-fiver/`). SSL pela Cloudflare (proxy ligado).
- **DNS:** registro A `<id-cliente>` → `177.70.13.133`, proxied, criado na Cloudflare.
- **Código para o cliente:** se o cliente pedir o código-fonte, a pasta dele é extraída para um repositório próprio.
- Nada de segredos (chaves de API, senhas) no repositório. Eles ficam só no servidor.
