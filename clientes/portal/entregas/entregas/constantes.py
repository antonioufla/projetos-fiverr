import re

# Subdomínios que não podem virar cliente: o admin, o host do container e www.
SLUGS_RESERVADOS = frozenset({"arquivos", "www", "portal"})

SUFIXO_HOST = ".viralmedia.vip"

# Host do container (id/projeto no deploy). Não é área de cliente nem admin.
HOSTS_PLATAFORMA = frozenset({"portal.viralmedia.vip"})

# Rótulo DNS: sem underscore (o Nginx curinga só aceita [a-z0-9-]).
SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")

REFERENCIA_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
