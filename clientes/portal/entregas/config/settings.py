import os
from pathlib import Path

from config.segredo import ler_chave_secreta

BASE_DIR = Path(__file__).resolve().parent.parent

_data = Path(os.environ.get("DATA_DIR", "/data")).expanduser()
DATA_DIR = _data if _data.is_absolute() else BASE_DIR / _data

SECRET_KEY = ler_chave_secreta(DATA_DIR)
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"


def _lista(nome, padrao):
    bruto = os.environ.get(nome, padrao)
    itens = []
    for item in bruto.split(","):
        item = item.strip()
        # Django usa ".dominio" para o domínio e os subdomínios. O desenho
        # cita "*.dominio"; os dois formatos valem aqui.
        if item.startswith("*."):
            item = item[1:]
        if item:
            itens.append(item)
    return itens


ALLOWED_HOSTS = _lista(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,testserver,.viralmedia.vip",
)

# Hosts em que /admin/ responde. O padrão é o subdomínio da equipe.
ADMIN_HOSTS = _lista("ADMIN_HOSTS", "arquivos.viralmedia.vip")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "entregas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Por último, para a resposta 404 ainda receber os cabeçalhos acima.
    "config.middleware.SubdominioClienteMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATA_DIR / "db.sqlite3"),
        "OPTIONS": {
            "timeout": 20,
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

MEDIA_URL = "media/"
MEDIA_ROOT = DATA_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "entrar"
LOGOUT_REDIRECT_URL = "entrar"

# Cookie só no host que o definiu. Sem domínio pai, a sessão de um cliente
# não segue para o subdomínio de outro.
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None
SESSION_COOKIE_NAME = "entregas_sessao"
CSRF_COOKIE_NAME = "entregas_csrf"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

_cookies_seguros = os.environ.get("DJANGO_SECURE_COOKIES")
if _cookies_seguros is None:
    _cookies_seguros = "0" if DEBUG else "1"
SESSION_COOKIE_SECURE = _cookies_seguros == "1"
CSRF_COOKIE_SECURE = _cookies_seguros == "1"

CSRF_TRUSTED_ORIGINS = _lista("CSRF_TRUSTED_ORIGINS", "https://*.viralmedia.vip")
if DEBUG:
    for _origem in ("http://localhost", "http://127.0.0.1"):
        if _origem not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(_origem)

# O Nginx envia X-Forwarded-Proto. Sem isto o Django vê http e recusa o POST.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# O tenant vem do Host, que o Nginx define. Não honrar X-Forwarded-Host.
USE_X_FORWARDED_HOST = False

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

CSRF_FAILURE_VIEW = "entregas.views.csrf_falhou"

_raiz = os.environ.get("ROOT_PATH", "").strip().rstrip("/")
if _raiz:
    FORCE_SCRIPT_NAME = _raiz
