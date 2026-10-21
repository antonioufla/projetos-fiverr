# novo / site

- **Tipo:** site próprio Viral Media (substituto do WordPress de viralmedia.vip)
- **URL:** https://viralmedia.vip/ (pt-BR) e https://viralmedia.vip/en/ (en)
- **Status:** no ar no domínio principal

## Escopo
Página única PT/EN: hero, conteúdo sobre IA para pequenos negócios, serviços, como funciona, demos, sobre, contato (WhatsApp + formulário).
Pedidos do formulário: SQLite em /srv/dados/pedidos.db (volume persistente).
Leitura: `GET /api/pedidos` com `Authorization: Bearer <token>`. O Git guarda só o SHA-256 do token; para trocar, defina
`PEDIDOS_TOKEN_SHA256` no `.env.secrets` do servidor.

## SEO
- `/` (pt-BR) e `/en/` (inglês) renderizados no servidor (o inglês vem dos atributos `data-en` do index.html), com canonical próprio e hreflang.
- JSON-LD (Organization/ProfessionalService, Person, WebSite, WebPage, FAQPage) gerado em `main.py` (`SERVICOS`, `FAQ`).
- `robots.txt` (libera buscadores e robôs de IA, bloqueia `/api/`), `sitemap.xml`, `llms.txt`, `llms-full.txt`, `site.webmanifest`.
- IndexNow: chave em `INDEXNOW_KEY`, arquivo `/<chave>.txt`.
