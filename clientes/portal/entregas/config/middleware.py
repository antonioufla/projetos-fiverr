"""Resolve o cliente pelo Host e impede admin e sessão cruzada."""

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import render

from entregas.constantes import HOSTS_PLATAFORMA, SLUG_RE, SLUGS_RESERVADOS, SUFIXO_HOST
from entregas.models import Cliente

# Acesso local ao processo (testes e docker exec). Não é roteado pelo Traefik.
_HOSTS_LOCAIS = frozenset({"localhost", "127.0.0.1", "testserver"})


def host_sem_porta(valor):
    """Tira a porta sem quebrar um IPv4 (127.0.0.1:8000)."""
    host = (valor or "").strip().lower().rstrip(".")
    if host.startswith("["):
        fim = host.find("]")
        return host[1:fim] if fim != -1 else host
    if host.count(":") == 1 and host.rsplit(":", 1)[1].isdigit():
        return host.rsplit(":", 1)[0]
    return host


def classificar_host(host):
    if host in _hosts_admin():
        return "admin", None
    if host in HOSTS_PLATAFORMA:
        return "plataforma", None
    if host.endswith(SUFIXO_HOST):
        slug = host[: -len(SUFIXO_HOST)]
        if slug in SLUGS_RESERVADOS or SLUG_RE.fullmatch(slug) is None:
            return "negado", None
        return "cliente", slug
    return "negado", None


def _hosts_admin():
    return {item.lower() for item in settings.ADMIN_HOSTS} | _HOSTS_LOCAIS


def _caminho_admin(caminho):
    return caminho == "/admin" or caminho.startswith("/admin/")


def _nao_encontrado(request):
    resposta = render(request, "404.html", status=404)
    resposta.headers["X-Frame-Options"] = "DENY"
    return resposta


class SubdominioClienteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # /saude não consulta o banco e não depende do tenant.
        if request.path.rstrip("/") == "/saude":
            request.modo = "saude"
            request.cliente = None
            return self.get_response(request)

        host = host_sem_porta(request.get_host())
        modo, slug = classificar_host(host)
        request.modo = modo
        request.cliente = None

        if modo == "negado":
            return _nao_encontrado(request)

        if modo == "cliente":
            cliente = (
                Cliente.objects.filter(slug=slug, ativo=True).select_related("user").first()
            )
            if cliente is None:
                return _nao_encontrado(request)
            request.cliente = cliente
            # Sessão apresentada no host de outro cliente deixa de valer.
            if request.user.is_authenticated and request.user.pk != cliente.user_id:
                logout(request)

        if _caminho_admin(request.path) and modo != "admin":
            return _nao_encontrado(request)

        return self.get_response(request)
