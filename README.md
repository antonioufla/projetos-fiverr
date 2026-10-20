# projetos-fiverr

Monorepo privado com os projetos de clientes do Fiverr (@antoniorochanet). Tudo em Python + uvicorn (FastAPI).

## Estrutura

```
clientes/
  <id-cliente>/                # usuario do Fiverr (minusculo, '_' vira '-')
    <projeto>/                 # um projeto = um container
      PROJETO.md               # pedido, escopo, prazo, status
      projeto.env              # CAMINHO=/ (ou /nome para projetos extras)
      Dockerfile               # padrao: uvicorn app.main:app na porta 8000
      requirements.txt
      app/main.py              # precisa ter GET /saude retornando 200
  _modelo/                     # copiar para iniciar um projeto
infra/                         # Traefik, Nginx curinga e scripts de deploy
```

## Novo projeto (passo a passo)

1. Copiar `clientes/_modelo` para `clientes/<id-cliente>/<projeto>` e preencher `PROJETO.md`.
2. Criar o registro DNS `A <id-cliente> -> 177.70.13.133` (proxied) na Cloudflare, se o cliente for novo.
3. Desenvolver em `app/` e fazer push na `main`.
4. A Action publica so os projetos alterados em `https://<id-cliente>.viralmedia.vip<CAMINHO>` e confere `/saude`.

Sem portas para gerenciar e sem editar o Nginx. Segredos (chaves de API do cliente) ficam so no servidor, em `.env.secrets`.
Se o cliente pedir o codigo-fonte, a pasta do projeto e extraida para um repositorio proprio.
