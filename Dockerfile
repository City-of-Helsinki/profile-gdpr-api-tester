FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/City-of-Helsinki/profile-gdpr-api-tester
LABEL org.opencontainers.image.description="Helsinki Profile GDPR API Tester"
LABEL org.opencontainers.image.licenses=MIT

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends rlwrap

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY /gdpr_api_tester /app/gdpr_api_tester
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8888

CMD ["/app/docker-entrypoint.sh"]
