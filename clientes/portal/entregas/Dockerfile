FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/srv

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /srv/entrypoint.sh \
    && python manage.py collectstatic --noinput

EXPOSE 8000

# Host explicito: sem ele o Django responde 400 se ALLOWED_HOSTS for so
# .viralmedia.vip, o container fica unhealthy e o Traefik tira o portal do ar.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; req = urllib.request.Request('http://127.0.0.1:8000/saude', headers={'Host': 'portal.viralmedia.vip'}); urllib.request.urlopen(req, timeout=3).read()"]

CMD ["/srv/entrypoint.sh"]
