# portal / entregas

- **Tipo:** portal interno de entregas (não é um pedido Fiverr avulso)
- **URL da equipe:** https://arquivos.viralmedia.vip/admin/
- **URL do cliente:** https://<slug>.viralmedia.vip/
- **Container:** https://portal.viralmedia.vip/ (`GET /saude`)
- **Primeiro cliente:** Bob Rubin / Rwa Advisors — slug `bbrubin123`
- **Pedido:** `FO6315C2D0C48` — Daily follow-up report (Jump + email + Teams)
- **Status do pedido:** em_andamento
- **Status do projeto:** em desenvolvimento

## Escopo combinado

O cliente recebe usuário e senha fora do Git, entra em `https://<slug>.viralmedia.vip`, vê só os pedidos dele e baixa os arquivos. Antonio gerencia clientes, pedidos e uploads no admin do Django.

Modelos:

- `Cliente` — user (OneToOne), slug, nome_exibicao, ativo, criado_em
- `Pedido` — cliente, referencia, titulo, status, prazo, notas_internas, criado_em, atualizado_em
- `ArquivoDeEntrega` — pedido, arquivo, rotulo, enviado_em

Status: proposto, em_andamento, em_revisao, entregue, pago, cancelado.

`notas_internas` fica só no admin.

## Hosts

O Nginx curinga já manda `*.viralmedia.vip` para o Traefik. O Traefik só entrega neste container o host do deploy (`portal.viralmedia.vip`) e os nomes em `HOSTS` no `projeto.env`.

| Host | O que responde |
|---|---|
| `portal.viralmedia.vip` | Página simples e `/saude`. Sem `/admin/`. |
| `arquivos.viralmedia.vip` | Landing e `/admin/`. |
| `<slug>.viralmedia.vip` | Login e entregas daquele cliente. `/admin/` responde 404. |

Um curinga no Traefik também pegaria demo, novo e teste. Cada slug entra em `HOSTS` e ganha um DNS A, como os outros clientes. Cliente novo: DNS A + host em `HOSTS` + registro no admin. O slug não pode ser `arquivos`, `portal` ou `www`, nem repetir um subdomínio que já tem projeto.

A sessão não usa cookie no domínio pai. No host do cliente a conta tem de ser a daquele slug. Credencial de outro cliente não entra. Se a sessão for apresentada noutro subdomínio, ela é encerrada. O download passa por uma view que confere o dono e devolve `FileResponse`. `/media/` não é público. O arquivo fica em `media/entregas/<slug>/<referencia>/`.

Para abrir o admin por um IP interno, acrescente o IP em `ADMIN_HOSTS` no `.env.secrets`. O padrão é `arquivos.viralmedia.vip`. `localhost` só vale para quem alcança o processo por dentro da máquina.

## Dados e segredos

SQLite em `/data/db.sqlite3`. Uploads em `/data/media`. O deploy monta `./dados` em `/srv/dados`. Na subida, se `/data` não for um volume próprio, o entrypoint aponta `/data` para `/srv/dados`. No servidor isso é `/opt/projetos-fiver/portal/entregas/dados/`.

Segredos só em `/opt/projetos-fiver/portal/entregas/.env.secrets` (o deploy cria o arquivo vazio; não entra no Git):

```
DJANGO_SECRET_KEY=<saida de: python -c "import secrets; print(secrets.token_urlsafe(64))">
ALLOWED_HOSTS=.viralmedia.vip
DJANGO_SECURE_COOKIES=1
```

Django trata `.viralmedia.vip` (ponto na frente) como o domínio e os subdomínios. Se `DJANGO_SECRET_KEY` faltar, o primeiro boot grava `/data/secret_key` (modo 600) e reutiliza. A variável de ambiente ganha das duas. Defina a chave antes de criar usuários: trocar a chave encerra as sessões. Não há senha de cliente no repositório.

## Primeiro cliente

- slug: `bbrubin123`
- nome de exibição inicial: Bob Rubin (Rwa Advisors — pode ajustar no admin)
- pedido: `FO6315C2D0C48`
- título: Daily follow-up report (Jump + email + Teams)
- status: em_andamento

Pelo admin, em https://arquivos.viralmedia.vip/admin/ : criar o usuário (sem permissão de equipe), o `Cliente` e o `Pedido`. Ou, no container `fiverr-portal-entregas`, com a senha só no ambiente da sessão:

```
read -rs BBRUBIN_SENHA && export BBRUBIN_SENHA
docker exec -e BBRUBIN_SENHA fiverr-portal-entregas python manage.py preparar_primeiro_cliente
unset BBRUBIN_SENHA
```

O comando é idempotente: se o pedido já existe, não muda status nem senha, e não escreve a senha no log.

Usuário e senha do Bob saem por Fiverr ou e-mail, fora do Git, e só com aprovação do Antonio.

## Subida

Imagem na porta 8000, gunicorn. `GET /saude` responde 200 com `{"ok": true, "versao": "..."}`. O entrypoint roda `migrate` antes do gunicorn. `createsuperuser` continua manual:

```
docker exec -it fiverr-portal-entregas python manage.py createsuperuser
docker exec fiverr-portal-entregas python manage.py migrate
```

## faltando para implantar no servidor 133

- [ ] DNS A `arquivos` → 177.70.13.133 (proxied)
- [ ] DNS A `bbrubin123` → 177.70.13.133 (proxied)
- [ ] Segredos em `/opt/projetos-fiver/portal/entregas/.env.secrets`: `DJANGO_SECRET_KEY` e `ALLOWED_HOSTS=.viralmedia.vip` (sem senha de cliente no Git)
- [ ] Volume persistente: pasta `dados` do deploy ligada a `/data` (`db.sqlite3` e `media`)
- [ ] `migrate` (o entrypoint roda; conferir com `docker exec fiverr-portal-entregas python manage.py migrate`)
- [ ] `createsuperuser` no container `fiverr-portal-entregas`
- [ ] Criar o cliente `bbrubin123` e o pedido `FO6315C2D0C48` (admin ou `preparar_primeiro_cliente`)
- [ ] Enviar usuário e senha ao Bob somente com aprovação do Antonio
