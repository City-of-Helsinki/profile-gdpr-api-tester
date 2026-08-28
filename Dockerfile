FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/City-of-Helsinki/profile-gdpr-api-tester
LABEL org.opencontainers.image.description="Helsinki Profile GDPR API Tester"
LABEL org.opencontainers.image.licenses=MIT

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends rlwrap; \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE /app/
COPY /gdpr_api_tester /app/gdpr_api_tester

RUN pip3 install --no-cache-dir --only-binary=:all: uv==0.12.6 \
  && uv sync --locked --no-default-groups --no-install-project --no-build

ENV PATH="/app/.venv/bin:$PATH"

COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Prepare entrypoint permissions and create non-root runtime user
RUN chmod +x /app/docker-entrypoint.sh \
  && useradd -m -u 1000 appuser \
  && chown -R appuser:appuser /app

USER appuser

EXPOSE 8888

CMD ["/app/docker-entrypoint.sh"]
