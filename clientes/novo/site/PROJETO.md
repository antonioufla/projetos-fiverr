# novo / site

- **Tipo:** site próprio Viral Media (substituto do WordPress de viralmedia.vip)
- **URL (staging):** https://novo.viralmedia.vip/
- **Status:** staging, aguardando aprovação para trocar o domínio principal

## Escopo
Página única PT/EN: hero, conteúdo sobre IA para pequenos negócios, serviços, como funciona, demos, sobre, contato (WhatsApp + formulário).
Pedidos do formulário: SQLite em /srv/dados/pedidos.db (volume persistente).
Leitura: `GET /api/pedidos` com `Authorization: Bearer <token>`. O Git guarda só o SHA-256 do token; para trocar, defina
`PEDIDOS_TOKEN_SHA256` no `.env.secrets` do servidor.
