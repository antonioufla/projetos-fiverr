"""Site Viral Media (substituto do WordPress). Paginas estaticas + pedidos de orcamento.

- POST   /api/pedido          recebe o formulario (honeypot + limite por IP), grava em SQLite
- GET    /api/pedidos         lista os pedidos (Authorization: Bearer <token>)
- DELETE /api/pedidos/{id}    apaga um pedido (mesmo token)

O token nao fica no Git: so o SHA-256 dele (PEDIDOS_TOKEN_SHA256). Para trocar, gere outro
token e coloque o novo hash em PEDIDOS_TOKEN_SHA256 no .env.secrets do servidor (tem prioridade).
Banco: $DADOS/pedidos.db (volume persistente /srv/dados).
"""
import hashlib
import hmac
import os
import re
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

AQUI = Path(__file__).parent
VERSAO = os.getenv("VERSAO", "dev")
DADOS = Path(os.getenv("DADOS", "/srv/dados"))
TOKEN_SHA256 = os.getenv("PEDIDOS_TOKEN_SHA256", "ba8409e14796355eb0aa10501b625f5b500785b4ebde16094d7c4774fc50862f").strip().lower()
TIPOS = {"chatbot", "app", "landing", "logo", "prompts", "python", "make", "outro"}

app = FastAPI(title="Viral Media", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")


# ---------- banco ----------
def _db() -> sqlite3.Connection:
    DADOS.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DADOS / "pedidos.db", timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, criado TEXT NOT NULL, nome TEXT, email TEXT, telefone TEXT,
        tipo TEXT, descricao TEXT, prazo TEXT, idioma TEXT, ip TEXT, agente TEXT)""")
    return con


# ---------- limite por IP: 5 envios a cada 10 min, 20 por dia ----------
_envios: dict[str, deque] = defaultdict(deque)


def _ip(req: Request) -> str:
    return (req.headers.get("cf-connecting-ip") or req.headers.get("x-real-ip")
            or req.headers.get("x-forwarded-for", "").split(",")[0].strip() or (req.client.host if req.client else "?"))


def _limitado(ip: str) -> bool:
    agora = time.time(); fila = _envios[ip]
    while fila and agora - fila[0] > 86400:
        fila.popleft()
    if sum(1 for t in fila if agora - t < 600) >= 5 or len(fila) >= 20:
        return True
    fila.append(agora)
    return False


class Pedido(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    telefone: str = Field(default="", max_length=40)
    tipo: str = Field(max_length=20)
    descricao: str = Field(min_length=10, max_length=4000)
    prazo: str = Field(default="", max_length=200)
    idioma: str = Field(default="pt", max_length=5)
    site: str = Field(default="", max_length=200)  # honeypot: humano deixa vazio


@app.post("/api/pedido")
def novo_pedido(p: Pedido, req: Request):
    if p.site.strip():  # robo: finge sucesso e descarta
        return {"ok": True}
    ip = _ip(req)
    if _limitado(ip):
        return JSONResponse({"ok": False, "erro": "limite"}, status_code=429)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", p.email.strip()):
        return JSONResponse({"ok": False, "erro": "email"}, status_code=422)
    tipo = p.tipo if p.tipo in TIPOS else "outro"
    with _db() as con:
        cur = con.execute(
            "INSERT INTO pedidos (criado,nome,email,telefone,tipo,descricao,prazo,idioma,ip,agente) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), p.nome.strip(), p.email.strip(), p.telefone.strip(),
             tipo, p.descricao.strip(), p.prazo.strip(), "en" if p.idioma == "en" else "pt", ip,
             req.headers.get("user-agent", "")[:200]))
    print(f"Novo pedido #{cur.lastrowid} ({tipo})", flush=True)
    return {"ok": True, "id": cur.lastrowid}


def _autorizar(authorization: str | None):
    if not TOKEN_SHA256:
        raise HTTPException(503, "token nao configurado")
    tok = (authorization or "").removeprefix("Bearer ").strip()
    if not tok or not hmac.compare_digest(hashlib.sha256(tok.encode()).hexdigest(), TOKEN_SHA256):
        time.sleep(0.5)
        raise HTTPException(401, "nao autorizado")


@app.get("/api/pedidos")
def listar(authorization: str | None = Header(default=None), desde: str = "", limite: int = 100):
    _autorizar(authorization)
    with _db() as con:
        linhas = con.execute("SELECT * FROM pedidos WHERE criado > ? ORDER BY id DESC LIMIT ?",
                             (desde, max(1, min(limite, 1000)))).fetchall()
    return {"total": len(linhas), "pedidos": [dict(r) for r in linhas]}


@app.delete("/api/pedidos/{pid}")
def apagar(pid: int, authorization: str | None = Header(default=None)):
    _autorizar(authorization)
    with _db() as con:
        n = con.execute("DELETE FROM pedidos WHERE id = ?", (pid,)).rowcount
    if not n:
        raise HTTPException(404, "nao encontrado")
    return {"ok": True, "apagado": pid}


# ---------- paginas e SEO ----------
def _base(req: Request) -> str:
    return f"https://{req.headers.get('host', 'viralmedia.vip')}"


@app.get("/saude")
def saude():
    return {"ok": True, "versao": VERSAO}


@app.get("/", response_class=HTMLResponse)
def inicio(req: Request):
    html = (AQUI / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{VERSAO}}", VERSAO).replace("{{URL}}", _base(req))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots(req: Request):
    return f"User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {_base(req)}/sitemap.xml\n"


@app.get("/sitemap.xml")
def sitemap(req: Request):
    hoje = datetime.now(timezone.utc).date().isoformat()
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f"<url><loc>{_base(req)}/</loc><lastmod>{hoje}</lastmod><priority>1.0</priority></url></urlset>\n")
    return Response(xml, media_type="application/xml")


@app.get("/favicon.ico")
def favicon():
    return Response((AQUI / "static" / "favicon.png").read_bytes(), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})
