import sys

from django.conf import settings
from django.core.checks import Warning, register

from config.segredo import CHAVE_DEV


@register()
def checar_chave(app_configs, **kwargs):
    if "test" in sys.argv:
        return []
    if settings.SECRET_KEY == CHAVE_DEV:
        return [
            Warning(
                "DJANGO_SECRET_KEY não está definido e não há secret_key em DATA_DIR. "
                "Defina a chave no .env.secrets antes de criar usuários.",
                id="entregas.W001",
            )
        ]
    return []
