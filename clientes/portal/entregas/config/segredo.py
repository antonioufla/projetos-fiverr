"""Leitura da chave do Django. Nunca grave um segredo real neste arquivo."""

from pathlib import Path

# Placeholder óbvio. O entrypoint grava uma chave em /data/secret_key quando
# DJANGO_SECRET_KEY não vem do ambiente. Os dois ficam fora do Git.
CHAVE_DEV = "django-insecure-dev-only-troque-DJANGO_SECRET_KEY-antes-de-criar-usuarios"


def ler_chave_secreta(data_dir, ambiente=None):
    if ambiente is None:
        import os

        ambiente = os.environ
    vinda_do_ambiente = str(ambiente.get("DJANGO_SECRET_KEY", "")).strip()
    if vinda_do_ambiente:
        return vinda_do_ambiente
    caminho = Path(data_dir) / "secret_key"
    try:
        if caminho.is_file():
            gravada = caminho.read_text(encoding="utf-8").strip()
            if gravada:
                return gravada
    except OSError:
        pass
    return CHAVE_DEV
