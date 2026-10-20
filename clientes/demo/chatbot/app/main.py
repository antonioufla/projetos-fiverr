"""Demo: chatbot de atendimento com IA para sites (Clinica Sorriso, empresa ficticia).

- GET  /            pagina de exemplo da clinica com o widget instalado
- GET  /widget.js   o widget (instalacao com uma linha de <script>)
- POST /api/chat    responde a pergunta (FAQ por similaridade; LLM opcional no servidor)

LLM opcional: se OPENAI_API_KEY existir no .env.secrets do servidor, a resposta vem do
modelo (OPENAI_MODEL, OPENAI_BASE_URL) usando a base da clinica como contexto. A chave
nunca vai para o navegador. Sem chave, ou se o LLM falhar, responde pelo FAQ.
"""
import os
import time
from collections import defaultdict, deque
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .faq import contexto_llm, responder

AQUI = Path(__file__).parent
VERSAO = os.getenv("VERSAO", "dev")
BASE = os.getenv("ROOT_PATH", "").rstrip("/")
LLM_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODELO = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_LIMITE_DIA = int(os.getenv("LLM_LIMITE_DIA", "300"))

app = FastAPI(title="Demo Chatbot", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST", "GET"], allow_headers=["Content-Type"])
app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")

# Limite por IP: 12 mensagens por minuto e 120 por dia (memoria do processo).
_por_ip: dict[str, deque] = defaultdict(deque)
_llm_uso = {"dia": "", "n": 0}


def _ip(req: Request) -> str:
    return (req.headers.get("cf-connecting-ip") or req.headers.get("x-real-ip")
            or (req.headers.get("x-forwarded-for", "").split(",")[0].strip()) or (req.client.host if req.client else "?"))


def _limitado(ip: str) -> bool:
    agora = time.time()
    fila = _por_ip[ip]
    while fila and agora - fila[0] > 86400:
        fila.popleft()
    ultimo_minuto = sum(1 for t in fila if agora - t < 60)
    if ultimo_minuto >= 12 or len(fila) >= 120:
        return True
    fila.append(agora)
    if len(_por_ip) > 5000:  # evita crescer sem fim
        for k in list(_por_ip)[:1000]:
            _por_ip.pop(k, None)
    return False


def _pode_llm() -> bool:
    if not LLM_KEY:
        return False
    hoje = time.strftime("%Y-%m-%d")
    if _llm_uso["dia"] != hoje:
        _llm_uso.update(dia=hoje, n=0)
    return _llm_uso["n"] < LLM_LIMITE_DIA


async def _perguntar_llm(msg: str, idioma: str, historico: list[dict]) -> str | None:
    _llm_uso["n"] += 1
    sistema = (
        "Voce e a assistente virtual da Clinica Sorriso. Responda curto (ate 3 frases), simpatico, "
        f"no idioma {'ingles' if idioma == 'en' else 'portugues do Brasil'}. Use SOMENTE as informacoes abaixo; "
        "se nao souber, diga que nao tem a informacao e indique o telefone (11) 4000-1234. "
        "Nao de diagnosticos medicos.\n\n" + contexto_llm()
    )
    mensagens = [{"role": "system", "content": sistema}]
    for h in historico[-6:]:
        if h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str):
            mensagens.append({"role": h["role"], "content": h["content"][:500]})
    mensagens.append({"role": "user", "content": msg})
    try:
        async with httpx.AsyncClient(timeout=15) as cli:
            r = await cli.post(f"{LLM_URL}/chat/completions", headers={"Authorization": f"Bearer {LLM_KEY}"},
                               json={"model": LLM_MODELO, "messages": mensagens, "max_tokens": 250, "temperature": 0.3})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:  # nunca expoe detalhes nem a chave
        print(f"LLM falhou: {type(e).__name__}", flush=True)
        return None


class Pergunta(BaseModel):
    mensagem: str = Field(min_length=1, max_length=500)
    idioma: str = "pt"
    historico: list[dict] = Field(default_factory=list, max_length=12)


@app.post("/api/chat")
async def chat(p: Pergunta, req: Request):
    idioma = "en" if p.idioma == "en" else "pt"
    if _limitado(_ip(req)):
        txt = ("You're sending messages too fast. Please wait a minute. 🙂" if idioma == "en"
               else "Você enviou muitas mensagens seguidas. Aguarde um minuto, por favor. 🙂")
        return JSONResponse({"resposta": txt, "fonte": "limite", "sugestoes": []}, status_code=429)
    faq = responder(p.mensagem, idioma)
    if faq["intencao"] is None and _pode_llm():
        llm = await _perguntar_llm(p.mensagem, idioma, p.historico)
        if llm:
            return {"resposta": llm, "fonte": "llm", "sugestoes": []}
    return {"resposta": faq["resposta"], "fonte": "faq", "intencao": faq["intencao"], "sugestoes": faq["sugestoes"]}


@app.get("/saude")
def saude():
    return {"ok": True, "versao": VERSAO, "llm": bool(LLM_KEY)}


@app.get("/widget.js")
def widget():
    return Response((AQUI / "widget.js").read_text(encoding="utf-8"), media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=300", "Access-Control-Allow-Origin": "*"})


@app.get("/", response_class=HTMLResponse)
def inicio():
    html = (AQUI / "index.html").read_text(encoding="utf-8").replace("{{BASE}}", BASE).replace("{{VERSAO}}", VERSAO)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})
