"""Demonstracao do portfolio: serve paginas estaticas com o prefixo (ROOT_PATH) aplicado."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, Response
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
