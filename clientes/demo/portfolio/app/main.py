"""Demonstracao do portfolio: serve paginas estaticas com o prefixo (ROOT_PATH) aplicado."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

AQUI = Path(__file__).parent
VERSAO = os.getenv("VERSAO", "dev")
BASE = os.getenv("ROOT_PATH", "").rstrip("/")

app = FastAPI(title="Demo", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")


def _render(nome: str) -> str:
    html = (AQUI / nome).read_text(encoding="utf-8")
    return html.replace("{{BASE}}", BASE).replace("{{VERSAO}}", VERSAO)


@app.get("/saude")
def saude():
    return {"ok": True, "versao": VERSAO}


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio():
    return HTMLResponse(_render("index.html"), headers={"Cache-Control": "no-cache"})


D = "https://demo.viralmedia.vip"


@app.api_route("/robots.txt", methods=["GET", "HEAD"], response_class=PlainTextResponse)
def robots():
    return f"User-agent: *\nAllow: /\nDisallow: /chatbot/api/\n\nSitemap: {D}/sitemap.xml\n"


@app.api_route("/sitemap.xml", methods=["GET", "HEAD"])
def sitemap():
    urls = "".join(f"<url><loc>{D}{p}</loc></url>" for p in ("/", "/chatbot/", "/app/", "/landing/"))
    return Response('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    + urls + "</urlset>\n", media_type="application/xml")
