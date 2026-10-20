# demo / chatbot

- **Tipo:** demonstração do portfólio (não é cliente real)
- **URL:** https://demo.viralmedia.vip/
- **Status:** publicado

## Escopo
Site da "Clínica Sorriso" (fictícia) com widget de chat flutuante. O widget (`/chatbot/widget.js`) instala em qualquer site com uma linha de `<script>`.
Respostas por FAQ com busca tolerante a erros (`app/faq.py`). LLM opcional: colocar `OPENAI_API_KEY` (e opcionalmente `OPENAI_BASE_URL`, `OPENAI_MODEL`, `LLM_LIMITE_DIA`) no `.env.secrets` do servidor; só é usado quando o FAQ não acha resposta. Limite de 12 msgs/min e 120/dia por IP.
