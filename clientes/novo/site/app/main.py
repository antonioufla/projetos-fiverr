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
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

AQUI = Path(__file__).parent
VERSAO = os.getenv("VERSAO", "dev")
DADOS = Path(os.getenv("DADOS", "/srv/dados"))
TOKEN_SHA256 = os.getenv("PEDIDOS_TOKEN_SHA256", "ba8409e14796355eb0aa10501b625f5b500785b4ebde16094d7c4774fc50862f").strip().lower()
TIPOS = {"chatbot", "app", "landing", "logo", "prompts", "python", "make", "outro"}

CANONICO = os.getenv("CANONICO", "").strip().lower()  # ex.: viralmedia.vip (ativa o redirecionamento)
# Enderecos do WordPress antigo: mandam para a pagina inicial em vez de dar erro
ANTIGOS = {"/pv_felipe", "/pv01", "/terms", "/privacy-policy-2", "/sample-page", "/home", "/feed",
           "/comments/feed", "/wp-admin", "/wp-login.php", "/wp-json", "/xmlrpc.php"}

app = FastAPI(title="Viral Media", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")


@app.middleware("http")
async def canonico(request: Request, call_next):
    # com CANONICO definido, o subdominio de teste (novo.) redireciona para o dominio principal
    host = request.headers.get("host", "").split(":")[0].lower()
    if CANONICO and host.startswith("novo.") and request.url.path != "/saude" and request.method in ("GET", "HEAD"):
        destino = f"https://{CANONICO}{request.url.path}" + (f"?{request.url.query}" if request.url.query else "")
        return RedirectResponse(destino, status_code=301)
    return await call_next(request)


PAGINA_404 = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Página não encontrada · Viral Media</title><link rel="icon" href="/static/favicon.png">
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
background:linear-gradient(120deg,#0F2340 0%,#0F2E45 55%,#0E4249 100%);color:#fff;text-align:center;padding:24px}
.k{color:#2DD4BF;font-weight:700;letter-spacing:.14em;font-size:13px}h1{font-size:34px;margin:12px 0}p{color:#C3CFDC;margin:0 0 28px}
a{display:inline-block;background:#0F766E;color:#fff;text-decoration:none;font-weight:600;padding:13px 22px;border-radius:10px}a:hover{background:#115E59}</style></head>
<body><div><div class="k">ERRO 404</div><h1>Página não encontrada</h1><p>O endereço que você abriu não existe mais ou mudou de lugar.<br>Page not found.</p>
<a href="/">Ir para a página inicial</a></div></body></html>"""


@app.exception_handler(StarletteHTTPException)
async def erro_http(request: Request, exc: StarletteHTTPException):
    caminho = request.url.path.rstrip("/") or "/"
    if exc.status_code == 404 and not caminho.startswith("/api"):
        if caminho in ANTIGOS or caminho.startswith(("/wp-", "/category/", "/author/", "/tag/")):
            return RedirectResponse("/", status_code=301)
        return HTMLResponse(PAGINA_404, status_code=404)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


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


def _staging(req: Request) -> bool:
    # enquanto estiver so no subdominio de teste, nao deixa o Google indexar
    return req.headers.get("host", "").startswith("novo.")


@app.get("/saude")
def saude():
    return {"ok": True, "versao": VERSAO}


@app.get("/", response_class=HTMLResponse)
def inicio(req: Request):
    html = (AQUI / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{VERSAO}}", VERSAO).replace("{{URL}}", _base(req))
    cab = {"Cache-Control": "no-cache"}
    if _staging(req):
        html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)
        cab["X-Robots-Tag"] = "noindex"
    return HTMLResponse(html, headers=cab)


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots(req: Request):
    if _staging(req):
        return "User-agent: *\nDisallow: /\n"
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
